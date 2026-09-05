"""Invariantes del plan y de la operación de edición.

Verifican que ``Book.replace_suffix`` reproduce la semántica de ``editBook`` en OASys:
una edición se acepta o se rechaza entera, no puede reescribir el pasado, y debe dejar
las líneas bloqueadas intactas (``validate_edit`` en
``backend/src/agent/tools/governance.rs``).
"""

from oasys_abm.book import Book, EditRejected, Line, LineOp, goto_lines
import pytest


def plan_simple() -> Book:
    """Plan de referencia: ir, recoger, entregar (la entrega es un compromiso)."""
    return Book(
        [
            Line(LineOp.GOTO, (1, 0)),
            Line(LineOp.GOTO, (2, 0)),
            Line(LineOp.PICK, "r0"),
            Line(LineOp.DELIVER, None, locked=True),
        ]
    )


def test_contador_avanza_y_termina() -> None:
    book = plan_simple()
    assert book.current == Line(LineOp.GOTO, (1, 0))
    for _ in range(len(book)):
        assert not book.done
        book.advance()
    assert book.done
    assert book.current is None


def test_remaining_excluye_lo_ejecutado() -> None:
    book = plan_simple()
    book.advance()
    book.advance()
    assert book.remaining == book.lines[2:]


def test_edicion_que_preserva_lo_bloqueado_se_acepta() -> None:
    """Reparar la ruta conservando el DELIVER comprometido es legal."""
    book = plan_simple()
    book.advance()
    book.replace_suffix(
        1,
        [
            Line(LineOp.GOTO, (5, 5)),
            Line(LineOp.PICK, "r0"),
            Line(LineOp.DELIVER, None, locked=True),
        ],
    )
    assert [ln.op for ln in book.lines] == [
        LineOp.GOTO,
        LineOp.GOTO,
        LineOp.PICK,
        LineOp.DELIVER,
    ]
    assert book.locked_render() == [Line(LineOp.DELIVER, None, locked=True)]


def test_edicion_que_elimina_lo_bloqueado_se_rechaza() -> None:
    book = plan_simple()
    with pytest.raises(EditRejected, match="bloqueadas"):
        book.replace_suffix(1, [Line(LineOp.SCAN)])


def test_edicion_que_altera_lo_bloqueado_se_rechaza() -> None:
    """Sustituir la línea bloqueada por otra distinta tampoco vale."""
    book = plan_simple()
    with pytest.raises(EditRejected, match="bloqueadas"):
        book.replace_suffix(1, [Line(LineOp.DELIVER, "otro", locked=True)])


def test_edicion_del_pasado_se_rechaza() -> None:
    book = plan_simple()
    book.advance()
    book.advance()
    with pytest.raises(EditRejected, match="ya ejecutadas"):
        book.replace_suffix(0, [Line(LineOp.SCAN)])


def test_edicion_fuera_de_rango_se_rechaza() -> None:
    book = plan_simple()
    with pytest.raises(EditRejected, match="fuera de rango"):
        book.replace_suffix(99, [Line(LineOp.SCAN)])


def test_rechazo_no_deja_el_plan_a_medias() -> None:
    """La atomicidad es la propiedad central: un rechazo no muta nada."""
    book = plan_simple()
    antes = list(book.lines)
    with pytest.raises(EditRejected):
        book.replace_suffix(0, [Line(LineOp.SCAN)])
    with pytest.raises(EditRejected):
        book.replace_suffix(1, [Line(LineOp.SCAN)])
    assert book.lines == antes


def test_lineas_son_inmutables() -> None:
    """Una línea bloqueada no puede alterarse ni por accidente."""
    line = Line(LineOp.DELIVER, None, locked=True)
    with pytest.raises(Exception):  # noqa: B017 — FrozenInstanceError
        line.locked = False  # type: ignore[misc]


def test_goto_lines_omite_la_posicion_actual() -> None:
    """El primer elemento de una ruta es donde ya está el agente, no un destino."""
    lines = goto_lines([(0, 0), (0, 1), (0, 2)])
    assert [ln.arg for ln in lines] == [(0, 1), (0, 2)]
    assert all(ln.op is LineOp.GOTO for ln in lines)


def test_copy_es_independiente() -> None:
    book = plan_simple()
    clon = book.copy()
    clon.advance()
    clon.lines.append(Line(LineOp.SCAN))
    assert book.pc == 0
    assert len(book) == 4
