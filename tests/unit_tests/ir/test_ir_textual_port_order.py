from pathlib import Path

from asdl.parser import ASDLParser
from asdl.ir import build_textual_ir


def test_textual_ir_preserves_port_order(tmp_path: Path) -> None:
    # Use fixture ASDL to ensure stable test inputs independent of examples/
    fixture = Path(__file__).resolve().parents[2] / "fixtures" / "ir" / "prim_with_ports.yml"
    parser = ASDLParser()
    asdl_file, diags = parser.parse_file(str(fixture))
    assert asdl_file is not None and not any(d.is_error for d in diags)

    text = build_textual_ir(asdl_file)
    # Expect ports listed in declared order: a, b, c
    a_idx = text.index("%port a ")
    b_idx = text.index("%port b ")
    c_idx = text.index("%port c ")
    assert a_idx < b_idx < c_idx

