import pytest
from pydantic import ValidationError

from asdl.ast import AsdlDocument, DeviceBackendDecl, DeviceDecl, ModuleDecl


def test_document_requires_modules_or_devices() -> None:
    with pytest.raises(ValidationError):
        AsdlDocument.model_validate({})


def test_document_requires_top_when_multiple_modules() -> None:
    data = {
        "modules": {
            "a": {"nets": {"$A": ["I1.P"]}},
            "b": {"nets": {"$B": ["I2.P"]}},
        }
    }
    with pytest.raises(ValidationError):
        AsdlDocument.model_validate(data)


def test_document_allows_imports() -> None:
    document = AsdlDocument.model_validate({"imports": {"gf": "lib.asdl"}, "modules": {"top": {}}})
    assert document.imports == {"gf": "lib.asdl"}


def test_document_rejects_non_string_import_paths() -> None:
    with pytest.raises(ValidationError):
        AsdlDocument.model_validate({"imports": {"gf": 123}, "modules": {"top": {}}})


def test_device_backend_requires_template() -> None:
    with pytest.raises(ValidationError):
        DeviceBackendDecl.model_validate({})


def test_device_decl_requires_non_empty_backends() -> None:
    with pytest.raises(ValidationError):
        DeviceDecl.model_validate({"ports": ["D"], "backends": {}})


def test_device_decl_allows_missing_ports() -> None:
    device = DeviceDecl.model_validate(
        {"backends": {"ngspice": {"template": "R{name} {ports} {params}"}}}
    )
    assert device.ports is None


def test_device_backend_allows_extra_fields() -> None:
    backend = DeviceBackendDecl.model_validate({"template": "M{inst}", "model": "nfet"})
    assert backend.model == "nfet"


def test_module_instances_require_string_values() -> None:
    with pytest.raises(ValidationError):
        ModuleDecl.model_validate({"instances": {"M1": 123}})


def test_module_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ModuleDecl.model_validate({"exports": {"A": "B"}})


def test_module_accepts_patterns_and_instance_defaults() -> None:
    module = ModuleDecl.model_validate(
        {
            "patterns": {"k": "<1|2>"},
            "instance_defaults": {"mos": {"bindings": {"B": "$VSS"}}},
        }
    )
    assert module.patterns == {"k": "<1|2>"}
    assert module.instance_defaults["mos"].bindings == {"B": "$VSS"}


def test_module_rejects_invalid_pattern_group() -> None:
    with pytest.raises(ValidationError):
        ModuleDecl.model_validate({"patterns": {"k": "MN<1|2>"}})


def test_module_rejects_instance_defaults_missing_bindings() -> None:
    with pytest.raises(ValidationError):
        ModuleDecl.model_validate({"instance_defaults": {"mos": {}}})
