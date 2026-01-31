import pytest

from asdl.docs.sphinx_domain import (
    AsdlDomainError,
    make_asdl_target_id,
    register_asdl_object,
)


def test_make_asdl_target_id_is_stable_and_scoped() -> None:
    first = make_asdl_target_id("module", "top")
    second = make_asdl_target_id("module", "top")
    assert first == second
    assert first.startswith("asdl-module-top-")

    other = make_asdl_target_id("net", "top::net1")
    assert other.startswith("asdl-net-top-net1-")
    assert other != first


def test_register_asdl_object_records_entry() -> None:
    objects: dict[tuple[str, str], object] = {}
    entry = register_asdl_object(objects, "module", "top", "index")

    assert objects[("module", "top")] == entry
    assert entry.target_id == make_asdl_target_id("module", "top")
    assert entry.display_name == "top"


def test_register_asdl_object_rejects_unknown_type() -> None:
    objects: dict[tuple[str, str], object] = {}
    with pytest.raises(AsdlDomainError):
        register_asdl_object(objects, "unknown", "name", "index")
