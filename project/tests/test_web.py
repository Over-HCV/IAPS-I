"""El deck web: Que sus datos digan lo mismo que el modelo y que el control no sea público.

Tres frentes:

- el formato compacto de ``exportar._compactar`` se decodifica a los mismos frames que
  produce ``animacion.traza_corrida`` (si se desalinea, el simulador mostraría otra
  corrida con toda convicción);
- los JSON versionados en ``beamer/web/datos/`` tienen la forma que esperan
  ``graficas.js`` y ``simulador.html``;
- ``servidor.py`` rechaza las órdenes sin token y no entrega la URL de control a quien
  llega por el túnel.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import pytest  # noqa: E402

from project import animacion as anim  # noqa: E402

WEB = Path(__file__).resolve().parents[1] / "beamer" / "web"
DATOS = WEB / "datos"


def _cargar(nombre: str):
    """Importar un script de beamer/web como módulo (no es parte del paquete)."""
    sys.path.insert(0, str(WEB.parent))  # exportar.py importa figuras.py, su vecino
    spec = importlib.util.spec_from_file_location(f"web_{nombre}", WEB / f"{nombre}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def exportar():
    return _cargar("exportar")


@pytest.fixture(scope="module")
def servidor():
    return _cargar("servidor")


# ------------------------------------------------------------- formato compacto


def test_compactar_es_reversible(exportar):
    """Decodificar el formato compacto devuelve el agente, los recursos y la ruta reales."""
    _, frames = anim.traza_corrida(60, policy="CLOSED_LOOP", lambda_dinamismo=0.5,
                                   costo_edicion=2, radio=3, rng=3)
    co = exportar._compactar(frames)
    lado = exportar.LADO
    celda = lambda n: (n // lado, n % lado)  # noqa: E731
    assert len(co["ag"]) == len(frames)
    for i, f in enumerate(frames):
        assert celda(co["ag"][i]) == tuple(f.agente)
        rec = co["rec"][i]
        assert {f"r{rec[k]}": celda(rec[k + 1]) for k in range(0, len(rec), 2)} == {
            rid: tuple(c) for rid, c in f.recursos.items()}
        assert [celda(c) for c in co["ruta"][i]] == [tuple(c) for c in f.ruta]
        assert co["ent"][i] == f.metricas["entregas"]
        assert (co["d"][i] == 0) == (f.deliberando is None)


def test_compactar_regiones_solo_si_se_piden(exportar):
    _, frames = anim.traza_corrida(20, policy="KNOWLEDGE_BASED", lambda_dinamismo=0.25,
                                   radio=3, rng=3)
    assert "reg" not in exportar._compactar(frames)
    assert len(exportar._compactar(frames, regiones=True)["reg"]) == len(frames)


# ------------------------------------------------------------- datos versionados


def test_indice_y_corridas_existen():
    ind = json.loads((DATOS / "corridas" / "indice.json").read_text())
    assert ind["orden"] and set(ind["orden"]) == set(ind["semillas"])
    for s in ind["orden"]:
        for lam in ind["lambdas"]:
            for pol in ind["politicas"]:
                for c in ([5] if pol in ind["sin_c"] else ind["costos"]):
                    ruta = DATOS / "corridas" / f"{s}-{pol}-{lam:g}-{c}.json"
                    assert ruta.exists(), ruta.name
    co = json.loads((DATOS / "corridas" / f"{ind['orden'][0]}-CLOSED_LOOP-0.5-5.json").read_text())
    assert len(co["ag"]) == ind["ticks"] + 1


def test_frontera_cubre_las_celdas_del_simulador():
    """El simulador muestra el promedio del barrido para cada (λ, c) que ofrece."""
    ind = json.loads((DATOS / "corridas" / "indice.json").read_text())
    f = json.loads((DATOS / "frontera.json").read_text())
    for c in ind["costos"]:
        for pol in ind["politicas"]:
            xs = {d["x"] for d in f[str(c)][pol]}
            assert set(ind["lambdas"]) <= xs


@pytest.mark.parametrize("nombre", ["frontera", "abierto-cerrado", "caliente-frio", "dinamica",
                                    "kb-r3", "mecanismo", "quien-gana", "escasez",
                                    "sensibilidad", "abc", "fiabilidad",
                                    "kb-corrida"])
def test_datos_de_figuras(nombre):
    assert json.loads((DATOS / f"{nombre}.json").read_text())


def test_frontera_coincide_con_el_deck():
    """Las cifras que el texto de la diapositiva cita salen del JSON que se anima."""
    f = json.loads((DATOS / "frontera.json").read_text())
    en = lambda c, p: next(d["m"] for d in f[c][p] if d["x"] == 0.5)  # noqa: E731
    assert round(en("2", "MODEL_BASED"), 1) == 98.3
    assert round(max(en("2", p) for p in ("OPEN_LOOP", "COLD_RESTART", "CLOSED_LOOP")), 1) == 53.3
    assert round(max(en("5", p) for p in ("OPEN_LOOP", "COLD_RESTART", "CLOSED_LOOP")), 1) == 27.0


# ------------------------------------------------------------------- servidor


@pytest.fixture()
def en_marcha(servidor):
    estado = servidor.Estado("secreto")
    estado.locales = ["http://192.0.2.1:1"]
    srv = ThreadingHTTPServer(("127.0.0.1", 0), servidor.manejador(estado))
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", estado
    srv.shutdown()


def _pedir(url: str, *, datos: dict | None = None, cabeceras: dict | None = None):
    req = urllib.request.Request(url, data=None if datos is None else json.dumps(datos).encode(),
                                 headers={"Content-Type": "application/json", **(cabeceras or {})})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def test_ir_exige_token(en_marcha):
    base, _ = en_marcha
    assert _pedir(f"{base}/api/ir", datos={"ir": "next"})[0] == 403
    assert _pedir(f"{base}/api/ir", datos={"ir": "next"}, cabeceras={"X-Token": "otro"})[0] == 403
    codigo, cuerpo = _pedir(f"{base}/api/ir", datos={"ir": "next"}, cabeceras={"X-Token": "secreto"})
    assert codigo == 200 and cuerpo == {"decks": 0}
    assert _pedir(f"{base}/api/ir", datos={"ir": "borrar"}, cabeceras={"X-Token": "secreto"})[0] == 400


def test_ir_llega_al_deck(en_marcha):
    base, estado = en_marcha
    q = estado.suscribir(estado.decks)
    _pedir(f"{base}/api/ir", datos={"ir": "prev"}, cabeceras={"X-Token": "secreto"})
    assert json.loads(q.get(timeout=2)) == {"ir": "prev"}


def test_control_no_sale_por_el_tunel(en_marcha):
    base, _ = en_marcha
    _, local = _pedir(f"{base}/api/config")
    assert "secreto" in local["control"]
    _, tunel = _pedir(f"{base}/api/config", cabeceras={"Cf-Ray": "x", "Cf-Connecting-Ip": "203.0.113.9"})
    assert "control" not in tunel and "secreto" not in json.dumps(tunel)


def test_tunel_no_sirve_codigo(en_marcha):
    base, _ = en_marcha
    cab = {"Cf-Ray": "x"}
    assert _pedir(f"{base}/web/servidor.py", cabeceras=cab)[0] == 404
    assert _pedir(f"{base}/main.tex", cabeceras=cab)[0] == 404
    assert _pedir(f"{base}/api/estado", datos={"i": 3}, cabeceras=cab)[0] == 403
