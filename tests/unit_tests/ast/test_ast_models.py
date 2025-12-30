import pytest
from pydantic import ValidationError

from asdl.ast import AsdlDocument, model_json_schema


def minimal_doc(view_name="nominal", view=None):
    return {
        "modules": {
            "m": {
                "ports": {"p": {"dir": "in"}},
                "port_order": ["p"],
                "views": {view_name: view or {"kind": "primitive", "templates": {"spice": "X"}}},
            }
        }
    }


def test_minimal_primitive_view_valid():
    doc = AsdlDocument(**minimal_doc())
    assert doc.modules["m"].views["nominal"].kind == "primitive"


def test_primitive_templates_non_empty():
    data = minimal_doc(view={"kind": "primitive", "templates": {}})
    with pytest.raises(ValidationError):
        AsdlDocument(**data)


def test_dummy_kind_requires_dummy_name():
    data = minimal_doc(view={"kind": "dummy"})
    with pytest.raises(ValidationError):
        AsdlDocument(**data)


def test_dummy_name_requires_dummy_kind():
    data = minimal_doc(view_name="dummy", view={"kind": "primitive", "templates": {"spice": "X"}})
    with pytest.raises(ValidationError):
        AsdlDocument(**data)


def test_instance_conns_must_be_mapping():
    view = {
        "kind": "subckt",
        "instances": {
            "i0": {"model": "m", "conns": ["p"]},
        },
    }
    data = minimal_doc(view=view)
    with pytest.raises(ValidationError):
        AsdlDocument(**data)


def test_view_kind_invalid():
    data = minimal_doc(view={"kind": "unknown", "templates": {"spice": "X"}})
    with pytest.raises(ValidationError):
        AsdlDocument(**data)


def test_port_order_required():
    data = {
        "modules": {
            "m": {
                "ports": {"p": {"dir": "in"}},
                "views": {"nominal": {"kind": "primitive", "templates": {"spice": "X"}}},
            }
        }
    }
    with pytest.raises(ValidationError):
        AsdlDocument(**data)


def test_model_json_schema_export():
    schema = model_json_schema()
    assert isinstance(schema, dict)
    assert "properties" in schema
