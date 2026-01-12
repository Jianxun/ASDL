from asdl.diagnostics import Severity
from asdl.patterns import (
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


def _atom(token: str, literal: str, origin: str | None = None) -> AtomizedPattern:
    return AtomizedPattern(token=token, literal=literal, origin=origin)


def _endpoint(
    inst_token: str,
    inst_literal: str,
    pin_token: str,
    pin_literal: str,
    *,
    inst_origin: str | None = None,
    pin_origin: str | None = None,
) -> AtomizedEndpoint:
    return AtomizedEndpoint(
        inst=_atom(inst_token, inst_literal, inst_origin),
        pin=_atom(pin_token, pin_literal, pin_origin),
    )


def test_atomize_pattern_splice_order_and_origin() -> None:
    token = "OUT<P|N>;CLK[1:0]"
    atoms, diagnostics = atomize_pattern(token)

    assert diagnostics == []
    assert atoms == [
        _atom("OUT<P>", "OUTP", token),
        _atom("OUT<N>", "OUTN", token),
        _atom("CLK[1:1]", "CLK1", token),
        _atom("CLK[0:0]", "CLK0", token),
    ]


def test_atomize_pattern_base_less() -> None:
    token = "<INP|INN>;[2:0]"
    atoms, diagnostics = atomize_pattern(token)

    assert diagnostics == []
    assert atoms == [
        _atom("<INP>", "INP", token),
        _atom("<INN>", "INN", token),
        _atom("[2:2]", "2", token),
        _atom("[1:1]", "1", token),
        _atom("[0:0]", "0", token),
    ]


def test_atomize_pattern_single_atom_origin_preserves_pattern_token() -> None:
    token = "OUT<P>"
    atoms, diagnostics = atomize_pattern(token)

    assert diagnostics == []
    assert atoms == [_atom("OUT<P>", "OUTP", token)]


def test_atomize_pattern_rejects_invalid_range() -> None:
    atoms, diagnostics = atomize_pattern("BUS[3:]")

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
        _endpoint("MN<P>", "MNP", "D<0>", "D0", inst_origin=inst_token, pin_origin=pin_token),
        _endpoint("MN<P>", "MNP", "D<1>", "D1", inst_origin=inst_token, pin_origin=pin_token),
        _endpoint("MN<N>", "MNN", "D<0>", "D0", inst_origin=inst_token, pin_origin=pin_token),
        _endpoint("MN<N>", "MNN", "D<1>", "D1", inst_origin=inst_token, pin_origin=pin_token),
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
