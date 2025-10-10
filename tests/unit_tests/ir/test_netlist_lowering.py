from pathlib import Path

from asdl.parser import ASDLParser
from asdl.ir.converter import asdl_ast_to_netlist_module, print_xdsl_module


def test_asdl_to_netlist_module_ports_and_instances() -> None:
    fixture = Path(__file__).resolve().parents[2] / "fixtures" / "ir" / "single_inst.yml"
    parser = ASDLParser()
    asdl_file, diags = parser.parse_file(str(fixture))
    assert asdl_file is not None and not any(d.is_error for d in diags)

    mod = asdl_ast_to_netlist_module(asdl_file)
    text = print_xdsl_module(mod)

    # Expect two modules emitted: prim and top (order unspecified, but both present)
    assert "netlist.module" in text
    assert "sym_name = \"prim\"" in text
    assert "sym_name = \"top\"" in text

    # Ports preserved in order for both modules
    assert "ports = [\"a\", \"b\"]" in text

    # Instance inside top with named pin_map and pin_order
    assert "netlist.instance" in text
    assert "model_ref = \"prim\"" in text
    assert "pin_map = {\"a\": \"a\", \"b\": \"b\"}" in text or "pin_map = {\"b\": \"b\", \"a\": \"a\"}" in text
    assert "pin_order = [\"a\", \"b\"]" in text


