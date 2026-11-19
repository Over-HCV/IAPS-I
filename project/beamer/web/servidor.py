"""Servidor de la presentación: deck, control desde el celular y simulador público.

Solo biblioteca estándar. Sirve ``project/beamer/`` (el deck está en ``/web/`` y lee
las figuras de ``/figuras/``) y agrega una API mínima:

- ``GET  /api/eventos``      SSE para el deck: Recibe ``{"ir": "next" | "prev" | n}``.
- ``POST /api/ir``           Lo manda el celular; exige el token (``?k=`` o ``X-Token``).
- ``POST /api/estado``       El deck reporta su diapositiva (solo desde esta máquina).
- ``GET  /api/estado/sse``   El celular sigue la diapositiva actual (con token).
- ``GET  /api/config``       URL pública del simulador para todos; la del control
                             solo a esta máquina, nunca por el túnel.

Uso, desde ``project/beamer``::

    python web/servidor.py              # http://localhost:8420 y la IP de la red local
    python web/servidor.py --tunel      # además, una URL https pública (cloudflared)

Con ``--tunel`` el celular y el público no dependen de que la Wi-Fi deje hablar a los
dispositivos entre sí. En el deck, la tecla Q muestra el QR del control.
"""

from __future__ import annotations

import argparse
import json
import queue
import re
import secrets
import shutil
import socket
import subprocess
import sys
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent  # project/beamer: así /figuras/ y /tema/ quedan al alcance del deck
LATIDO = 15.0  # s entre comentarios SSE, para que ningún proxy cierre la conexión


class Estado:
    """Lo compartido entre hilos: Suscriptores SSE, última diapositiva, URLs."""

    def __init__(self, token: str) -> None:
        self.token = token
        self.lock = threading.Lock()
        self.decks: list[queue.Queue[str]] = []
        self.controles: list[queue.Queue[str]] = []
        self.diapositiva: dict = {}
        self.publica: str | None = None
        self.locales: list[str] = []

    def suscribir(self, lista: list[queue.Queue[str]]) -> queue.Queue[str]:
        q: queue.Queue[str] = queue.Queue(maxsize=64)
        with self.lock:
            lista.append(q)
        return q

    def desuscribir(self, lista: list[queue.Queue[str]], q: queue.Queue[str]) -> None:
        with self.lock:
            if q in lista:
                lista.remove(q)

    def difundir(self, lista: list[queue.Queue[str]], dato: dict) -> int:
        msg = json.dumps(dato, ensure_ascii=False)
        with self.lock:
            destinos = list(lista)
        for q in destinos:
            try:
                q.put_nowait(msg)
            except queue.Full:
                pass
        return len(destinos)


def manejador(estado: Estado) -> type[SimpleHTTPRequestHandler]:
    class Manejador(SimpleHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def __init__(self, *a, **kw) -> None:
            super().__init__(*a, directory=str(RAIZ), **kw)

        # ------------------------------------------------------------ utilidades
        def log_message(self, fmt: str, *args) -> None:  # silencioso salvo la API
            if self.path.startswith("/api/ir"):
                sys.stderr.write(f"  {self.address_string()} {fmt % args}\n")

        def end_headers(self) -> None:
            # el deck se edita entre ensayos: sin caché para HTML, JS y datos
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def es_local(self) -> bool:
            """Esta máquina y no a través del túnel (cloudflared llega desde 127.0.0.1)."""
            if any(h in self.headers for h in ("Cf-Connecting-Ip", "Cf-Ray", "X-Forwarded-For")):
                return False
            return self.client_address[0] in ("127.0.0.1", "::1")

        def token_ok(self) -> bool:
            q = parse_qs(urlsplit(self.path).query)
            dado = self.headers.get("X-Token") or (q.get("k") or [""])[0]
            return secrets.compare_digest(dado, estado.token)

        def json(self, codigo: int, obj: dict) -> None:
            cuerpo = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def leer_json(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            if not 0 < n <= 4096:
                return {}
            try:
                return json.loads(self.rfile.read(n))
            except (ValueError, UnicodeDecodeError):
                return {}

        def sse(self, lista: list[queue.Queue[str]], inicial: dict | None = None) -> None:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            self.close_connection = True
            q = estado.suscribir(lista)
            try:
                self.wfile.write(b"retry: 1500\n\n")
                if inicial:
                    self.wfile.write(f"data: {json.dumps(inicial, ensure_ascii=False)}\n\n".encode())
                self.wfile.flush()
                while True:
                    try:
                        msg = q.get(timeout=LATIDO)
                        self.wfile.write(f"data: {msg}\n\n".encode())
                    except queue.Empty:
                        self.wfile.write(b": latido\n\n")
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            finally:
                estado.desuscribir(lista, q)

        # ---------------------------------------------------------------- rutas
        def do_GET(self) -> None:
            ruta = urlsplit(self.path).path
            if ruta in ("/", "/web"):
                self.send_response(HTTPStatus.FOUND)
                self.send_header("Location", "/web/simulador.html" if not self.es_local() else "/web/")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if ruta == "/api/eventos":
                return self.sse(estado.decks)
            if ruta == "/api/estado/sse":
                if not self.token_ok():
                    return self.json(403, {"error": "token"})
                return self.sse(estado.controles, estado.diapositiva or None)
            if ruta == "/api/estado":
                if not self.token_ok():
                    return self.json(403, {"error": "token"})
                return self.json(200, estado.diapositiva)
            if ruta == "/api/config":
                base_pub = estado.publica or (estado.locales[0] if estado.locales else None)
                cfg: dict = {"publico": f"{base_pub}/web/simulador.html" if base_pub else None,
                             "tunel": bool(estado.publica)}
                if self.es_local():
                    base = estado.publica or (estado.locales[0] if estado.locales else None)
                    cfg["control"] = f"{base}/web/control.html?k={estado.token}" if base else None
                    cfg["locales"] = [f"{u}/web/control.html?k={estado.token}" for u in estado.locales]
                return self.json(200, cfg)
            if ruta.startswith("/api/"):
                return self.json(404, {"error": "ruta"})
            # por el túnel solo se sirve lo que el público necesita: deck, simulador y datos
            if not self.es_local() and not (ruta.startswith("/web/") or ruta.startswith("/figuras/")
                                            or ruta.startswith("/tema/")):
                return self.json(404, {"error": "no disponible"})
            if not self.es_local() and ruta.endswith(".py"):
                return self.json(404, {"error": "no disponible"})
            return super().do_GET()

        def do_POST(self) -> None:
            ruta = urlsplit(self.path).path
            if ruta == "/api/ir":
                if not self.token_ok():
                    return self.json(403, {"error": "token"})
                d = self.leer_json()
                ir = d.get("ir")
                if ir not in ("next", "prev", "inicio") and not isinstance(ir, int):
                    return self.json(400, {"error": "ir"})
                n = estado.difundir(estado.decks, {"ir": ir})
                return self.json(200, {"decks": n})
            if ruta == "/api/estado":
                if not self.es_local():
                    return self.json(403, {"error": "solo local"})
                d = self.leer_json()
                estado.diapositiva = {k: d.get(k) for k in ("i", "total", "n", "de", "respaldo", "titulo")}
                estado.difundir(estado.controles, estado.diapositiva)
                return self.json(200, {"ok": True})
            return self.json(404, {"error": "ruta"})

    return Manejador


def ips_locales() -> list[str]:
    ips: set[str] = set()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))  # no envía nada: solo elige la interfaz
            ips.add(s.getsockname()[0])
    except OSError:
        pass
    return sorted(ip for ip in ips if not ip.startswith("127."))


def abrir_tunel(puerto: int, estado: Estado) -> subprocess.Popen | None:
    exe = shutil.which("cloudflared")
    if not exe:
        print("  ✗ no se encontró cloudflared (brew install cloudflared); sigo sin túnel")
        return None
    proc = subprocess.Popen(
        [exe, "tunnel", "--no-autoupdate", "--url", f"http://localhost:{puerto}"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )
    lista = threading.Event()

    def leer() -> None:
        assert proc.stdout is not None
        for linea in proc.stdout:
            m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", linea)
            if m and not estado.publica:
                estado.publica = m.group(0)
                lista.set()

    threading.Thread(target=leer, daemon=True).start()
    if not lista.wait(30):
        print("  ✗ el túnel no respondió en 30 s; sigo sin túnel")
    return proc


def ocupado(puerto: int) -> bool:
    """¿Ya responde algo en ese puerto? En macOS otro proceso puede tener localhost:p
    mientras este enlaza 0.0.0.0:p sin error, y el navegador hablaría con el otro."""
    for anfitrion in ("127.0.0.1", "::1"):
        fam = socket.AF_INET6 if ":" in anfitrion else socket.AF_INET
        with socket.socket(fam, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            if s.connect_ex((anfitrion, puerto)) == 0:
                return True
    return False


def main() -> None:
    sys.stdout.reconfigure(line_buffering=True)
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--puerto", type=int, default=8420)
    ap.add_argument("--tunel", action="store_true", help="URL https pública con cloudflared")
    ap.add_argument("--token", help="token fijo (por defecto, uno nuevo en cada arranque)")
    args = ap.parse_args()

    while ocupado(args.puerto):
        print(f"  el puerto {args.puerto} está ocupado; pruebo {args.puerto + 1}")
        args.puerto += 1
    estado = Estado(args.token or secrets.token_urlsafe(9))
    estado.locales = [f"http://{ip}:{args.puerto}" for ip in ips_locales()]
    servidor = ThreadingHTTPServer(("0.0.0.0", args.puerto), manejador(estado))
    servidor.daemon_threads = True
    threading.Thread(target=servidor.serve_forever, daemon=True).start()

    tunel = abrir_tunel(args.puerto, estado) if args.tunel else None

    print(f"\n  Deck (esta máquina):   http://localhost:{args.puerto}/web/")
    print("  Control (celular):     tecla Q en el deck muestra el QR")
    for u in estado.locales:
        print(f"    misma Wi-Fi:         {u}/web/control.html?k={estado.token}")
    if estado.publica:
        print(f"    por el túnel:        {estado.publica}/web/control.html?k={estado.token}")
        print(f"  Simulador (público):   {estado.publica}/web/simulador.html")
    else:
        print(f"  Simulador:             http://localhost:{args.puerto}/web/simulador.html")
    print("\n  Ctrl+C para terminar.\n")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.shutdown()
        if tunel:
            tunel.terminate()


if __name__ == "__main__":
    main()
