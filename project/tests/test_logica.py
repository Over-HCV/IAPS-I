"""El motor de inferencia proposicional (``docs/roadmap-c4b.md``, KB-1)."""

from itertools import product
from math import comb
import random
import time

from project.logica import (
    And,
    Iff,
    Implies,
    KnowledgeBase,
    Not,
    Or,
    Oracion,
    dpll,
    exactly,
    lit_positive,
    lit_symbol,
    pl_true,
    symbols_of,
    to_clauses,
    tt_entails,
)
import pytest

SIMBOLOS = ("p", "q", "r", "s")


def _aleatoria(rng: random.Random, prof: int) -> Oracion:
    """Oración aleatoria de profundidad acotada sobre a lo sumo cuatro símbolos."""
    if prof == 0 or rng.random() < 0.3:
        return rng.choice(SIMBOLOS)
    op = rng.choice(("not", "and", "or", "implies", "iff"))
    if op == "not":
        return Not(_aleatoria(rng, prof - 1))
    if op in ("and", "or"):
        args = [_aleatoria(rng, prof - 1) for _ in range(rng.randint(2, 3))]
        return And(*args) if op == "and" else Or(*args)
    a, b = _aleatoria(rng, prof - 1), _aleatoria(rng, prof - 1)
    return Implies(a, b) if op == "implies" else Iff(a, b)


def _satisface(clausulas: list[frozenset[str]], modelo: dict[str, bool]) -> bool:
    """Todas las cláusulas tienen algún literal verdadero en el modelo."""
    return all(
        any(modelo[lit_symbol(lit)] == lit_positive(lit) for lit in c) for c in clausulas
    )


# ------------------------------------------------------------ ejemplo del libro

R1 = Not("P11")
R2 = Iff("B11", Or("P12", "P21"))
R3 = Iff("B21", Or("P11", "P22", "P31"))
R4 = Not("B11")
R5 = "B21"
KB_WUMPUS = And(R1, R2, R3, R4, R5)


def _kb_wumpus() -> KnowledgeBase:
    kb = KnowledgeBase()
    for r in (R1, R2, R3, R4, R5):
        kb.tell(r)
    return kb


def test_wumpus_por_enumeracion() -> None:
    """R&N §7.4.3: KB ⊨ ¬P12 y KB ⊨ P22 ∨ P31, pero P22 no se decide."""
    assert tt_entails(KB_WUMPUS, Not("P12"))
    assert tt_entails(KB_WUMPUS, Or("P22", "P31"))
    assert not tt_entails(KB_WUMPUS, "P22")
    assert not tt_entails(KB_WUMPUS, Not("P22"))


def test_wumpus_por_dpll() -> None:
    """La KB por refutación da las mismas tres respuestas que la enumeración."""
    kb = _kb_wumpus()
    assert kb.ask(Not("P12"))
    assert kb.ask(Or("P22", "P31"))
    assert kb.ask_status("P12") == "falso"
    assert kb.ask_status("P22") == "desconocido"
    assert kb.ask_status(Or("P22", "P31")) == "verdadero"


# --------------------------------------------------------- solidez y completitud


def test_tt_entails_coincide_con_ask() -> None:
    """~100 pares (KB, α) aleatorios: enumeración y DPLL responden lo mismo."""
    rng = random.Random(0)
    distintas = set()
    for _ in range(100):
        kb_s, alpha = _aleatoria(rng, 3), _aleatoria(rng, 3)
        kb = KnowledgeBase()
        kb.tell(kb_s)
        esperado = tt_entails(kb_s, alpha)
        distintas.add(esperado)
        assert kb.ask(alpha) == esperado, (kb_s, alpha)
    assert distintas == {True, False}  # la muestra ejercita ambos casos


def test_cnf_equivale_a_la_oracion() -> None:
    """En los 2^n modelos, la oración y su conjunto de cláusulas tienen el mismo valor."""
    rng = random.Random(0)
    for _ in range(100):
        s = _aleatoria(rng, 4)
        clausulas = to_clauses(s)
        syms = sorted(symbols_of(s))
        for valores in product([True, False], repeat=len(syms)):
            modelo = dict(zip(syms, valores, strict=True))
            assert pl_true(s, modelo) == _satisface(clausulas, modelo), s


# ------------------------------------------------------------------------ DPLL


def test_dpll_detecta_contradiccion() -> None:
    """p ∧ ¬p es insatisfacible."""
    assert dpll(to_clauses(And("p", Not("p")))) is None


def test_dpll_clausula_unitaria_fuerza_valor() -> None:
    """Una cláusula unitaria fija su símbolo, y la propagación sigue la implicación."""
    modelo = dpll([["~p"], ["p", "q"]])
    assert modelo is not None
    assert modelo["p"] is False and modelo["q"] is True


def test_cadena_de_implicaciones_es_rapida() -> None:
    """x0, x0⇒x1, …, x39⇒x40: DPLL lo decide al instante (TT-ENTAILS: 2^41 modelos)."""
    n = 40
    kb = KnowledgeBase()
    kb.tell("x0")
    for i in range(n):
        kb.tell(Implies(f"x{i}", f"x{i + 1}"))
    t0 = time.perf_counter()
    assert kb.ask(f"x{n}")
    assert time.perf_counter() - t0 < 1.0


# ------------------------------------------------------------- cardinalidad


@pytest.mark.parametrize("k,n", [(0, 3), (1, 2), (1, 3), (2, 4), (3, 5), (4, 4), (2, 6)])
def test_exactly_numero_de_clausulas(k: int, n: int) -> None:
    """exactly(k, n) da C(n, k+1) + C(n, k−1) cláusulas, con C(n, −1) = 0."""
    simbolos = [f"s{i}" for i in range(n)]
    esperado = comb(n, k + 1) + (comb(n, k - 1) if k >= 1 else 0)
    assert len(to_clauses(exactly(k, simbolos))) == esperado


def test_exactly_semantica() -> None:
    """En los 2^n modelos, exactly(k, ·) es verdadera sii hay k símbolos verdaderos."""
    simbolos = ["a", "b", "c", "d"]
    for k in range(len(simbolos) + 1):
        s = exactly(k, simbolos)
        for valores in product([True, False], repeat=len(simbolos)):
            modelo = dict(zip(simbolos, valores, strict=True))
            assert pl_true(s, modelo) == (sum(valores) == k)


def test_exactly_cincuenta_cincuenta() -> None:
    """exactly(1, [a, b]) no decide ninguno de los dos (el 50/50 del Buscaminas)."""
    kb = KnowledgeBase()
    kb.tell(exactly(1, ["a", "b"]))
    assert kb.ask_status("a") == "desconocido"
    assert kb.ask_status("b") == "desconocido"


def test_exactly_con_descartes_decide() -> None:
    """exactly(1, [a, b, c]) con ¬a y ¬b obliga a c."""
    kb = KnowledgeBase()
    kb.tell(exactly(1, ["a", "b", "c"]))
    kb.tell(Not("a"))
    kb.tell(Not("b"))
    assert kb.ask_status("c") == "verdadero"


@pytest.mark.parametrize("k", [-1, 3])
def test_exactly_k_fuera_de_rango(k: int) -> None:
    """k fuera de [0, n] es un error."""
    with pytest.raises(ValueError):
        exactly(k, ["a", "b"])


# ----------------------------------------------------------------- contador


def test_n_ask_cuenta_consultas() -> None:
    """Cada ASK incrementa el contador; ask_status puede hacer una o dos."""
    kb = _kb_wumpus()
    assert kb.n_ask == 0
    kb.ask("P12")
    assert kb.n_ask == 1
    kb.ask_status(Not("P12"))  # verdadero: una sola consulta
    assert kb.n_ask == 2
    kb.ask_status("P22")  # desconocido: dos consultas
    assert kb.n_ask == 4
