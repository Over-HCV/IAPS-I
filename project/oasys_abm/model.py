"""El entorno: retícula con recursos que derivan y un agente que los recoge.

La especificación formal (PEAS, clasificación del entorno, métricas) está en
``docs/02-design.md``. Este módulo la implementa.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import OrthogonalVonNeumannGrid
from oasys_abm.agents import Collector, Policy, Resource
from oasys_abm.oracle import Oracle


class OASysWorld(Model):
    """Retícula de recolección con recursos móviles.

    La tarea es de horizonte largo por construcción: cada entrega repone un recurso, así
    que el agente encadena subobjetivos hasta agotar ``max_steps``. Es el régimen donde
    un plan estático se degrada, que es lo que motiva el experimento.

    Args:
        policy: arquitectura de agente (ver ``agents.Policy``).
        size: lado de la retícula.
        n_resources: recursos simultáneos en el mundo.
        capacidad: recursos que el agente debe reunir antes de entregar. Es lo que crea
            *trabajo en vuelo*, sin el cual un reinicio en frío no pierde nada y la
            comparación ``cold`` contra ``hot`` se vacía.
        lambda_dinamismo: probabilidad por tick de que un recurso se desplace.
        competencia: probabilidad ``p`` de que el oráculo proponga la reparación óptima.
        costo_edicion: ticks ``c`` que consume cada deliberación.
        radio: radio de observación. ``None`` = observabilidad total.
        presupuesto: ediciones permitidas. ``None`` = ilimitadas.
        kappa: precio por tick de deliberación, para la utilidad neta.
        valor_entrega: valor de cada entrega, para la utilidad neta.
        densidad_obstaculos: fracción de celdas bloqueadas.
        epsilon_reflejo: probabilidad de movimiento aleatorio en las políticas
            reactivas, para escapar de mínimos locales (R&N §2.4.2).
        max_steps: horizonte de la corrida.
        torus: si la retícula da la vuelta.
        rng: semilla del generador. Se usa ``rng`` y no ``seed`` porque es el nombre
            que ``batch_run`` inyecta y porque ``seed`` está deprecado en Mesa 3.5.
    """

    def __init__(
        self,
        *,
        policy: Policy | str = Policy.CLOSED_LOOP,
        size: int = 20,
        n_resources: int = 8,
        capacidad: int = 3,
        lambda_dinamismo: float = 0.1,
        competencia: float = 0.9,
        costo_edicion: int = 5,
        radio: int | None = 3,
        presupuesto: int | None = None,
        kappa: float = 0.0,
        valor_entrega: float = 10.0,
        densidad_obstaculos: float = 0.15,
        epsilon_reflejo: float = 0.15,
        max_steps: int = 1000,
        torus: bool = False,
        rng: int | None = None,
    ) -> None:
        """Construir el mundo y colocar agentes y recursos."""
        super().__init__(rng=rng)

        self.policy = Policy(policy)
        self.lambda_dinamismo = lambda_dinamismo
        self.capacidad = capacidad
        self.costo_edicion = costo_edicion
        self.radio = radio
        self.presupuesto = presupuesto
        self.kappa = kappa
        self.valor_entrega = valor_entrega
        self.epsilon_reflejo = epsilon_reflejo
        self.max_steps = max_steps
        self.dimensions = (size, size)
        self.torus = torus

        self.grid: OrthogonalVonNeumannGrid = OrthogonalVonNeumannGrid(
            (size, size), torus=torus, capacity=None, random=self.random
        )
        self.grid.create_property_layer("obstaculo", default_value=False, dtype=bool)

        self.base = self.grid[(0, 0)]
        self._colocar_obstaculos(densidad_obstaculos)
        self.libres = self._componente_de_la_base()

        self.oracle = Oracle(
            p=competencia,
            cost=costo_edicion,
            random=self.random,
            passable=self.passable,
            dimensions=self.dimensions,
            torus=torus,
            cells=self.libres,
        )

        self._siguiente_rid = 0
        for _ in range(n_resources):
            self.reponer_recurso()

        self.collector = Collector(self, self.policy)
        self._divergente_real = False
        self._deteccion_pendiente = False
        self._target_anterior: str | None = None
        self._inicio_divergencia = 0
        self.divergencias_reales = 0
        self.divergencias_detectadas = 0
        self.latencias: list[int] = []

        self.datacollector = DataCollector(model_reporters=REPORTERS)
        self.datacollector.collect(self)

    # ------------------------------------------------------------------ entorno

    def passable(self, cell: Any) -> bool:
        """Si una celda puede ser ocupada. Los recursos no bloquean el paso."""
        return not cell.obstaculo

    def _colocar_obstaculos(self, densidad: float) -> None:
        """Bloquear celdas al azar, dejando siempre libre la base."""
        capa = self.grid.obstaculo
        for cell in self.grid.all_cells.cells:
            if cell is self.base:
                continue
            if self.random.random() < densidad:
                capa.data[cell.coordinate] = True

    def _componente_de_la_base(self) -> list[Any]:
        """Celdas alcanzables desde la base.

        Los obstáculos aleatorios pueden aislar regiones enteras. Restringir el mundo
        útil a la componente conexa de la base evita generar tareas imposibles, que
        contaminarían las métricas con fallos que no dicen nada sobre la política.

        El resultado se ordena por coordenada a propósito. Devolver ``list(set)`` haría
        que el orden dependiera del hash de los objetos —es decir, de direcciones de
        memoria— y con él el resultado de cada ``random.choice`` sobre esta lista. Las
        corridas dejarían de ser reproducibles con la misma semilla, que es el control
        de sanidad nº 4 de ``docs/02-design.md``.
        """
        vistos = {self.base}
        cola = deque([self.base])
        while cola:
            cell = cola.popleft()
            for nb in cell.connections.values():
                if nb not in vistos and self.passable(nb):
                    vistos.add(nb)
                    cola.append(nb)
        return sorted(vistos, key=lambda c: c.coordinate)

    # ----------------------------------------------------------------- recursos

    def recursos(self) -> list[Resource]:
        """Recursos vivos en la retícula."""
        tipo = self.agents_by_type.get(Resource)
        return list(tipo) if tipo else []

    def recurso_en(self, cell: Any, rid: str) -> Resource | None:
        """El recurso ``rid`` si está en esa celda."""
        for agent in cell.agents:
            if isinstance(agent, Resource) and agent.rid == rid:
                return agent
        return None

    def celda_real_visible(self, rid: str, vision: list[Any]) -> Any | None:
        """Dónde está realmente el recurso, **si el agente puede verlo**.

        Devolver ``None`` cuando está fuera de vista es lo que impide que el oráculo
        haga trampa: sin observación no hay reparación correcta posible, por competente
        que sea el replanificador.
        """
        visibles = set(vision)
        for recurso in self.recursos():
            if recurso.rid == rid and recurso.cell in visibles:
                return recurso.cell
        return None

    def retirar_recurso(self, recurso: Resource) -> None:
        """Sacar un recurso del mundo porque el agente lo recogió."""
        recurso.remove()

    def soltar_recurso(self, rid: str, cell: Any) -> None:
        """Devolver al mundo la carga perdida en un reinicio en frío."""
        Resource(self, cell, rid)

    def reponer_recurso(self) -> None:
        """Crear un recurso nuevo en una celda libre al azar."""
        candidatas = [c for c in self.libres if c is not self.base]
        if not candidatas:
            return
        rid = f"r{self._siguiente_rid}"
        self._siguiente_rid += 1
        Resource(self, self.random.choice(candidatas), rid)

    # --------------------------------------------------------------------- ciclo

    def notificar_deteccion(self) -> None:
        """El agente avisa de que notó una divergencia.

        Solo cuenta si hay una divergencia real pendiente de ser detectada. Sin ese
        emparejamiento, el agente puede notar varias veces la misma discrepancia
        —al verla moverse, y luego al ver vacía la celda vieja— y la cifra de detectadas
        superaría a la de reales.

        Se registra además **cuánto tardó** en notarla. Esa latencia, y no la fracción de
        divergencias perdidas, es el costo real de la observabilidad parcial en este
        entorno: como el plan lleva al agente precisamente a la celda donde creía que
        estaba el recurso, casi toda divergencia termina descubriéndose. Lo que cambia
        con el radio de visión no es *si* se entera, sino *cuándo* — y mientras tanto
        camina hacia un sitio equivocado.
        """
        if self._deteccion_pendiente:
            self.divergencias_detectadas += 1
            self.latencias.append(self.steps - self._inicio_divergencia)
            self._deteccion_pendiente = False

    def _contar_divergencia_real(self) -> None:
        """Contar las divergencias que ocurren, las vea el agente o no.

        Se cuentan como eventos —transiciones a estado divergente— y no por tick, para
        que una divergencia larga no infle la cifra. La diferencia contra
        ``divergencias_detectadas`` es exactamente el costo de la observabilidad
        parcial.
        """
        rid = self.collector.target
        if rid != self._target_anterior and self._deteccion_pendiente:
            # El agente cambió de objetivo sin haber llegado a notar la divergencia
            # anterior: se la perdió. Sin esta expiración, una detección tardía —ochenta
            # ticks después, con el plan ya rehecho— contaría igual que una a tiempo, y
            # la ceguera saldría nula con cualquier radio de visión.
            self._deteccion_pendiente = False
        self._target_anterior = rid

        if rid is None:
            self._divergente_real = False
            return
        creido = self.collector.belief.get(rid)
        real = next((r.cell for r in self.recursos() if r.rid == rid), None)
        ahora = creido is not None and real is not None and creido is not real
        if ahora and not self._divergente_real:
            self.divergencias_reales += 1
            self._deteccion_pendiente = True
            self._inicio_divergencia = self.steps
        self._divergente_real = ahora

    def step(self) -> None:
        """Un tick: el agente actúa, el mundo deriva, se miden las consecuencias."""
        self.collector.step()
        recursos = self.agents_by_type.get(Resource)
        if recursos:
            recursos.shuffle_do("step")
        self._contar_divergencia_real()
        self.datacollector.collect(self)
        if self.steps >= self.max_steps:
            self.running = False


def _c(model: OASysWorld) -> Collector:
    """Atajo al recolector, para los reporters."""
    return model.collector


REPORTERS = {
    "politica": lambda m: str(m.policy),
    "entregas": lambda m: _c(m).entregas,
    "pasos_utiles": lambda m: _c(m).pasos_utiles,
    "pasos_deliberando": lambda m: _c(m).pasos_deliberando,
    "n_ediciones": lambda m: _c(m).n_ediciones,
    "n_ediciones_desperdiciadas": lambda m: _c(m).n_ediciones_desperdiciadas,
    "divergencias_reales": lambda m: m.divergencias_reales,
    "divergencias_detectadas": lambda m: m.divergencias_detectadas,
    "tareas_fallidas": lambda m: _c(m).tareas_fallidas,
    "carga_perdida": lambda m: _c(m).carga_perdida,
    "ceguera": lambda m: (
        0.0
        if m.divergencias_reales == 0
        else 1.0 - m.divergencias_detectadas / m.divergencias_reales
    ),
    "latencia_deteccion": lambda m: (
        0.0 if not m.latencias else sum(m.latencias) / len(m.latencias)
    ),
    "utilidad_bruta": lambda m: m.valor_entrega * _c(m).entregas,
    "costo_deliberacion": lambda m: m.kappa * _c(m).pasos_deliberando,
    "utilidad_neta": lambda m: (
        m.valor_entrega * _c(m).entregas - m.kappa * _c(m).pasos_deliberando
    ),
}
"""Reporters de modelo. Las definiciones operacionales están en ``docs/02-design.md`` §4."""
