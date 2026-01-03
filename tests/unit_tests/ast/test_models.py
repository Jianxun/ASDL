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


def test_device_backend_requires_template() -> None:
    with pytest.raises(ValidationError):
        DeviceBackendDecl.model_validate({})


def test_device_decl_requires_non_empty_backends() -> None:
    with pytest.raises(ValidationError):
        DeviceDecl.model_validate({"ports": ["D"], "backends": {}})


def test_device_backend_allows_extra_fields() -> None:
    backend = DeviceBackendDecl.model_validate({"template": "M{inst}", "model": "nfet"})
    assert backend.model == "nfet"


def test_module_instances_require_string_values() -> None:
    with pytest.raises(ValidationError):
        ModuleDecl.model_validate({"instances": {"M1": 123}})


def test_module_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ModuleDecl.model_validate({"exports": {"A": "B"}})
