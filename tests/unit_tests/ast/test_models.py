import pytest
from pydantic import ValidationError

from asdl.ast import AsdlDocument


def test_document_requires_modules_or_devices() -> None:
    with pytest.raises(ValidationError) as excinfo:
        AsdlDocument.model_validate({})
    assert "module or device" in str(excinfo.value)


def test_document_requires_top_with_multiple_modules() -> None:
    with pytest.raises(ValidationError) as excinfo:
        AsdlDocument.model_validate({"modules": {"m1": {}, "m2": {}}})
    assert "top is required" in str(excinfo.value)


def test_instances_require_explicit_mapping() -> None:
    with pytest.raises(ValidationError):
        AsdlDocument.model_validate(
            {
                "modules": {
                    "m1": {
                        "instances": {"M1": "nfet_3p3"},
                        "nets": {"$VDD": [{"inst": "M1", "pin": "D"}]},
                    }
                }
            }
        )


def test_net_names_reject_pattern_sugar() -> None:
    with pytest.raises(ValidationError):
        AsdlDocument.model_validate(
            {
                "modules": {
                    "m1": {
                        "instances": {"M1": {"ref": "nfet_3p3"}},
                        "nets": {"VSS*": [{"inst": "M1", "pin": "S"}]},
                    }
                }
            }
        )


def test_device_backends_must_be_non_empty() -> None:
    with pytest.raises(ValidationError):
        AsdlDocument.model_validate(
            {
                "devices": {
                    "nfet_3p3": {
                        "ports": ["D", "G", "S", "B"],
                        "backends": {},
                    }
                }
            }
        )
