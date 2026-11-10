"""Las seis arquitecturas de agente.

Las tres primeras recorren la taxonomía de Russell & Norvig §2.4 (reflejo simple, reflejo
basado en modelo, basado en objetivos), que es el primer resultado de aprendizaje de la
asignatura. Las tres últimas replanifican al divergir y difieren en cuándo aplica la
reparación: **en frío** (en la ejecución siguiente, y el trabajo en curso se pierde), **en
caliente** (en sitio, sobre la ejecución en curso) o en caliente con un presupuesto de
ediciones.

Tres decisiones de fidelidad importantes.

**El plan inicial no lo escribe el oráculo.** Se construye con A\\* sobre la creencia
actual, de forma determinista. El oráculo ruidoso interviene solo en las *reparaciones*.
Es lo habitual en un motor de ejecución agéntica: el programa inicial lo escribe una
persona, y el LLM solo interviene reescribiendo el plan cuando deja de servir.

**La regla de costo es la misma para todo planificador.** Los planes de rutina —el
inicial y el que sigue a una entrega sin que nada haya fallado— son A\\* determinista y
gratuitos: equivalen al programa que se le entrega de antemano al agente. Toda
replanificación de *reparación*, en cambio, pasa por el mismo replanificador (el oráculo,
con competencia ``p``) y cuesta ``c`` ticks de deliberación, la dispare un **fallo del
plan** (llegar a la celda y no encontrar el recurso, o un plan que ya no puede
ejecutarse) o una **divergencia detectada** por el monitoreo. Las políticas que planifican
difieren por tanto solo en *cuándo* invocan al replanificador —``OPEN_LOOP`` al fallar,
``CLOSED_LOOP`` y ``GOVERNED`` al detectar la divergencia— y no en si lo pagan. Sin esta
regla el lazo abierto replanificaría gratis y con competencia perfecta tras cada fallo, y
el experimento compararía una reparación pagada contra una gratuita en vez de dos
criterios sobre cuándo reparar (``info/02-design.md`` §3.2).

**La tarea encadena varios objetivos.** El agente debe reunir ``capacidad`` recursos
antes de entregar. Sin eso, la comparación central del trabajo se vacía: mientras el
agente lleva un único recurso su plan es "volver a la base", la base no se mueve, no hay
divergencia posible, y el reinicio en frío nunca llega a perder nada. Es el trabajo en
vuelo lo que hace caro reiniciar, y hace falta que exista.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from mesa.discrete_space import CellAgent
from project.book import Book, EditRejected, Line, LineOp, goto_lines
from project.deliberation import Deliberation
from project.oracle import RepairRequest
from project.planner import astar, manhattan

LINEAS_PARA_NO_SER_DESPERDICIO = 2
"""Líneas que hay que ejecutar tras una edición para que no cuente como desperdiciada."""


class Policy(StrEnum):
    """Arquitecturas de agente comparadas en el experimento."""

    REFLEX = "REFLEX"
    """Reflejo simple: avidez hacia lo visible, sin plan ni memoria (R&N §2.4.2)."""

    MODEL_BASED = "MODEL_BASED"
    """Reflejo basado en modelo: mantiene creencias, sigue sin plan (R&N §2.4.3)."""

    OPEN_LOOP = "OPEN_LOOP"
    """Basado en objetivos, lazo abierto: ejecuta el plan sin monitorearlo y solo
    replanifica —pagando la deliberación— cuando el plan falla."""

    COLD_RESTART = "COLD_RESTART"
    """Reinicio en frío: al divergir, la edición aplica en la ejecución siguiente y el
    trabajo en curso se pierde."""

    CLOSED_LOOP = "CLOSED_LOOP"
    """Reparación en caliente: repara el plan en sitio pagando la deliberación."""

    GOVERNED = "GOVERNED"
    """Reparación en caliente con presupuesto ``B`` de ediciones. Es lo único que la
    distingue de ``CLOSED_LOOP``."""

    @property
    def planifica(self) -> bool:
        """True si la política construye y ejecuta un plan explícito."""
        return self not in (Policy.REFLEX, Policy.MODEL_BASED)

    @property
    def replanifica(self) -> bool:
        """True si la política reacciona a las divergencias replanificando.

        Es la replanificación *proactiva*, disparada por el monitoreo. La replanificación
        forzada por un fallo del plan la hacen todas las políticas que planifican.
        """
        return self in (Policy.COLD_RESTART, Policy.CLOSED_LOOP, Policy.GOVERNED)


class Resource(CellAgent):
    """Un recurso que deriva por la retícula.

    Su movimiento es la fuente de dinamismo del entorno: con probabilidad ``λ`` por tick
    se desplaza a una celda vecina transitable, invalidando los planes que lo tuvieran
    como objetivo.
    """

    def __init__(self, model: Any, cell: Any, rid: str) -> None:
        """Crear un recurso en una celda."""
        super().__init__(model)
        self.rid = rid
        self.cell = cell

    def step(self) -> None:
        """Derivar a una celda vecina con probabilidad ``λ``."""
        if self.random.random() >= self.model.lambda_dinamismo:
            return
        opciones = [c for c in self.cell.connections.values() if not c.obstaculo]
        if opciones:
            self.cell = self.random.choice(opciones)


class Collector(CellAgent):
    """El agente que ejecuta —y según su política, reescribe— un plan.

    Todas las políticas comparten el mismo cuerpo; lo que cambia es cómo reaccionan a
    una divergencia entre el plan y el mundo.
    """

    def __init__(self, model: Any, policy: Policy) -> None:
        """Crear el recolector en la base del modelo."""
        super().__init__(model)
        self.policy = policy
        self.cell = model.base

        self.book = Book()
        self.belief: dict[str, Any] = {}
        self.target: str | None = None
        self.carrying: list[str] = []
        self.deliberation: Deliberation | None = None
        # El presupuesto de ediciones es la gobernanza, y la gobernanza es lo que
        # distingue a GOVERNED de CLOSED_LOOP (info/02-design.md §3 y §5: «B —
        # ediciones permitidas, solo GOVERNED»). Leerlo para toda política haría
        # que el barrido `gobernanza` comparase una política contra sí misma. Acota solo
        # las reparaciones proactivas: las forzadas por un fallo no se pueden evitar.
        self.presupuesto: int | None = (
            model.presupuesto if policy is Policy.GOVERNED else None
        )

        self.entregas = 0
        self.pasos_utiles = 0
        self.pasos_deliberando = 0
        self.n_ediciones = 0
        self.n_ediciones_desperdiciadas = 0
        self.n_ediciones_por_fallo = 0
        self.tareas_fallidas = 0
        self.carga_perdida = 0

        self._lineas_desde_edicion = 0
        self._divergente = False
        self._fallo_pendiente = False

    @property
    def lleno(self) -> bool:
        """True si ya no cabe otro recurso."""
        return len(self.carrying) >= self.model.capacidad

    # ---------------------------------------------------------------- percepción

    def _vision(self) -> list[Any]:
        """Celdas dentro del radio de observación.

        Un radio ``None`` significa observabilidad total, que es el caso de control del
        experimento. Un radio finito modela la **observabilidad parcial**: hay partes del
        mundo que el agente no tiene en su contexto y simplemente no ve.
        """
        radio = self.model.radio
        if radio is None:
            return self.model.grid.all_cells.cells
        return [
            self.cell,
            *self.cell.get_neighborhood(radius=radio, include_center=False),
        ]

    def observar(self) -> None:
        """Actualizar creencias con lo que se ve y detectar divergencias.

        Hay dos formas de descubrir que el plan dejó de servir, y son los dos primeros
        niveles de monitoreo de R&N §11.5.3:

        - **se ve el objetivo en otro sitio**: la creencia se corrige, y esa corrección
          invalida la ruta que el plan tenía trazada;
        - **se ve vacía la celda donde se creía que estaba**: la creencia era falsa y se
          descarta.

        Que la primera cuente es esencial. Corregir la creencia en silencio dejaría el
        plan apuntando a la celda vieja, el agente caminaría hasta allí y solo
        descubriría el problema al intentar recoger — es decir, toda política se
        comportaría como lazo abierto y el experimento no mediría nada.

        Si el agente no ve ninguna de las dos cosas, sigue creyendo lo que creía: eso es
        lo que mide la métrica de ceguera.
        """
        visibles = self._vision()
        vistos: dict[str, Any] = {}
        for cell in visibles:
            for agent in cell.agents:
                if isinstance(agent, Resource):
                    vistos[agent.rid] = cell

        for rid, cell in vistos.items():
            anterior = self.belief.get(rid)
            self.belief[rid] = cell
            if rid == self.target and anterior is not None and anterior is not cell:
                self._marcar_divergencia()

        if self.target is None or self.target in vistos:
            return
        creido = self.belief.get(self.target)
        if creido is not None and creido in visibles:
            self.belief.pop(self.target, None)
            self._marcar_divergencia()

    def _marcar_divergencia(self) -> None:
        """Registrar que el agente notó que su plan dejó de ser válido."""
        self.model.notificar_deteccion()
        self._divergente = True

    # ------------------------------------------------------------------- decisión

    def step(self) -> None:
        """Un tick: percibir, y luego deliberar o actuar. Nunca las dos cosas."""
        self.observar()

        if self.deliberation is not None:
            self._continuar_deliberacion()
            return

        if not self.policy.planifica:
            self._paso_reactivo()
            return

        self._paso_planificado()

    # ------------------------------------------------------- políticas reactivas

    def _paso_reactivo(self) -> None:
        """Avidez pura (REFLEX) o avidez sobre creencias (MODEL_BASED)."""
        if self.lleno:
            self._mover_hacia(self.model.base)
            if self.cell is self.model.base:
                self._entregar()
            return

        objetivo = self._recurso_mas_cercano(
            usar_creencias=self.policy is Policy.MODEL_BASED
        )
        if objetivo is None:
            if self.carrying:
                self._mover_hacia(self.model.base)
                if self.cell is self.model.base:
                    self._entregar()
            else:
                self._deambular()
            return

        rid, cell = objetivo
        if cell is self.cell:
            self._recoger(rid)
        else:
            self._mover_hacia(cell)

    def _conocidos(self, *, usar_creencias: bool) -> dict[str, Any]:
        """Recursos que el agente puede perseguir ahora mismo."""
        visibles = set(self._vision())
        return {
            rid: cell
            for rid, cell in self.belief.items()
            if (usar_creencias or cell in visibles) and rid not in self.carrying
        }

    def _recurso_mas_cercano(self, *, usar_creencias: bool) -> tuple[str, Any] | None:
        """El recurso conocido más cercano, por distancia de Manhattan."""
        fuente = self._conocidos(usar_creencias=usar_creencias)
        if not fuente:
            return None
        return min(fuente.items(), key=lambda kv: self._dist(self.cell, kv[1]))

    def _deambular(self) -> None:
        """Sin nada que perseguir, moverse al azar para descubrir el mundo."""
        opciones = [c for c in self.cell.connections.values() if not c.obstaculo]
        if opciones:
            self.cell = self.random.choice(opciones)
        self.pasos_utiles += 1

    def _mover_hacia(self, destino: Any) -> None:
        """Un paso ávido hacia el destino, con aleatorización de escape.

        La avidez pura es miope: ante un callejón sin salida el agente entra en él
        porque acerca al destino, y luego oscila indefinidamente entre la entrada y el
        fondo. Es el mínimo local clásico del agente reflejo, y sin remedio deja a las
        dos políticas reactivas en cero entregas, con lo que dejan de servir como línea
        base.

        El remedio es el que da Russell & Norvig §2.4.2 para exactamente este caso:
        *"escape from infinite loops is possible if the agent can randomize its
        actions"*. Con probabilidad ``epsilon_reflejo`` el agente ignora la avidez y se
        mueve al azar. Sigue siendo un agente reflejo —no planifica, no busca— pero deja
        de quedarse encerrado.
        """
        opciones = [c for c in self.cell.connections.values() if not c.obstaculo]
        if not opciones:
            return
        if self.random.random() < self.model.epsilon_reflejo:
            self.cell = self.random.choice(opciones)
        else:
            actual = self._dist(self.cell, destino)
            mejores = [c for c in opciones if self._dist(c, destino) < actual]
            self.cell = self.random.choice(mejores or opciones)
        self.pasos_utiles += 1

    # ----------------------------------------------------- políticas con plan

    def _paso_planificado(self) -> None:
        """Ejecutar el plan, reparándolo antes si hace falta.

        Hay dos disparadores de reparación, y los dos pasan por el mismo replanificador
        al mismo precio (ver la regla de costo en el docstring del módulo):

        - un **fallo del plan** en el tick anterior obliga a replanificar a *toda*
          política que planifica, y no consume presupuesto: es inevitable;
        - una **divergencia detectada** dispara la reparación proactiva, solo en las
          políticas que monitorean y mientras les quede presupuesto.

        Con ``c = 0`` la deliberación es instantánea y el agente todavía actúa en el
        mismo tick. Cobrarle un tick por una edición que por definición es gratuita
        falsearía el experimento justo en el punto de control: con deliberación sin
        costo, el lazo cerrado debe poder igualar al abierto.
        """
        if self._fallo_pendiente:
            self._fallo_pendiente = False
            self._iniciar_deliberacion(por_fallo=True)
            if self.deliberation is not None:
                return
        elif self._divergente and self._vigila_divergencias():
            self._iniciar_deliberacion()
            if self.deliberation is not None:
                return

        self._divergente = False

        if self.book.done:
            self._nuevo_plan()
            if self.book.done:
                self._deambular()
                return

        self._ejecutar_linea()

    def _puede_editar(self) -> bool:
        """La gobernanza: con el presupuesto agotado ya no se repara de forma proactiva.

        El presupuesto acota solo las reparaciones disparadas por una divergencia. Las
        forzadas por un fallo se pagan siempre y no lo consumen, así que ``GOVERNED`` con
        el presupuesto agotado se comporta exactamente como ``OPEN_LOOP`` (y con
        ``B = 0`` es idéntica a ella, semilla a semilla).
        """
        return self.presupuesto is None or self.presupuesto > 0

    def _vigila_divergencias(self) -> bool:
        """True si la política repara al detectar una divergencia, ahora mismo."""
        return self.policy.replanifica and self._puede_editar()

    def _actualizar_target(self) -> None:
        """El objetivo es el recurso de la próxima línea ``PICK`` pendiente."""
        for line in self.book.remaining:
            if line.op is LineOp.PICK:
                self.target = line.arg
                return
        self.target = None

    def _nuevo_plan(self) -> None:
        """Construir un plan de rutina desde cero con A\\*, sin intervención del oráculo.

        Corresponde al programa escrito a mano por una persona: el plan inicial es
        determinista, y el replanificador ruidoso solo aparece al repararlo. Por eso es
        gratuito, y por eso solo se usa cuando nada ha fallado —al empezar, tras una
        entrega o cuando no hay plan que seguir—: tras un fallo, el plan nuevo es una
        reparación y se paga (:meth:`_fallar_tarea`).

        El encadenamiento de objetivos es ávido —el más cercano primero— y no resuelve
        el problema del viajante. Es deliberado: el objeto de estudio es la reparación
        del plan, no su optimalidad global, y un encadenamiento ávido es lo que
        escribiría una persona.
        """
        self._divergente = False
        libres = self._conocidos(usar_creencias=True)
        pendientes = self.model.capacidad - len(self.carrying)

        lineas: list[Line] = []
        pos = self.cell
        for _ in range(pendientes):
            if not libres:
                break
            rid, cell = min(libres.items(), key=lambda kv: self._dist(pos, kv[1]))
            del libres[rid]
            ruta = self._ruta(pos, cell)
            if not ruta:
                self.belief.pop(rid, None)
                continue
            lineas.extend(goto_lines(ruta))
            lineas.append(Line(LineOp.PICK, rid))
            pos = cell

        if not lineas and not self.carrying:
            self.target = None
            self.book = Book()
            return

        lineas.extend(goto_lines(self._ruta(pos, self.model.base)))
        lineas.append(Line(LineOp.DELIVER, None, locked=True))
        self.book = Book(lineas)
        self._actualizar_target()

    # ------------------------------------------------------------ deliberación

    def _iniciar_deliberacion(self, *, por_fallo: bool = False) -> None:
        """Consultar al oráculo y quedarse pensando ``c`` ticks.

        Es la única vía de reparación, la dispare un fallo del plan (``por_fallo=True``,
        replanificación forzada) o una divergencia detectada (reparación proactiva). Que
        ambas compartan oráculo, costo y forma de aplicarse es lo que hace justa la
        comparación entre políticas.

        Antes de preguntar hay que decidir *sobre qué* preguntar. Si el objetivo
        desapareció y el agente no lo ve, reparar la ruta hacia él no tiene sentido: no
        está en ninguna parte que el agente conozca. Lo que corresponde es reelegir
        objetivo entre los recursos que sí conoce —monitoreo a nivel de objetivo, en los
        términos de R&N §11.5.3— y pedir la reparación hacia ese.

        La reparación conserva la estructura de la tarea: se parchea la ruta hacia el
        objetivo y se arrastra la continuación —los objetivos pendientes, el regreso y la
        entrega comprometida—. Truncar el plan a un solo objetivo produciría planes
        sistemáticamente peores, y el experimento acabaría midiendo ese defecto en vez de
        la replanificación: con deliberación gratuita el lazo cerrado saldría perdiendo,
        que es justo lo contrario de lo que debe ocurrir (control de sanidad nº 2).

        El resultado se calcula **ahora** y se retiene hasta que la deliberación
        termina: si el mundo se mueve mientras tanto, el plan llegará desactualizado.
        """
        self._divergente = False

        objetivo = self._recurso_mas_cercano(usar_creencias=True)
        if objetivo is None or self.lleno:
            # Nada conocido que perseguir, o ya va lleno: no se delibera sobre la nada,
            # y por tanto no se paga. Es un plan de rutina.
            self._plan_sin_objetivo()
            return

        if (
            self.n_ediciones > 0
            and self._lineas_desde_edicion < LINEAS_PARA_NO_SER_DESPERDICIO
        ):
            # Se pide una edición nueva cuando la anterior apenas se ejecutó: aquella se
            # pagó y no compró nada. Es la forma operacional del thrashing.
            self.n_ediciones_desperdiciadas += 1

        rid, creido = objetivo
        prop = self.model.oracle.propose(
            RepairRequest(
                book=self.book,
                from_idx=self.book.pc,
                origin=self.cell,
                true_goal=self.model.celda_real_visible(rid, self._vision()),
                believed_goal=creido,
                resource_id=rid,
                tail=tuple(self._cadena_desde(creido, excluir={rid})),
            )
        )
        if not prop.feasible:
            self._plan_sin_objetivo()
            return

        self.deliberation = Deliberation(
            duration=self.model.costo_edicion,
            from_idx=prop.from_idx,
            lines=prop.lines,
            label=str(prop.kind),
            por_fallo=por_fallo,
        )
        if self.deliberation.is_complete:
            self._aplicar_deliberacion()

    def _cadena_desde(self, pos: Any, excluir: set[str]) -> list[Line]:
        """Continuación del plan tras recoger un objetivo: lo que falta, y volver.

        Se encadena de forma ávida desde ``pos``, que es donde el agente *cree* que
        estará tras la recogida. Si el oráculo lo manda a otro sitio, la continuación
        queda algo desalineada — cosa que también le pasa a un replanificador real que
        escribe el resto del plan asumiendo que su propio objetivo era el correcto.

        El ``DELIVER`` final se crea con ``locked=True``, igual que en
        :meth:`_nuevo_plan` y :meth:`_plan_de_regreso`: en toda política que replanifica,
        la entrega comprometida queda fuera del alcance de edición del agente.
        """
        libres = {
            rid: cell
            for rid, cell in self._conocidos(usar_creencias=True).items()
            if rid not in excluir
        }
        faltan = self.model.capacidad - len(self.carrying) - 1
        lineas: list[Line] = []
        for _ in range(max(0, faltan)):
            if not libres:
                break
            rid, cell = min(libres.items(), key=lambda kv: self._dist(pos, kv[1]))
            del libres[rid]
            ruta = self._ruta(pos, cell)
            if not ruta:
                continue
            lineas.extend(goto_lines(ruta))
            lineas.append(Line(LineOp.PICK, rid))
            pos = cell
        lineas.extend(goto_lines(self._ruta(pos, self.model.base)))
        lineas.append(Line(LineOp.DELIVER, None, locked=True))
        return lineas

    def _plan_sin_objetivo(self) -> None:
        """Sin objetivo sobre el cual reparar: volver con la carga, o quedarse sin plan.

        Con carga, el plan es regresar a la base y entregarla. Sin carga, regresar no
        sirve de nada —el ``DELIVER`` final fallaría por falta de carga y contaría como
        una tarea fallida espuria—, así que el plan queda vacío y el agente deambula
        hasta descubrir algún recurso. Ninguno de los dos casos pasa por el oráculo ni
        cuesta deliberación.
        """
        self.book = self._plan_de_regreso() if self.carrying else Book()
        self._actualizar_target()

    def _plan_de_regreso(self) -> Book:
        """Plan para volver a la base con lo que se lleve y entregarlo."""
        lineas = goto_lines(self._ruta(self.cell, self.model.base))
        lineas.append(Line(LineOp.DELIVER, None, locked=True))
        return Book(lineas)

    def _continuar_deliberacion(self) -> None:
        """Consumir un tick de deliberación, o abortarla si algo nuevo la invalida."""
        deliberacion = self.deliberation
        assert deliberacion is not None

        if self._divergente and self._vigila_divergencias():
            # Llega una divergencia nueva antes de terminar de pensar sobre la anterior:
            # los ticks gastados se pierden. Esto es el thrashing. Solo le pasa a quien
            # monitorea: OPEN_LOOP ignora las divergencias también mientras delibera.
            deliberacion.interrupt()
            self.n_ediciones_desperdiciadas += 1
            self.deliberation = None
            self.pasos_deliberando += 1
            self._iniciar_deliberacion(por_fallo=deliberacion.por_fallo)
            return

        self.pasos_deliberando += 1
        deliberacion.tick()
        if deliberacion.is_complete:
            self._aplicar_deliberacion()

    def _aplicar_deliberacion(self) -> None:
        """Instalar el plan reparado, con la semántica de la política.

        La forma de aplicar depende de la política y no del disparador: ``COLD_RESTART``
        aplica en frío también la replanificación forzada por un fallo, y las demás en
        caliente. Toda reparación cuenta en ``n_ediciones`` —es una reescritura del plan—,
        pero solo las proactivas consumen presupuesto; las forzadas por un fallo se
        cuentan además aparte, en ``n_ediciones_por_fallo``.
        """
        deliberacion = self.deliberation
        assert deliberacion is not None
        self.deliberation = None

        if self.policy is Policy.COLD_RESTART:
            self._aplicar_en_frio(deliberacion.lines)
        else:
            self._aplicar_en_caliente(deliberacion)

        if deliberacion.por_fallo:
            self.n_ediciones_por_fallo += 1
        elif self.presupuesto is not None:
            self.presupuesto -= 1
        self.n_ediciones += 1
        self._lineas_desde_edicion = 0
        self._actualizar_target()

    def _aplicar_en_caliente(self, deliberacion: Deliberation) -> None:
        """En caliente: parchear el sufijo del plan en curso, conservando el progreso."""
        try:
            self.book.replace_suffix(deliberacion.from_idx, deliberacion.lines)
        except EditRejected:
            # La edición viola una invariante del plan (toca líneas ya ejecutadas o
            # fuera del alcance de edición) y se rechaza entera: el plan queda como
            # estaba, nunca a medias, y la edición se cuenta como desperdiciada.
            self.n_ediciones_desperdiciadas += 1

    def _aplicar_en_frio(self, lines: list[Line]) -> None:
        """En frío: se aborta la ejecución y se pierde el trabajo en curso.

        Modela a los sistemas que aplican ediciones en la ejecución siguiente: la edición
        solo tiene efecto al reiniciar y todo lo hecho en la ejecución actual se
        descarta. Aquí eso significa soltar la carga acumulada y arrancar con el plan
        nuevo desde cero. La diferencia de rendimiento contra ``CLOSED_LOOP`` es el valor
        cuantificado de reparar en caliente en lugar de reiniciar en frío.
        """
        for rid in self.carrying:
            self.model.soltar_recurso(rid, self.cell)
            self.carga_perdida += 1
        self.carrying = []
        self.book = Book(list(lines))

    # -------------------------------------------------------------- ejecución

    def _ejecutar_linea(self) -> None:
        """Ejecutar exactamente una línea del plan. Un tick, una acción."""
        line = self.book.current
        if line is None:
            return

        match line.op:
            case LineOp.GOTO:
                self._ir_a(line.arg)
            case LineOp.PICK:
                if not self._recoger(line.arg):
                    self._fallar_tarea()
                    return
            case LineOp.DELIVER:
                if not self._entregar():
                    self._fallar_tarea()
                    return
            case LineOp.SCAN:
                self.pasos_utiles += 1

        self.book.advance()
        self._lineas_desde_edicion += 1
        self._actualizar_target()

    def _ir_a(self, coord: tuple[int, ...]) -> None:
        """Avanzar a una celda contigua del plan."""
        destino = self.model.grid[coord]
        if destino in self.cell.connections.values() and not destino.obstaculo:
            self.cell = destino
        self.pasos_utiles += 1

    def _recoger(self, rid: str) -> bool:
        """Recoger el recurso si de verdad está aquí y queda sitio."""
        if self.lleno:
            return False
        recurso = self.model.recurso_en(self.cell, rid)
        if recurso is None:
            return False
        self.carrying.append(rid)
        self.belief.pop(rid, None)
        self.model.retirar_recurso(recurso)
        self.pasos_utiles += 1
        return True

    def _entregar(self) -> bool:
        """Depositar la carga en la base."""
        if not self.carrying or self.cell is not self.model.base:
            return False
        self.entregas += len(self.carrying)
        for _ in self.carrying:
            self.model.reponer_recurso()
        self.carrying = []
        self.pasos_utiles += 1
        return True

    def _fallar_tarea(self) -> None:
        """El plan dejó de ser ejecutable: queda pendiente una replanificación forzada.

        Le pasa sobre todo a ``OPEN_LOOP``, que ignora las divergencias y solo descubre
        el problema cuando intenta recoger algo que ya no está (monitoreo a nivel de
        acción, R&N §11.5.3). Ese descubrimiento tardío es precisamente su desventaja.

        El tick del fallo ya se gastó en la acción fallida. En el tick siguiente
        :meth:`_paso_planificado` repara el plan por la vía de siempre —oráculo con
        competencia ``p``, ``c`` ticks de deliberación— y sin tocar el presupuesto. Antes
        el plan se vaciaba y se reconstruía gratis y con A\\* exacto, lo que regalaba al
        lazo abierto una replanificación perfecta y sin costo tras cada fallo.

        El plan se conserva con el contador sobre la línea que falló: la reparación
        reescribe el sufijo desde ahí, conserva la carga que ya se lleva (salvo en
        ``COLD_RESTART``, que la suelta como en toda reparación suya) y reproduce
        intacto el ``DELIVER`` bloqueado. La creencia sobre el objetivo se descarta,
        porque se acaba de comprobar que es falsa.
        """
        self.tareas_fallidas += 1
        if self.target is not None:
            self.belief.pop(self.target, None)
        self.target = None
        self._fallo_pendiente = True

    # ------------------------------------------------------------------ utilidades

    def _dist(self, a: Any, b: Any) -> int:
        """Distancia de Manhattan entre dos celdas."""
        return manhattan(
            a.coordinate,
            b.coordinate,
            dimensions=self.model.dimensions,
            torus=self.model.torus,
        )

    def _ruta(self, origen: Any, destino: Any) -> list[Any]:
        """Ruta óptima entre dos celdas, esquivando obstáculos."""
        return astar(
            origen,
            destino,
            passable=self.model.passable,
            dimensions=self.model.dimensions,
            torus=self.model.torus,
        ).path
