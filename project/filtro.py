"""Filtrado bayesiano de la posición de los recursos (``docs/roadmap-c5.md``, C5-B).

Es el paso que KB-2 deja como límite honesto: la lógica dice dónde **puede** estar un
recurso, no dónde **probablemente** está. Aquí la celda de cada recurso fuera de vista es
un estado oculto que sigue una caminata conocida, y el agente mantiene sobre ella una
distribución con el filtro *forward* de R&N §14.2 (predicción con el modelo de transición,
corrección con la observación). El soporte de esa distribución es exactamente la región
posible de :mod:`project.conocimiento`, lo cual se comprueba con una prueba.

Lo que el agente **no** recibe es λ: lo aprende mirando, con un modelo Beta–Bernoulli
(C5 §2.3), porque cada recurso que ve en dos observaciones seguidas es un ensayo de
Bernoulli (se movió o no).

Modelo de transición (``Resource.step``): con probabilidad λ el recurso pasa a una vecina
transitable elegida al azar, y una celda sin vecinas transitables no se mueve nunca:

.. math::

    P'(x) = (1-\\lambda)P(x)[\\deg x>0] + P(x)[\\deg x=0]
            + \\lambda \\sum_{y \\sim x} P(y)/\\deg y.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import math
from typing import Any

import numpy as np


@dataclass(slots=True)
class BetaBernoulli:
    """Posterior conjugada de una probabilidad de éxito (C5 §2.3).

    Attributes:
        a0: parámetro α del prior.
        b0: parámetro β del prior. Beta(1,1) es el prior uniforme.
        exitos: ensayos con éxito observados.
        fracasos: ensayos sin éxito observados.
    """

    a0: float = 1.0
    b0: float = 1.0
    exitos: int = 0
    fracasos: int = 0

    def observar(self, exito: bool) -> None:
        """Sumar un ensayo."""
        if exito:
            self.exitos += 1
        else:
            self.fracasos += 1

    @property
    def n(self) -> int:
        """Ensayos observados."""
        return self.exitos + self.fracasos

    @property
    def media(self) -> float:
        """Media posterior, :math:`(a_0+s)/(a_0+b_0+n)`."""
        return (self.a0 + self.exitos) / (self.a0 + self.b0 + self.n)

    @property
    def desviacion(self) -> float:
        """Desviación típica posterior, que decrece como :math:`1/\\sqrt{n}`."""
        a = self.a0 + self.exitos
        b = self.b0 + self.fracasos
        return math.sqrt(a * b / ((a + b) ** 2 * (a + b + 1)))


class MallaFiltro:
    """La geometría que comparten los filtros: índice de celdas y matriz de la caminata.

    El espacio de estados son las celdas dadas (en el modelo, ``OASysWorld.libres``, la
    componente de la base, que es cerrada bajo la deriva). La transición se precalcula una
    vez como matriz densa :math:`W^\\top` con :math:`W^\\top_{xy} = 1/\\deg y` si
    :math:`x \\sim y`, de modo que predecir es un producto matriz-vector.
    """

    def __init__(self, celdas: Sequence[Any]) -> None:
        """Construir la malla sobre ``celdas`` (deben ser transitables y cerradas bajo la
        relación de vecindad transitable)."""
        self.celdas: list[Any] = list(celdas)
        self.indice: dict[Any, int] = {c: i for i, c in enumerate(self.celdas)}
        n = len(self.celdas)
        self.grado = np.zeros(n, dtype=int)
        self._wt = np.zeros((n, n))
        for j, y in enumerate(self.celdas):
            vecinas = [c for c in y.connections.values() if not c.obstaculo]
            self.grado[j] = len(vecinas)
            for x in vecinas:
                i = self.indice.get(x)
                if i is None:
                    raise ValueError(
                        f"la vecina {x.coordinate} de {y.coordinate} no está en la malla: "
                        "el espacio de estados no es cerrado bajo la deriva"
                    )
                self._wt[i, j] = 1.0 / len(vecinas)
        self.movil = (self.grado > 0).astype(float)

    def __len__(self) -> int:
        """Número de estados."""
        return len(self.celdas)

    def indices(self, celdas: Iterable[Any]) -> np.ndarray:
        """Índices de las celdas que están en la malla (las demás se ignoran)."""
        idx = [i for c in celdas if (i := self.indice.get(c)) is not None]
        return np.fromiter(idx, dtype=int, count=len(idx))

    def predecir(self, p: np.ndarray, lam: float) -> np.ndarray:
        """Un paso del modelo de transición, sin mutar ``p``."""
        return p - lam * p * self.movil + lam * (self._wt @ p)


class FiltroRecurso:
    """Distribución sobre la celda de un recurso: filtro de rejilla (R&N §14.2).

    Attributes:
        malla: geometría compartida.
        p: probabilidad de cada celda de la malla.
    """

    __slots__ = ("malla", "p")

    def __init__(self, malla: MallaFiltro, cell: Any | None = None) -> None:
        """Un filtro colapsado en ``cell``, o uniforme si no se da celda."""
        self.malla = malla
        if cell is None:
            self.p = np.full(len(malla), 1.0 / len(malla))
        else:
            self.p = np.zeros(len(malla))
            self.avistar(cell)

    def avistar(self, cell: Any) -> None:
        """Se ve el recurso: la distribución colapsa a su celda."""
        self.p[:] = 0.0
        self.p[self.malla.indice[cell]] = 1.0

    def predecir(self, lam: float) -> None:
        """Paso de predicción: una deriva del mundo."""
        self.p = self.malla.predecir(self.p, lam)

    def corregir(self, celdas_vistas_sin_recurso: Iterable[Any]) -> None:
        """Paso de corrección: las celdas a la vista sin el recurso pasan a cero."""
        self.corregir_indices(self.malla.indices(celdas_vistas_sin_recurso))

    def corregir_indices(self, idx: np.ndarray) -> None:
        """:meth:`corregir` con los índices ya calculados (se comparten entre filtros)."""
        if len(idx) == 0:
            return
        self.p[idx] = 0.0
        total = self.p.sum()
        if total > 0:
            self.p /= total

    def propagado(self, lam: float, k: int) -> np.ndarray:
        """La distribución tras ``k`` derivas sin observar, **sin mutar** el filtro."""
        p = self.p
        for _ in range(k):
            p = self.malla.predecir(p, lam)
        return p if k else p.copy()

    def prob(self, cell: Any) -> float:
        """Probabilidad de que el recurso esté en ``cell`` ahora."""
        i = self.malla.indice.get(cell)
        return 0.0 if i is None else float(self.p[i])

    def soporte(self) -> set[Any]:
        """Celdas con probabilidad positiva: la región posible de KB-2."""
        return {self.malla.celdas[i] for i in np.flatnonzero(self.p > 0)}


class CreenciaBayesiana:
    """Lo que sabe ``BAYESIAN``: un filtro por recurso y λ aprendido.

    Comparte con :class:`project.conocimiento.BaseConocimiento` la interfaz que usa el
    recolector (``percibir``, ``recoger``, ``posible``, ``plan_valido``), así que se engancha
    en los mismos sitios.

    **El ensayo de Bernoulli.** Un recurso visto en la celda ``y`` (con alguna vecina
    transitable) cuenta como ensayo en la observación siguiente si ``y`` sigue a la vista:
    entonces el resultado es observable sin ambigüedad (está en ``y``: no se movió; no
    está: se movió, se le vea o no en otro sitio). Seleccionar los ensayos por la
    visibilidad de ``y`` y no por la del recurso es lo que los hace insesgados: qué ve el
    agente en la observación siguiente depende solo de su propio movimiento, decidido antes
    de la deriva, mientras que exigir *ver de nuevo al recurso* descarta justo a los que se
    movieron fuera de la vista y sesga λ̂ hacia abajo con radio pequeño. Solo se cuenta
    cuando hubo exactamente una deriva entre las dos observaciones.

    Attributes:
        malla: geometría compartida.
        filtros: filtro de cada recurso rastreado.
        aprendiz: posterior de λ.
        lam_fijo: si se da, el filtro predice con este λ en vez del aprendido. Solo para
            pruebas (calibración con λ conocido): la política nunca lo recibe.
    """

    def __init__(self, malla: MallaFiltro, *, lam_fijo: float | None = None) -> None:
        """Una creencia sin observaciones, con prior Beta(1,1) sobre λ."""
        self.malla = malla
        self.lam_fijo = lam_fijo
        self.filtros: dict[str, FiltroRecurso] = {}
        self.aprendiz = BetaBernoulli()
        self._previos: dict[str, Any] = {}
        self._derivas: int | None = None
        self._propagados: dict[str, list[np.ndarray]] = {}

    @property
    def lam(self) -> float:
        """El λ con que se predice: el aprendido (media posterior) salvo en pruebas."""
        return self.aprendiz.media if self.lam_fijo is None else self.lam_fijo

    @property
    def lambda_estimado(self) -> float:
        """λ̂, la media posterior."""
        return self.aprendiz.media

    # ------------------------------------------------------------------ TELL

    def percibir(
        self,
        vistos: Mapping[str, Any],
        visibles: Iterable[Any],
        *,
        derivas: int,
        t: int,
    ) -> None:
        """Incorporar una observación (mismos argumentos que en ``BaseConocimiento``).

        Primero se predice con el λ̂ que había y se corrige; luego se aprende de lo que se
        acaba de ver. Así la predicción de cada deriva no usa los ensayos sobre esa misma
        deriva.
        """
        pasos = 0 if self._derivas is None else derivas - self._derivas
        self._derivas = derivas
        vistas = visibles if isinstance(visibles, set | frozenset) else set(visibles)
        idx = self.malla.indices(vistas)

        lam = self.lam
        for rid, filtro in self.filtros.items():
            if rid in vistos:
                continue
            for _ in range(pasos):
                filtro.predecir(lam)
            filtro.corregir_indices(idx)
        for rid, cell in vistos.items():
            filtro = self.filtros.get(rid)
            if filtro is None:
                self.filtros[rid] = FiltroRecurso(self.malla, cell)
            else:
                filtro.avistar(cell)

        if pasos == 1:
            for rid, y in self._previos.items():
                if y in vistas and self.malla.grado[self.malla.indice[y]] > 0:
                    self.aprendiz.observar(vistos.get(rid) is not y)
        self._previos = dict(vistos)
        self._propagados.clear()

    def recoger(self, rid: str, t: int) -> None:
        """El recurso sale del mundo: se deja de rastrear y no cuenta como ensayo."""
        self.filtros.pop(rid, None)
        self._previos.pop(rid, None)
        self._propagados.pop(rid, None)

    # ------------------------------------------------------------------- ASK

    def posible(self, rid: str, cell: Any) -> bool:
        """¿Tiene ``cell`` probabilidad positiva ahora? (el filtro de candidatos de KB-2)."""
        filtro = self.filtros.get(rid)
        return filtro is not None and filtro.prob(cell) > 0

    def prob_al_llegar(self, rid: str, cell: Any, k: int) -> float:
        """Probabilidad de que ``rid`` esté en ``cell`` tras ``k`` derivas sin observarlo.

        Las propagaciones se guardan durante el tick, porque elegir objetivos encadenados
        pregunta por el mismo recurso con distintos ``k``.
        """
        filtro = self.filtros.get(rid)
        if filtro is None:
            return 0.0
        if k <= 0:
            return filtro.prob(cell)
        serie = self._propagados.setdefault(rid, [filtro.p])
        while len(serie) <= k:
            serie.append(self.malla.predecir(serie[-1], self.lam))
        i = self.malla.indice.get(cell)
        return 0.0 if i is None else float(serie[k][i])

    def plan_valido(
        self,
        rid: str,
        *,
        refutada: Any | None,
        celda_pick: Any,
        k: int,
        horizonte: str,
        costo: int,
    ) -> bool:
        """Reparar o mantener, por utilidad esperada (R&N §16.1).

        - ``"llegada"``: con :math:`q` la probabilidad de que el recurso esté en la celda
          del ``PICK`` al llegar (``k`` derivas), mantener cuesta en esperanza
          :math:`(1-q)(c+k)` —la caminata perdida más la replanificación forzada— y
          reparar cuesta :math:`c` ya, así que se repara si y solo si
          :math:`c < (1-q)(c+k)`.
        - ``"ahora"``: se repara si la celda que el monitoreo acaba de contradecir no es
          segura (:math:`P < 1`). Con visión total es el monitor de ``CLOSED_LOOP``.
        """
        if rid not in self.filtros:
            return False
        if horizonte == "ahora":
            return refutada is not None and self.filtros[rid].prob(refutada) >= 1.0
        q = self.prob_al_llegar(rid, celda_pick, k)
        return not costo < (1.0 - q) * (costo + k)
