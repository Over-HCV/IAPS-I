"""Datos del deck web (project/beamer/web/datos/), desde los mismos resultados del PDF.

Responsabilidad: escribir en JSON lo que ``web/js/graficas.js`` y ``web/js/mundo.js``
animan. Ninguna cifra se escribe a mano: las agregaciones son las mismas que usa
``beamer/figuras.py`` para los PNG (se importan de ahí ``_medias`` y ``_dif``, y
las constantes de color), y las corridas del mundo salen de
``animacion.traza_corrida``, es decir, del modelo MESA corriendo de verdad.

Se corre desde ``figuras.sh`` o, directamente, desde la raíz del repositorio:

    PYTHONPATH=. .venv/bin/python project/beamer/web/exportar.py [nombre ...]

Salidas:

- ``datos/<figura>.json``: Una por diapositiva animada.
- ``datos/corridas/<semilla>-<política>-<λ>-<c>.json``: Una corrida de 400 ticks en
  formato compacto (ver :func:`_compactar`), para el simulador y las diapositivas del
  mundo. Se cargan bajo demanda, así que el total no pesa en la carga del deck.
- ``datos/corridas/indice.json``: Qué combinaciones existen y la retícula de cada
  semilla (obstáculos y base), que no cambia con la política.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))  # para importar figuras.py como módulo hermano

import figuras as fg  # noqa: E402
from project import analysis as an  # noqa: E402

DATOS = AQUI / "datos"
CORRIDAS = DATOS / "corridas"

SEMILLAS = (7, 11, 3)  # «Mundo 1, 2, 3» del simulador, en este orden
LAMBDAS = (0.0, 0.1, 0.25, 0.5)
COSTOS = (0, 2, 5)
POL_SIM = ("MODEL_BASED", "OPEN_LOOP", "COLD_RESTART", "CLOSED_LOOP")
SIN_C = {"MODEL_BASED"}  # no delibera: c no cambia nada, se corre una vez por λ
TICKS = 400
LADO = 15


def _r(x: Any, n: int = 3) -> float | None:
    """Redondeo para JSON; NaN pasa a null."""
    v = float(x)
    return None if np.isnan(v) else round(v, n)


def _escribir(nombre: str, obj: Any, carpeta: Path = DATOS) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{nombre}.json"
    ruta.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    print(f"  {ruta.relative_to(AQUI)}  ({ruta.stat().st_size / 1024:.0f} KB)")


def _serie_medias(m: pd.DataFrame, pol: str, x: str) -> list[dict[str, Any]]:
    d = m[m.politica == pol].sort_values(x)
    return [{"x": _r(a), "m": _r(b), "e": _r(c)} for a, b, c in zip(d[x], d["mean"], d.err)]


def _difs(d: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {"lam": _r(r.lambda_dinamismo), "c": int(r.costo_edicion), "m": _r(r.media),
         "e": _r(r.err)}
        for r in d.itertuples()
    ]


# ------------------------------------------------------------------ figuras


def frontera() -> None:
    df = an.cargar("principal")
    m = fg._medias(df, ["lambda_dinamismo", "costo_edicion"])
    out = {}
    for c in sorted(m.costo_edicion.unique()):
        sub = m[m.costo_edicion == c]
        out[str(int(c))] = {p: _serie_medias(sub, p, "lambda_dinamismo")
                            for p in fg.POLITICAS[:6]}
    _escribir("frontera", out)


def abierto_cerrado() -> None:
    df = an.cargar("principal")
    d = fg._dif(df, "OPEN_LOOP", "CLOSED_LOOP", ("lambda_dinamismo", "costo_edicion"))
    _escribir("abierto-cerrado", _difs(d[d.lambda_dinamismo > 0]))


def caliente_frio() -> None:
    df = an.cargar("principal")
    d = fg._dif(df, "CLOSED_LOOP", "COLD_RESTART", ("lambda_dinamismo", "costo_edicion"))
    _escribir("caliente-frio", _difs(d[d.lambda_dinamismo > 0]))


def dinamica() -> None:
    t = an.agregar_tiempo(an.cargar_dinamica(), "entregas")
    pols = ["REFLEX", "MODEL_BASED", "OPEN_LOOP", "COLD_RESTART", "CLOSED_LOOP"]
    out = {}
    for lam in (0.1, 0.5):
        sub = t[t.faceta.astype(float) == lam]
        out[f"{lam:g}"] = {
            p: [[int(x), _r(y), _r(e)] for x, y, e in
                sub[sub.serie == p].sort_values("x")[["x", "y", "err"]].itertuples(index=False)]
            for p in pols
        }
    _escribir("dinamica", out)


def kb_r3() -> None:
    df = an.cargar("conocimiento")
    m = fg._medias(df[df.radio == "3"], ["lambda_dinamismo"])
    pols = ["MODEL_BASED", "OPEN_LOOP", "CLOSED_LOOP", "KNOWLEDGE_BASED", "BAYESIAN"]
    _escribir("kb-r3", {p: _serie_medias(m, p, "lambda_dinamismo") for p in pols})


def mecanismo() -> None:
    df = an.cargar("conocimiento")
    df = df[(df.radio == "3") & (df.lambda_dinamismo == 0.5)].copy()
    df["proactivas"] = df.n_ediciones - df.n_ediciones_por_fallo
    pols = ["CLOSED_LOOP", "KNOWLEDGE_BASED", "BAYESIAN"]
    paneles = []
    for col, titulo, dec in (("proactivas", "Reparaciones proactivas", 1),
                             ("n_ediciones_desperdiciadas", "Ediciones desperdiciadas", 1),
                             ("pasos_deliberando", "Ticks deliberando (de 400)", 0),
                             ("utilidad_neta", "Utilidad neta", 1)):
        g = df.groupby("politica")[col].agg(["mean", "std", "count"]).loc[pols]
        g["err"] = g["std"] / g["count"] ** 0.5
        paneles.append({"titulo": titulo, "dec": dec,
                        "barras": [{"pol": p, "m": _r(g.loc[p, "mean"]), "e": _r(g.loc[p, "err"])}
                                   for p in pols]})
    _escribir("mecanismo", paneles)


def quien_gana() -> None:
    k = an.cargar("conocimiento")
    k = k[(k.radio == "3") & (k.lambda_dinamismo == 0.5)]
    p = an.cargar("principal")
    p = p[(p.lambda_dinamismo == 0.5) & (p.costo_edicion == 5)]
    filas = []
    for pol, src, delibera in (("MODEL_BASED", k, False), ("REFLEX", p, False),
                               ("KNOWLEDGE_BASED", k, True), ("OPEN_LOOP", k, True),
                               ("BAYESIAN", k, True), ("CLOSED_LOOP", k, True),
                               ("COLD_RESTART", p, True)):
        v = src[src.politica == pol].utilidad_neta
        filas.append({"pol": pol, "m": _r(v.mean()), "e": _r(v.std() / len(v) ** 0.5),
                      "delibera": delibera})
    _escribir("quien-gana", filas)


def escasez() -> None:
    inf, mix = an.cargar("escasez_inf"), an.cargar("escasez")
    K = [2, 4, 8, 16]

    def serie(df: pd.DataFrame, a: str, b: str, lam: float, rotulo: str, punteada: bool,
              color: str) -> dict[str, Any]:
        d = an.diferencia_pareada(df[df.lambda_dinamismo == lam], a, b,
                                  por=("n_resources",)).set_index("n_resources").loc[K]
        return {"rotulo": rotulo, "punteada": punteada, "color": color,
                "puntos": [{"x": k, "m": _r(m), "e": _r(e)}
                           for k, m, e in zip(K, d.media, d.err)]}

    cl, mb = fg.COLOR["CLOSED_LOOP"], fg.COLOR["MODEL_BASED"]
    _escribir("escasez", [
        {"titulo": "Replanificar es gratis (r = ∞, c = 0, p = 1)", "y": [0, 75], "series": [
            serie(inf, "CLOSED_LOOP", "OPEN_LOOP", 0.5, "CL − OL, λ = 0.5", False, cl),
            serie(inf, "CLOSED_LOOP", "OPEN_LOOP", 0.1, "CL − OL, λ = 0.1", True, cl)]},
        {"titulo": "Replanificar cuesta (r = 3, c = 5, p = 0.9)", "y": [-25, 118], "series": [
            serie(mix, "MODEL_BASED", "OPEN_LOOP", 0.5, "MB − OL, λ = 0.5", False, mb),
            serie(mix, "MODEL_BASED", "CLOSED_LOOP", 0.25, "MB − CL, λ = 0.25", True, mb)]},
    ])


def sensibilidad() -> None:
    from project import sensibilidad as se

    tab = se.tabla_sensibilidad()
    tab = tab[tab.politica == "CLOSED_LOOP"]
    eta_d, _ = se.tabla_sensibilidad_delta()
    corto = {"lambda_dinamismo": "λ", "costo_edicion": "c", "competencia": "p",
             "radio": "r", "presupuesto": "B"}

    def valor(datos: pd.DataFrame, b: str, f: str) -> float | None:
        s = datos[(datos.barrido == b) & (datos.factor == f)]
        return None if s.empty else _r(s.eta2.iloc[0])

    filas = [{"barrido": b, "factor": corto[f], "lambda": f == "lambda_dinamismo",
              "nivel": valor(tab, b, f), "dif": valor(eta_d, b, f)}
             for b, factores in se.BARRIDOS.items() for f in factores]
    _escribir("sensibilidad", filas)


def abc() -> None:
    from project import calibracion as ca

    tabla = ca.cargar_referencia()
    lam, p = 0.25, 0.7
    res = ca.abc_rechazo(ca.observar(lam, p), tabla)
    post, ic = res.posterior, res.intervalos
    # la previa se submuestrea: 3.000 puntos de fondo no cambian la lectura y pesan
    previa = tabla.sample(n=min(1500, len(tabla)), random_state=0)
    # las aceptadas, ordenadas por distancia si la hay: se dibujan de la mejor a la peor
    if "dist" in post.columns:
        post = post.sort_values("dist")
    _escribir("abc", {
        "verdad": [lam, p],
        "prior": {"lam": list(ca.PRIOR["lam"]), "p": list(ca.PRIOR["p"])},
        "previa": [[_r(a), _r(b)] for a, b in zip(previa.lam, previa.p)],
        "aceptadas": [[_r(a), _r(b)] for a, b in zip(post.lam, post.p)],
        "ic": {k: [_r(ic.loc[k, "q05"]), _r(ic.loc[k, "q95"])] for k in ("lam", "p")},
    })


def fiabilidad() -> None:
    d = an.datos_calibracion()
    _escribir("fiabilidad", [{"x": _r(a), "y": _r(b), "e": _r(c)}
                             for a, b, c in zip(d.p_media, d.frecuencia, d.err)])


def _celda(coord: Any) -> int:
    """(x, y) -> un entero x·15 + y: la mitad de bytes que un par."""
    x, y = coord
    return int(x) * LADO + int(y)


def _rid(rid: str) -> int:
    return int(rid.lstrip("r"))


EDICION = {None: 0, "aplicada": 1, "rechazada": 2, "desperdiciada": 3}
ACCION = {a: i for i, a in enumerate(
    ("INICIO", "GOTO", "PICK", "DELIVER", "SCAN", "DELIBERAR", "FALLO", "ESPERA"))}


def _compactar(frames: list[Any], *, regiones: bool = False) -> dict[str, Any]:
    """Frames de ``animacion`` a columnas compactas (una lista por campo, índice = tick).

    Celdas como ``x·15 + y``; recursos y creencias como pares planos ``[rid, celda, …]``;
    ``d`` es ``[transcurrido, duración]`` de la deliberación en curso o 0; ``e`` el
    código de :data:`EDICION`; ``a`` el de :data:`ACCION`. Las métricas van acumuladas.
    """
    out: dict[str, list[Any]] = {k: [] for k in
                                 ("ag", "rec", "cre", "obj", "car", "ruta", "a", "d", "e",
                                  "ent", "edi", "des", "del", "per")}
    if regiones:
        out["reg"] = []
    for f in frames:
        out["ag"].append(_celda(f.agente))
        out["rec"].append([v for rid, c in f.recursos.items() for v in (_rid(rid), _celda(c))])
        out["cre"].append([v for rid, c in f.creencias.items() for v in (_rid(rid), _celda(c))])
        out["obj"].append(-1 if f.objetivo is None else _rid(f.objetivo))
        out["car"].append(len(f.carrying))
        out["ruta"].append([_celda(c) for c in f.ruta])
        out["a"].append(ACCION.get(f.accion, 0))
        out["d"].append(list(f.deliberando) if f.deliberando else 0)
        out["e"].append(EDICION.get(f.edicion, 0))
        m = f.metricas
        out["ent"].append(int(m["entregas"]))
        out["edi"].append(int(m["n_ediciones"]))
        out["des"].append(int(m["n_ediciones_desperdiciadas"]))
        out["del"].append(int(m["pasos_deliberando"]))
        out["per"].append(int(m["carga_perdida"]))
        if regiones:
            out["reg"].append({str(_rid(rid)): [_celda(c) for c in cs]
                               for rid, cs in f.regiones.items()})
    return out


def _reticula(modelo: Any) -> dict[str, Any]:
    obst = np.asarray(modelo.grid.obstaculo.data)
    return {
        "lado": LADO,
        "obst": [_celda((x, y)) for x, y in zip(*np.nonzero(obst))],
        "base": _celda(modelo.base.coordinate),
        "radio": modelo.radio,
        "capacidad": modelo.capacidad,
    }


def corridas() -> None:
    from project import animacion as ani

    CORRIDAS.mkdir(parents=True, exist_ok=True)
    # "orden": JS ordena numéricamente las claves que parecen enteros, así que el orden de
    # «Mundo 1, 2, 3» va en una lista aparte
    indice: dict[str, Any] = {"semillas": {}, "orden": [str(s) for s in SEMILLAS],
                              "lambdas": list(LAMBDAS), "costos": list(COSTOS),
                              "politicas": list(POL_SIM), "sin_c": sorted(SIN_C),
                              "ticks": TICKS, "colores": fg.COLOR}
    total = 0
    for s in SEMILLAS:
        for lam in LAMBDAS:
            for pol in POL_SIM:
                for c in ((5,) if pol in SIN_C else COSTOS):
                    modelo, frames = ani.traza_corrida(
                        TICKS, policy=pol, lambda_dinamismo=lam, costo_edicion=c, radio=3,
                        rng=s)
                    ret = _reticula(modelo)
                    previa = indice["semillas"].setdefault(str(s), ret)
                    if previa["obst"] != ret["obst"] or previa["base"] != ret["base"]:
                        raise RuntimeError(f"la semilla {s} no da el mismo mundo con {pol}")
                    nombre = f"{s}-{pol}-{lam:g}-{c}"
                    ruta = CORRIDAS / f"{nombre}.json"
                    ruta.write_text(json.dumps(_compactar(frames), separators=(",", ":")))
                    total += ruta.stat().st_size
    _escribir("indice", indice, CORRIDAS)
    print(f"  corridas: {total / 1e6:.1f} MB en {len(list(CORRIDAS.glob('*-*.json')))} archivos")


def conocimiento() -> None:
    """La corrida de la tira del agente lógico (``figuras.fig_tiras``), con su región."""
    from project import animacion as ani

    modelo, frames = ani.traza_corrida(80, policy="KNOWLEDGE_BASED", lambda_dinamismo=0.25,
                                       costo_edicion=5, radio=3, rng=3)
    _escribir("kb-corrida", {"reticula": _reticula(modelo),
                             "corrida": _compactar(frames, regiones=True)})


# ---------------------------------------------------------------------- main

EXPORTES = {
    "frontera": frontera,
    "abierto-cerrado": abierto_cerrado,
    "caliente-frio": caliente_frio,
    "dinamica": dinamica,
    "kb-r3": kb_r3,
    "mecanismo": mecanismo,
    "quien-gana": quien_gana,
    "escasez": escasez,
    "sensibilidad": sensibilidad,
    "abc": abc,
    "fiabilidad": fiabilidad,
    "conocimiento": conocimiento,
    "corridas": corridas,
}


def main(nombres: list[str]) -> None:
    pedidas = nombres or list(EXPORTES)
    desconocidas = [n for n in pedidas if n not in EXPORTES]
    if desconocidas:
        sys.exit(f"exportes desconocidos: {desconocidas}; opciones: {list(EXPORTES)}")
    for n in pedidas:
        EXPORTES[n]()


if __name__ == "__main__":
    main(sys.argv[1:])
