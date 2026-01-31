"""Sphinx domain support for ASDL documentation cross-references."""

from __future__ import annotations

from dataclasses import dataclass
import copy
import re
from typing import Iterable, Optional

ASDL_DOMAIN_NAME = "asdl"
ASDL_OBJECT_TYPES = (
    "doc",
    "module",
    "port",
    "net",
    "inst",
    "var",
    "pattern",
    "import",
)


class _ObjTypeStub:
    """Fallback ObjType replacement when Sphinx is unavailable."""

    def __init__(self, name: str, *roles: str) -> None:
        self.name = name
        self.roles = roles


class _XRefRoleStub:
    """Fallback XRefRole replacement when Sphinx is unavailable."""

    def __init__(self) -> None:
        self.name = "xref"


class _DomainStub:
    """Fallback Domain replacement when Sphinx is unavailable."""

    name = ""
    label = ""
    object_types: dict[str, _ObjTypeStub] = {}
    roles: dict[str, _XRefRoleStub] = {}
    initial_data: dict[str, object] = {}

    def __init__(self, env: object) -> None:
        self.env = env
        if not hasattr(env, "domaindata"):
            raise AttributeError("Domain environment must define domaindata")
        data = copy.deepcopy(self.initial_data)
        env.domaindata.setdefault(self.name, data)
        self.data = env.domaindata[self.name]


try:  # pragma: no cover - exercised when sphinx is installed
    from docutils import nodes
    from sphinx.application import Sphinx
    from sphinx.domains import Domain, ObjType
    from sphinx.roles import XRefRole
    from sphinx.util.nodes import make_refnode

    _SPHINX_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised when sphinx is not installed
    nodes = None
    Sphinx = None
    Domain = _DomainStub
    ObjType = _ObjTypeStub
    XRefRole = _XRefRoleStub
    make_refnode = None
    _SPHINX_AVAILABLE = False


@dataclass(frozen=True)
class AsdlObjectEntry:
    """Registry entry for an ASDL object reference.

    Args:
        objtype: ASDL object type string used by the domain registry.
        name: Canonical object name stored in the registry.
        docname: Sphinx document name where the object is defined.
        anchor: Target anchor ID for the object reference.
        display_name: Display label used in inventories and cross-references.

    Invariants:
        Values are stored verbatim and treated as the canonical registry record.
    """

    objtype: str
    name: str
    docname: str
    anchor: str
    display_name: str


def asdl_reference_name(objtype: str, name: str, *, module: Optional[str] = None) -> str:
    """Return the canonical reference name for an ASDL object.

    Naming scheme:
    - Modules: ``module::<name>``
    - Imports: ``file::<alias>``
    - Doc/file: ``file::<name>``
    - Module-scoped objects: ``<module>::<name>``
    - Ports: ``<module>::$<port>``

    Args:
        objtype: ASDL object type.
        name: Base object name.
        module: Optional module name for module-scoped objects.

    Returns:
        Canonical reference name.
    """
    _validate_objtype(objtype)
    if "::" in name:
        return name
    if objtype == "module":
        return f"module::{name}"
    if objtype in {"import", "doc"}:
        return f"file::{name}"
    if objtype == "port":
        port_name = name if name.startswith("$") else f"${name}"
        return f"{module}::{port_name}" if module else port_name
    if module:
        return f"{module}::{name}"
    return name


def asdl_object_key(objtype: str, name: str) -> str:
    """Return the registry key for a named ASDL object.

    Args:
        objtype: ASDL object type string.
        name: Canonical object name.

    Returns:
        Registry key formatted as ``<objtype>:<name>``.

    Side Effects:
        Validates ``objtype`` against the configured ASDL object types.
    """
    _validate_objtype(objtype)
    return f"{objtype}:{name}"


def asdl_target_id(objtype: str, name: str) -> str:
    """Return a stable target ID for an ASDL object reference.

    Args:
        objtype: ASDL object type string.
        name: Canonical object name.

    Returns:
        Normalized target identifier prefixed with ``asdl-``.

    Side Effects:
        Validates ``objtype`` against the configured ASDL object types.
    """
    _validate_objtype(objtype)
    normalized = _normalize_target(name)
    return f"asdl-{objtype}-{normalized}"


def register_asdl_object(
    registry: dict[str, AsdlObjectEntry],
    objtype: str,
    name: str,
    docname: str,
    *,
    display_name: Optional[str] = None,
    anchor: Optional[str] = None,
) -> AsdlObjectEntry:
    """Register an ASDL object entry in the provided registry.

    Args:
        registry: Mutable registry mapping keys to object entries.
        objtype: ASDL object type string.
        name: Canonical object name.
        docname: Sphinx document name where the object is defined.
        display_name: Optional display label for inventories or xrefs.
        anchor: Optional explicit anchor target ID.

    Returns:
        The newly created registry entry.

    Side Effects:
        Mutates ``registry`` by inserting the entry for the object key.
    """
    _validate_objtype(objtype)
    target = anchor or asdl_target_id(objtype, name)
    entry = AsdlObjectEntry(
        objtype=objtype,
        name=name,
        docname=docname,
        anchor=target,
        display_name=display_name or name,
    )
    registry[asdl_object_key(objtype, name)] = entry
    return entry


class AsdlDomain(Domain):
    """Sphinx domain for ASDL objects and cross-references."""

    name = ASDL_DOMAIN_NAME
    label = "ASDL"
    object_types = {objtype: ObjType(objtype, objtype) for objtype in ASDL_OBJECT_TYPES}
    roles = {objtype: XRefRole() for objtype in ASDL_OBJECT_TYPES}
    initial_data = {"objects": {}, "docnames": {}}

    def register_object(
        self,
        objtype: str,
        name: str,
        docname: str,
        *,
        display_name: Optional[str] = None,
        anchor: Optional[str] = None,
    ) -> AsdlObjectEntry:
        """Register an ASDL object in the domain data store.

        Args:
            objtype: ASDL object type string.
            name: Canonical object name.
            docname: Sphinx document name where the object is defined.
            display_name: Optional display label for inventories or xrefs.
            anchor: Optional explicit anchor target ID.

        Returns:
            The registry entry stored for the object.

        Side Effects:
            Updates the domain ``objects`` registry and ``docnames`` index.
        """
        entry = register_asdl_object(
            self.data["objects"],
            objtype,
            name,
            docname,
            display_name=display_name,
            anchor=anchor,
        )
        self.data["docnames"].setdefault(docname, set()).add(
            asdl_object_key(objtype, name)
        )
        return entry

    def note_object(
        self,
        objtype: str,
        name: str,
        docname: str,
        *,
        display_name: Optional[str] = None,
        anchor: Optional[str] = None,
    ) -> AsdlObjectEntry:
        """Alias for register_object to match Sphinx naming conventions.

        Args:
            objtype: ASDL object type string.
            name: Canonical object name.
            docname: Sphinx document name where the object is defined.
            display_name: Optional display label for inventories or xrefs.
            anchor: Optional explicit anchor target ID.

        Returns:
            The registry entry stored for the object.

        Side Effects:
            Updates the domain ``objects`` registry and ``docnames`` index.
        """
        return self.register_object(
            objtype,
            name,
            docname,
            display_name=display_name,
            anchor=anchor,
        )

    def clear_doc(self, docname: str) -> None:
        """Remove all ASDL objects associated with a document.

        Args:
            docname: Sphinx document name whose objects should be removed.

        Returns:
            None.

        Side Effects:
            Deletes entries from the domain ``objects`` registry and ``docnames`` index.
        """
        keys = self.data["docnames"].pop(docname, set())
        for key in keys:
            self.data["objects"].pop(key, None)

    def resolve_xref(
        self,
        env: object,
        fromdocname: str,
        builder: object,
        typ: str,
        target: str,
        node: object,
        contnode: object,
    ) -> Optional[object]:
        """Resolve ASDL cross-references to registered targets."""
        if not _SPHINX_AVAILABLE:
            return None
        key = asdl_object_key(typ, target)
        entry = self.data["objects"].get(key)
        if entry is None:
            return None
        return make_refnode(
            builder,
            fromdocname,
            entry.docname,
            entry.anchor,
            contnode,
            entry.display_name,
        )

    def get_objects(self) -> Iterable[tuple[str, str, str, str, str, int]]:
        """Yield objects for Sphinx inventory generation."""
        for entry in self.data["objects"].values():
            yield (
                entry.name,
                entry.display_name,
                entry.objtype,
                entry.docname,
                entry.anchor,
                1,
            )

    def merge_domaindata(self, docnames: Iterable[str], otherdata: dict[str, object]) -> None:
        """Merge domain data when running in parallel builds."""
        objects = otherdata.get("objects", {})
        doc_map = otherdata.get("docnames", {})
        for docname in docnames:
            for key in doc_map.get(docname, set()):
                entry = objects.get(key)
                if entry is not None:
                    self.data["objects"][key] = entry
            if docname in doc_map:
                self.data["docnames"][docname] = set(doc_map[docname])


def setup(app: "Sphinx") -> dict[str, object]:
    """Register the ASDL Sphinx domain extension.

    Args:
        app: Sphinx application instance used to register the domain.

    Returns:
        Extension metadata describing parallel safety.

    Side Effects:
        Registers :class:`AsdlDomain` with the Sphinx application.
    """
    if not _SPHINX_AVAILABLE:
        raise RuntimeError("Sphinx is required to register the ASDL domain")
    app.add_domain(AsdlDomain)
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}


def _normalize_target(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return normalized or "asdl"


def _validate_objtype(objtype: str) -> None:
    if objtype not in ASDL_OBJECT_TYPES:
        raise ValueError(f"Unknown ASDL object type: {objtype}")


__all__ = [
    "ASDL_DOMAIN_NAME",
    "ASDL_OBJECT_TYPES",
    "AsdlDomain",
    "AsdlObjectEntry",
    "asdl_object_key",
    "asdl_reference_name",
    "asdl_target_id",
    "register_asdl_object",
    "setup",
]
