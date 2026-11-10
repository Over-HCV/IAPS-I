"""La base de conocimiento del agente ``KNOWLEDGE_BASED`` (``docs/roadmap-c4b.md``, KB-2).

Se separan los dos niveles de Newell (1982), y la equivalencia entre ambos se comprueba
con una prueba (``tests/test_conocimiento.py``, contra DPLL de :mod:`project.logica`), no
se supone.

**Nivel de conocimiento: qué sabe el agente.**

- *Percepción como fluentes.* Cada tick se hace ``TELL(Visto(r,c,t))`` por cada recurso a
  la vista y ``TELL(¬En(r,c,t))`` por cada celda a la vista que no lo contiene (``Vacía``
  cuando no contiene a ninguno). Recoger un recurso es ``TELL(Recogido(r,t))``.
- *Axioma de deriva.* Como ``Resource.step`` mueve el recurso a lo sumo a una vecina no
  obstáculo por tick, :math:`En(r,c,t) \\Rightarrow \\bigvee_{c' \\in N^+(c)}
  En(r,c',t+1)`, con :math:`N^+(c)` la propia celda y sus vecinas transitables. Con λ=0
  el axioma se instancia como «los recursos no se mueven»: es lo único que el agente sabe
  de λ.
- *Monotonía.* Ninguna observación se retira: lo que caduca es la conclusión «está ahí
  ahora», que ya no se afirma sino que se deriva.

**Nivel de implementación: operaciones de conjuntos.** La región posible
:math:`R(r,t)` (lo que DPLL no puede descartar) se mantiene de forma incremental: al ver
``r`` en ``c`` se fija :math:`R=\\{c\\}`, y en cada observación sin verlo se expande un
paso por cada deriva ocurrida (:math:`R \\cup N(R)`) y se le restan las celdas a la vista.
Es la estimación de estado de R&N §4.4 escrita como axiomas de estado sucesor (§7.7). La
poda tiene que hacerse tick a tick: restar a la bola *todas* las celdas vistas vacías desde
la última observación no es sólido, porque el recurso pudo entrar en una de ellas después de
que se viera vacía.

La distancia que importa es la **geodésica** (BFS sobre celdas transitables), no la de
Manhattan, que sobreestima la región junto a los obstáculos: seguiría siendo sólida, pero
floja.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any, Literal

Horizonte = Literal["ahora", "llegada"]
"""Cuándo debe seguir siendo posible el plan: en el tick actual o al llegar al ``PICK``."""

HORIZONTES: tuple[str, ...] = ("ahora", "llegada")


class Vecindario:
    """Vecinas transitables de cada celda, calculadas una sola vez.

    Son exactamente las opciones de ``Resource.step`` (``cell.connections`` sin
    obstáculos), de modo que el axioma de deriva del agente coincide con la ley del mundo.
    """

    def __init__(self) -> None:
        """Un vecindario vacío; se llena a medida que se consulta."""
        self._cache: dict[Any, tuple[Any, ...]] = {}

    def __call__(self, cell: Any) -> tuple[Any, ...]:
        """Vecinas transitables de ``cell`` (sin incluirla)."""
        vec = self._cache.get(cell)
        if vec is None:
            vec = tuple(c for c in cell.connections.values() if not c.obstaculo)
            self._cache[cell] = vec
        return vec


def expandir(
    region: Iterable[Any], k: int, vecinas: Callable[[Any], Iterable[Any]]
) -> set[Any]:
    """Expansión de ``k`` pasos sin poda: todo lo alcanzable en ``k`` derivas.

    Es la bola geodésica de radio ``k`` alrededor de la región, que en el horizonte
    ``"llegada"`` responde «¿puede estar el recurso en esta celda cuando llegue?».
    """
    actual = set(region)
    frontera = set(actual)
    for _ in range(k):
        nueva = {v for c in frontera for v in vecinas(c) if v not in actual}
        if not nueva:
            break
        actual |= nueva
        frontera = nueva
    return actual


class RegionPosible:
    """La región posible :math:`R(r,t)` de un recurso: dónde **puede** estar ahora.

    Se guarda junto con un *borde* (las celdas de la región que pueden tener vecinas
    fuera de ella), de forma que expandir cuesta lo que mide el borde y no lo que mide la
    región: una región saturada, con solo el disco de visión recortado, se expande en unas
    decenas de operaciones.

    Attributes:
        celdas: las celdas posibles.
    """

    __slots__ = ("_borde", "_extremos", "_vecinas", "celdas")

    def __init__(self, cell: Any, vecinas: Callable[[Any], Iterable[Any]]) -> None:
        """La región de un recurso recién visto en ``cell``: un punto."""
        self._vecinas = vecinas
        self.celdas: set[Any] = {cell}
        self._borde: set[Any] = {cell}
        self._extremos: tuple[int, int, int, int] | None = None

    def __contains__(self, cell: Any) -> bool:
        """Si el recurso puede estar en ``cell``."""
        return cell in self.celdas

    def __len__(self) -> int:
        """Número de celdas posibles."""
        return len(self.celdas)

    def avistar(self, cell: Any) -> None:
        """``TELL(Visto(r,c,t))``: la región colapsa a la celda observada."""
        self.celdas = {cell}
        self._borde = {cell}
        self._extremos = None

    def avanzar(self, pasos: int, vistas: set[Any] | frozenset[Any]) -> None:
        """Una observación sin ver el recurso, tras ``pasos`` derivas del mundo.

        Primero el axioma de deriva (``pasos`` expansiones, sin poda entre ellas porque no
        hubo observación intermedia) y luego ``TELL(¬En(r,c,t))`` para cada celda a la
        vista, que el recurso no ocupa porque no se le ve.
        """
        for _ in range(pasos):
            nuevas = {
                v for c in self._borde for v in self._vecinas(c) if v not in self.celdas
            }
            if not nuevas:
                self._borde = set()
                break
            self.celdas |= nuevas
            # Las vecinas del borde viejo ya están todas dentro: solo lo recién añadido
            # puede tener vecinas fuera.
            self._borde = nuevas
            self._extremos = None

        quitadas = [c for c in vistas if c in self.celdas]
        if not quitadas:
            return
        self.celdas.difference_update(quitadas)
        self._borde.difference_update(quitadas)
        # Junto a un hueco recién abierto vuelve a haber borde: el recurso puede entrar ahí.
        for c in quitadas:
            self._borde.update(v for v in self._vecinas(c) if v in self.celdas)
        self._extremos = None

    def peor_caso(self, coord: tuple[int, ...]) -> int:
        """:math:`\\max_{x \\in R} d(\\text{coord}, x)` con distancia de Manhattan.

        Se calcula sin recorrer la región: en dos dimensiones,
        :math:`|dx|+|dy| = \\max(\\pm(x - p_x) \\pm (y - p_y))`, así que basta guardar los
        extremos de :math:`x+y` y de :math:`x-y`. Vale solo para la retícula no toroidal;
        con toro, :meth:`peor_caso_con` recorre la región con la distancia que se le dé.
        """
        if self._extremos is None:
            sumas = [c.coordinate[0] + c.coordinate[1] for c in self.celdas]
            difs = [c.coordinate[0] - c.coordinate[1] for c in self.celdas]
            self._extremos = (max(sumas), min(sumas), max(difs), min(difs))
        s_max, s_min, d_max, d_min = self._extremos
        s, d = coord[0] + coord[1], coord[0] - coord[1]
        return max(s_max - s, s - s_min, d_max - d, d - d_min)

    def peor_caso_con(self, origen: Any, dist: Callable[[Any, Any], int]) -> int:
        """El peor caso por fuerza bruta, con cualquier distancia entre celdas."""
        return max(dist(origen, x) for x in self.celdas)


class BaseConocimiento:
    """La KB de ``KNOWLEDGE_BASED``: avistamientos fechados y una región por recurso.

    Responde las tres preguntas ``ASK`` de KB-2:

    1. **¿Dónde puede estar r ahora?** :meth:`posible` y :attr:`regiones`.
    2. **¿Qué recurso tengo asegurado?** :meth:`clave`, el peor caso sobre la región.
    3. **¿Sigue siendo ejecutable mi plan?** :meth:`plan_valido`, con horizonte
       ``"ahora"`` o ``"llegada"``.

    Attributes:
        dinamico: si el agente sabe que los recursos se mueven (λ>0). Es lo único que sabe
            de λ; con ``False`` las regiones nunca se expanden.
        regiones: región posible de cada recurso rastreado.
        avistamientos: el ``Visto(r,c,t)`` más reciente de cada recurso, con su tick.
        recogidos: ``Recogido(r,t)``: recursos que salieron del mundo, con su tick.
    """

    def __init__(
        self,
        *,
        dinamico: bool,
        vecinas: Callable[[Any], Iterable[Any]] | None = None,
        torus: bool = False,
        dist: Callable[[Any, Any], int] | None = None,
    ) -> None:
        """Una KB sin observaciones.

        Args:
            dinamico: si el mundo es dinámico (λ>0).
            vecinas: vecinas transitables de una celda; por defecto un :class:`Vecindario`.
            torus: si la retícula da la vuelta (el peor caso se calcula entonces con
                ``dist`` por fuerza bruta).
            dist: distancia entre celdas, obligatoria con ``torus``.
        """
        self.dinamico = dinamico
        self.vecinas = vecinas or Vecindario()
        self.torus = torus
        self.dist = dist
        if torus and dist is None:
            raise ValueError("torus=True requiere 'dist'")
        self.regiones: dict[str, RegionPosible] = {}
        self.avistamientos: dict[str, tuple[Any, int]] = {}
        self.recogidos: dict[str, int] = {}
        self._derivas: int | None = None

    # ------------------------------------------------------------------ TELL

    def percibir(
        self,
        vistos: Mapping[str, Any],
        visibles: Iterable[Any],
        *,
        derivas: int,
        t: int,
    ) -> None:
        """Incorporar una observación.

        Args:
            vistos: recurso → celda, para cada recurso a la vista.
            visibles: celdas a la vista.
            derivas: contador de derivas del mundo (``OASysWorld.derivas``). La
                diferencia con el de la observación anterior es cuántas veces pudo moverse
                cada recurso entretanto: una con el orden de activación fijo, y 0, 1 o 2
                con el orden sorteado.
            t: tick de la observación, para fechar los avistamientos.
        """
        pasos = 0 if self._derivas is None else derivas - self._derivas
        self._derivas = derivas
        if not self.dinamico:
            pasos = 0
        vistas = visibles if isinstance(visibles, set | frozenset) else set(visibles)
        for rid, region in self.regiones.items():
            if rid not in vistos:
                region.avanzar(pasos, vistas)
        for rid, cell in vistos.items():
            region = self.regiones.get(rid)
            if region is None:
                self.regiones[rid] = RegionPosible(cell, self.vecinas)
            else:
                region.avistar(cell)
            self.avistamientos[rid] = (cell, t)

    def recoger(self, rid: str, t: int) -> None:
        """``TELL(Recogido(r,t))``: el recurso deja el mundo y deja de rastrearse."""
        self.regiones.pop(rid, None)
        self.recogidos[rid] = t

    # ------------------------------------------------------------------- ASK

    def posible(self, rid: str, cell: Any) -> bool:
        """Pregunta 1: ¿puede estar ``rid`` en ``cell`` ahora?"""
        region = self.regiones.get(rid)
        return region is not None and cell in region

    def clave(self, rid: str, origen: Any) -> float:
        """Pregunta 2: el peor caso, :math:`\\max_{x \\in R(r,t)} d(\\text{origen}, x)`.

        Una creencia vieja, cuya región ya es ancha, pierde así frente a una observación
        reciente algo más lejana.
        """
        region = self.regiones[rid]
        if self.torus:
            assert self.dist is not None
            return region.peor_caso_con(origen, self.dist)
        return region.peor_caso(origen.coordinate)

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
        """Pregunta 3: ¿sigue siendo ejecutable el plan? Solo *inválido* lo repara.

        - ``"ahora"``: inválido si la celda que el agente creía del objetivo
          (``refutada``, la que el monitoreo acaba de contradecir) ya no está en
          :math:`R(r,t)`. Es, a nivel de conocimiento, el monitor de ``CLOSED_LOOP``.
        - ``"llegada"``: inválido solo si la celda del ``PICK`` cae fuera de la expansión
          de ``k`` pasos de :math:`R(r,t)`, con ``k`` las líneas ``GOTO`` que faltan: el
          recurso ya no puede estar ahí cuando el agente llegue. Lo que no se puede
          descartar (*desconocido*) mantiene el plan.

        ``costo`` no se usa: la lógica no pondera, solo descarta.
        """
        region = self.regiones.get(rid)
        if region is None:
            return False
        if horizonte == "ahora":
            return refutada is not None and refutada in region
        if not self.dinamico or k == 0:
            return celda_pick in region
        # P ∈ expandir(R, k)  ⇔  la bola de radio k alrededor de P toca R (vecindad
        # simétrica), y la bola de un punto es mucho más barata que la de la región.
        return not region.celdas.isdisjoint(expandir([celda_pick], k, self.vecinas))
