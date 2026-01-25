from asdl.diagnostics import Severity
from asdl.ir.patterns import (
    AtomizedEndpoint,
    AtomizedPattern,
    PATTERN_DUPLICATE_ATOM,
    PATTERN_EMPTY_ENUM,
    PATTERN_INVALID_RANGE,
    PATTERN_TOO_LARGE,
    PATTERN_UNEXPANDED,
    atomize_endpoint,
    atomize_pattern,
)


def _atom(
    literal: str,
    segment_index: int,
    base_name: str,
    pattern_parts: list[str | int],
) -> AtomizedPattern:
    return AtomizedPattern(
        literal=literal,
        segment_index=segment_index,
        base_name=base_name,
        pattern_parts=pattern_parts,
    )


def _endpoint(
    inst: str,
    port: str,
    segment_index: int,
    base_name: str,
    pattern_parts: list[str | int],
) -> AtomizedEndpoint:
    return AtomizedEndpoint(
        inst=inst,
        port=port,
        segment_index=segment_index,
        base_name=base_name,
        pattern_parts=pattern_parts,
    )


def test_atomize_pattern_splice_order_and_origin() -> None:
    token = "OUT<P|N>;CLK<1:0>"
    atoms, diagnostics = atomize_pattern(token)

    assert diagnostics == []
    assert atoms == [
        _atom("OUTP", 0, "OUT", ["P"]),
        _atom("OUTN", 0, "OUT", ["N"]),
        _atom("CLK1", 1, "CLK", [1]),
        _atom("CLK0", 1, "CLK", [0]),
    ]


def test_atomize_pattern_base_less() -> None:
    token = "<INP|INN>;<2:0>"
    atoms, diagnostics = atomize_pattern(token)

    assert diagnostics == []
    assert atoms == [
        _atom("INP", 0, "", ["INP"]),
        _atom("INN", 0, "", ["INN"]),
        _atom("2", 1, "", [2]),
        _atom("1", 1, "", [1]),
        _atom("0", 1, "", [0]),
    ]


def test_atomize_pattern_single_atom_origin_preserves_pattern_token() -> None:
    token = "OUT<P>"
    atoms, diagnostics = atomize_pattern(token)

    assert diagnostics == []
    assert atoms == [_atom("OUTP", 0, "OUT", ["P"])]


def test_atomize_pattern_rejects_invalid_range() -> None:
    atoms, diagnostics = atomize_pattern("BUS<3:>")

    assert atoms is None
    assert len(diagnostics) == 1
    diag = diagnostics[0]
    assert diag.code == PATTERN_INVALID_RANGE
    assert diag.severity is Severity.ERROR


def test_atomize_pattern_rejects_duplicate_atoms() -> None:
    atoms, diagnostics = atomize_pattern("OUT<P|P>")

    assert atoms is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == PATTERN_DUPLICATE_ATOM


def test_atomize_endpoint_cross_product() -> None:
    inst_token = "MN<P|N>"
    pin_token = "D<0|1>"
    endpoints, diagnostics = atomize_endpoint(inst_token, pin_token)

    assert diagnostics == []
    assert endpoints == [
        _endpoint("MNP", "D0", 0, "MN.D", ["P", "0"]),
        _endpoint("MNP", "D1", 0, "MN.D", ["P", "1"]),
        _endpoint("MNN", "D0", 0, "MN.D", ["N", "0"]),
        _endpoint("MNN", "D1", 0, "MN.D", ["N", "1"]),
    ]


def test_atomize_endpoint_rejects_empty_enum() -> None:
    endpoints, diagnostics = atomize_endpoint("MN<|>", "D")

    assert endpoints is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == PATTERN_EMPTY_ENUM


def test_atomize_endpoint_rejects_overflow() -> None:
    endpoints, diagnostics = atomize_endpoint("MN<P|N>", "D<0|1>", max_atoms=3)

    assert endpoints is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == PATTERN_TOO_LARGE


def test_atomize_pattern_rejects_empty_token() -> None:
    atoms, diagnostics = atomize_pattern("")

    assert atoms is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == PATTERN_UNEXPANDED
