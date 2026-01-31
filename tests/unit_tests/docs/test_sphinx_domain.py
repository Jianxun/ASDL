from __future__ import annotations

from dataclasses import dataclass

from asdl.docs.sphinx_domain import (
    ASDL_DOMAIN_NAME,
    ASDL_OBJECT_TYPES,
    AsdlDomain,
    asdl_object_key,
    asdl_reference_name,
    asdl_target_id,
    register_asdl_object,
)


@dataclass
class DummyEnv:
    domaindata: dict

    def __init__(self) -> None:
        self.domaindata = {}


def test_domain_registers_object_types_and_roles() -> None:
    assert AsdlDomain.name == ASDL_DOMAIN_NAME
    assert set(AsdlDomain.object_types.keys()) == set(ASDL_OBJECT_TYPES)
    assert set(AsdlDomain.roles.keys()) == set(ASDL_OBJECT_TYPES)


def test_asdl_target_id_is_stable() -> None:
    canonical_name = asdl_reference_name("port", "VDD", module="top")
    assert canonical_name == "top::$VDD"
    assert asdl_target_id("port", canonical_name) == "asdl-port-top-vdd"


def test_register_asdl_object_records_entry() -> None:
    registry: dict[str, object] = {}
    entry = register_asdl_object(
        registry,
        "module",
        "module::top",
        "index",
        display_name="top",
    )
    key = asdl_object_key("module", "module::top")
    assert key in registry
    assert registry[key] == entry
    assert entry.anchor == asdl_target_id("module", "module::top")
    assert entry.display_name == "top"


def test_domain_register_object_tracks_docnames() -> None:
    domain = AsdlDomain(DummyEnv())
    entry = domain.register_object("net", "top::net1", "index")
    key = asdl_object_key("net", "top::net1")
    assert domain.data["objects"][key] == entry
    assert key in domain.data["docnames"]["index"]
