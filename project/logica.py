"""Motor de inferencia proposicional (``docs/roadmap-c4b.md``, KB-1).

Es el motor de la sesión de agentes basados en conocimiento
(``content/presentation/IA_C4B.ipynb``) portado como módulo puro: no importa Mesa ni nada
del modelo. Su papel en el proyecto es servir de **nivel de conocimiento** contra el que
se comprueba la implementación por conjuntos de :mod:`project.conocimiento` (Newell,
1982): en retículas pequeñas, las observaciones y el axioma de deriva se codifican aquí
como oraciones, y DPLL debe responder ``falso`` exactamente fuera de la región posible.

Representación (la misma de la sesión):

- un **símbolo** es una cadena, p. ej. ``"En_r0_2_3_t1"``;
- una **oración compuesta** es una tupla ``("not", a)``, ``("and", a, b, ...)``,
  ``("or", a, b, ...)``, ``("implies", a, b)`` o ``("iff", a, b)``;
- un **literal** es ``"p"`` o ``"~p"``, y una **cláusula** un ``frozenset`` de literales.

Referencias: Russell & Norvig (2020) §7.4 (semántica y enumeración), §7.5 (CNF y
resolución) y §7.6 (DPLL); Davis, Logemann y Loveland (1962).
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from itertools import combinations, product
from typing import Literal

# Un símbolo (``str``) o una tupla ``(operador, *argumentos)``.
type Oracion = str | tuple
type Clausula = frozenset[str]
type Modelo = dict[str, bool]
type Estado = Literal["verdadero", "falso", "desconocido"]


# ------------------------------------------------------------------ constructores


def Not(a: Oracion) -> Oracion:  # noqa: N802 - nombres de la sesión
    """¬a."""
    return ("not", a)


def And(*args: Oracion) -> Oracion:  # noqa: N802
    """a ∧ b ∧ …  (sin argumentos es la oración verdadera)."""
    return ("and", *args)


def Or(*args: Oracion) -> Oracion:  # noqa: N802
    """a ∨ b ∨ …  (sin argumentos es la oración falsa)."""
    return ("or", *args)


def Implies(a: Oracion, b: Oracion) -> Oracion:  # noqa: N802
    """a ⇒ b."""
    return ("implies", a, b)


def Iff(a: Oracion, b: Oracion) -> Oracion:  # noqa: N802
    """a ⇔ b."""
    return ("iff", a, b)


# ------------------------------------------------------------------ semántica


def symbols_of(s: Oracion) -> set[str]:
    """Símbolos proposicionales que aparecen en ``s``."""
    if isinstance(s, str):
        return {s}
    return set().union(*(symbols_of(arg) for arg in s[1:]))


def pl_true(s: Oracion, model: Modelo) -> bool:
    """Valor de verdad de ``s`` en un modelo completo (R&N §7.4.1)."""
    if isinstance(s, str):
        return model[s]
    op, *args = s
    vals = [pl_true(a, model) for a in args]
    match op:
        case "not":
            return not vals[0]
        case "and":
            return all(vals)
        case "or":
            return any(vals)
        case "implies":
            return (not vals[0]) or vals[1]
        case "iff":
            return vals[0] == vals[1]
    raise ValueError(f"operador desconocido: {op}")


def models_of(s: Oracion) -> Iterator[Modelo]:
    """Los modelos de ``s`` sobre sus propios símbolos: M(s)."""
    syms = sorted(symbols_of(s))
    for values in product([True, False], repeat=len(syms)):
        model = dict(zip(syms, values, strict=True))
        if pl_true(s, model):
            yield model


def tt_entails(kb: Oracion, alpha: Oracion) -> bool:
    """KB ⊨ α por enumeración de modelos: M(KB) ⊆ M(α) (R&N §7.4.4, TT-ENTAILS)."""
    syms = sorted(symbols_of(kb) | symbols_of(alpha))
    for values in product([True, False], repeat=len(syms)):
        model = dict(zip(syms, values, strict=True))
        if pl_true(kb, model) and not pl_true(alpha, model):
            return False
    return True


# ------------------------------------------------------------------------- CNF


def lit_symbol(lit: str) -> str:
    """Símbolo de un literal."""
    return lit[1:] if lit[0] == "~" else lit


def lit_positive(lit: str) -> bool:
    """True si el literal es positivo."""
    return lit[0] != "~"


def neg_lit(lit: str) -> str:
    """Literal complementario."""
    return lit[1:] if lit[0] == "~" else "~" + lit


def eliminate_implications(s: Oracion) -> Oracion:
    """a ⇒ b ≡ ¬a ∨ b;  a ⇔ b ≡ (¬a ∨ b) ∧ (¬b ∨ a)."""
    if isinstance(s, str):
        return s
    op, *args = s
    args = [eliminate_implications(a) for a in args]
    if op == "implies":
        a, b = args
        return ("or", ("not", a), b)
    if op == "iff":
        a, b = args
        return ("and", ("or", ("not", a), b), ("or", ("not", b), a))
    return (op, *args)


def push_negations(s: Oracion, negate: bool = False) -> Oracion:
    """De Morgan: deja las negaciones solo delante de los símbolos."""
    if isinstance(s, str):
        return ("not", s) if negate else s
    op, *args = s
    if op == "not":
        return push_negations(args[0], not negate)
    if negate:
        op = "or" if op == "and" else "and"
    return (op, *[push_negations(a, negate) for a in args])


def cnf_clauses(s: Oracion) -> list[Clausula]:
    """Oración sin ⇒/⇔ y con negaciones internas → lista de cláusulas (distribución)."""
    if isinstance(s, str):
        return [frozenset([s])]
    op, *args = s
    if op == "not":
        return [frozenset(["~" + args[0]])]
    if op == "and":
        return [c for a in args for c in cnf_clauses(a)]
    if op == "or":
        result: list[Clausula] = [frozenset()]
        for a in args:
            result = [r | c for r in result for c in cnf_clauses(a)]
        return result
    raise ValueError(f"operador desconocido tras normalizar: {op}")


def to_clauses(sentence: Oracion) -> list[Clausula]:
    """Cualquier oración → CNF como lista de cláusulas, sin tautologías (R&N §7.5.2)."""
    clauses = cnf_clauses(push_negations(eliminate_implications(sentence)))
    return [c for c in clauses if not any(neg_lit(lit) in c for lit in c)]


# ------------------------------------------------------------------------ DPLL


def dpll(clauses: Iterable[Iterable[str]], model: Modelo | None = None) -> Modelo | None:
    """Un modelo que satisface todas las cláusulas, o ``None`` (R&N §7.6.1).

    Propagación de unidades hasta el punto fijo y luego ramificación con retroceso sobre
    el primer símbolo libre. Es la versión de la sesión, sin la heurística de símbolo
    puro, que no cambia la respuesta sino solo el tiempo.
    """
    model = dict(model or {})
    pending: list[list[str]] = [list(c) for c in clauses]
    while True:
        nuevas: list[list[str]] = []
        units: dict[str, bool] = {}
        for clause in pending:
            satisfied, remaining = False, []
            for lit in clause:
                sym = lit_symbol(lit)
                if sym in model:
                    if model[sym] == lit_positive(lit):
                        satisfied = True
                        break
                else:
                    remaining.append(lit)
            if satisfied:
                continue
            if not remaining:
                return None
            nuevas.append(remaining)
            if len(remaining) == 1:
                sym, val = lit_symbol(remaining[0]), lit_positive(remaining[0])
                if units.get(sym, val) != val:
                    return None
                units[sym] = val
        pending = nuevas
        if not pending:
            return model
        if not units:
            break
        model.update(units)
    sym = lit_symbol(pending[0][0])
    for value in (True, False):
        result = dpll(pending, {**model, sym: value})
        if result is not None:
            return result
    return None


# --------------------------------------------------------- base de conocimiento


class KnowledgeBase:
    """Base de conocimiento proposicional con ``TELL`` y ``ASK`` (R&N §7.1, KB-AGENT).

    Se guarda como conjunto de cláusulas, y ``ASK`` decide por refutación: KB ⊨ α si y
    solo si KB ∧ ¬α es insatisfacible.
    """

    def __init__(self) -> None:
        """Una KB vacía."""
        self.clauses: set[Clausula] = set()
        self.n_ask = 0

    def tell(self, sentence: Oracion) -> None:
        """TELL: añadir una oración."""
        self.clauses.update(to_clauses(sentence))

    def ask(self, query: Oracion) -> bool:
        """ASK: ¿KB ⊨ query?"""
        self.n_ask += 1
        return dpll([*self.clauses, *to_clauses(Not(query))]) is None

    def ask_status(self, query: Oracion) -> Estado:
        """Las tres respuestas: ``verdadero``, ``falso`` o ``desconocido``."""
        if self.ask(query):
            return "verdadero"
        if self.ask(Not(query)):
            return "falso"
        return "desconocido"


# ------------------------------------------------------------- cardinalidad


def exactly(k: int, simbolos: Sequence[str]) -> Oracion:
    """«Exactamente ``k`` de los símbolos son verdaderos», ya en forma de cláusulas.

    A lo sumo ``k``: toda combinación de ``k+1`` tiene alguno falso. Al menos ``k``: toda
    combinación de ``n-k+1`` tiene alguno verdadero. En total son
    :math:`\\binom{n}{k+1} + \\binom{n}{k-1}` cláusulas (la restricción del Buscaminas).
    """
    n = len(simbolos)
    if not 0 <= k <= n:
        raise ValueError(f"k={k} fuera de [0, {n}]")
    clausulas: list[Oracion] = [
        Or(*[Not(s) for s in combo]) for combo in combinations(simbolos, k + 1)
    ]
    clausulas += [Or(*combo) for combo in combinations(simbolos, n - k + 1)]
    return And(*clausulas)
