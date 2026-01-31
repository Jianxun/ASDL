"""Sphinx domain helpers for ASDL documentation cross-references."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Iterable, MutableMapping, Optional, Tuple

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


@dataclass(frozen=True)
class AsdlObjectEntry:
    """Registered ASDL object entry for Sphinx inventories.

    Args:
        objtype: Object type registered in the ASDL domain.
        name: Qualified reference name for the object.
        docname: Sphinx docname where the object is defined.
        target_id: Stable target id used for anchor lookup.
        display_name: Display name for inventory listings.
    """

    objtype: str
    name: str
    docname: str
    target_id: str
    display_name: str


class AsdlDomainError(ValueError):
    """Raised when ASDL domain helpers receive invalid input."""


def make_asdl_target_id(objtype: str, name: str) -> str:
    """Build a stable target id for an ASDL object.

    Args:
        objtype: ASDL object type.
        name: Qualified reference name for the object.

    Returns:
        A stable anchor id string suitable for Sphinx targets.
    """
    _validate_objtype(objtype)
    slug = _slugify(f"{objtype}-{name}")
    digest = hashlib.sha1(f"{objtype}:{name}".encode("utf-8")).hexdigest()[:8]
    return f"{ASDL_DOMAIN_NAME}-{slug}-{digest}"


def register_asdl_object(
    objects: MutableMapping[Tuple[str, str], AsdlObjectEntry],
    objtype: str,
    name: str,
    docname: str,
    display_name: Optional[str] = None,
) -> AsdlObjectEntry:
    """Register an ASDL object in a domain data mapping.

    Args:
        objects: Mapping of ``(objtype, name)`` keys to entries.
        objtype: ASDL object type.
        name: Qualified reference name for the object.
        docname: Sphinx docname where the object appears.
        display_name: Optional display name override for inventories.

    Returns:
        The registered :class:`AsdlObjectEntry`.
    """
    _validate_objtype(objtype)
    entry = AsdlObjectEntry(
        objtype=objtype,
        name=name,
        docname=docname,
        target_id=make_asdl_target_id(objtype, name),
        display_name=display_name or name,
    )
    objects[(objtype, name)] = entry
    return entry


def _validate_objtype(objtype: str) -> None:
    if objtype not in ASDL_OBJECT_TYPES:
        raise AsdlDomainError(f"Unknown ASDL object type: {objtype}")


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z]+", "-", value).strip("-").lower()
    return normalized or "asdl"


try:  # pragma: no cover - exercised indirectly when Sphinx is available.
    from docutils import nodes
    from sphinx.domains import Domain, ObjType
    from sphinx.roles import XRefRole
    from sphinx.util.docutils import SphinxDirective
    from sphinx.util.nodes import make_refnode

    SPHINX_AVAILABLE = True
except ImportError:  # pragma: no cover - Sphinx optional.
    Domain = object  # type: ignore[assignment]
    ObjType = object  # type: ignore[assignment]
    XRefRole = object  # type: ignore[assignment]
    SphinxDirective = object  # type: ignore[assignment]
    make_refnode = None  # type: ignore[assignment]
    nodes = None  # type: ignore[assignment]
    SPHINX_AVAILABLE = False


if SPHINX_AVAILABLE:

    class AsdlObjectDirective(SphinxDirective):
        """Register a named ASDL object without parsing ASDL sources."""

        has_content = False
        required_arguments = 1
        optional_arguments = 0
        final_argument_whitespace = True
        objtype = ""

        def run(self) -> list[nodes.Node]:  # type: ignore[name-defined]
            name = self.arguments[0].strip()
            if not name:
                raise AsdlDomainError("ASDL directive requires a non-empty name")

            domain = self.env.get_domain(ASDL_DOMAIN_NAME)
            if not isinstance(domain, AsdlDomain):
                raise AsdlDomainError("ASDL domain is not available")

            entry = domain.note_object(self.objtype, name)
            target_node = nodes.target("", "", ids=[entry.target_id])
            self.state.document.note_explicit_target(target_node)
            return [target_node]

    def _build_directives() -> dict[str, type[AsdlObjectDirective]]:
        directives: dict[str, type[AsdlObjectDirective]] = {}
        for objtype in ASDL_OBJECT_TYPES:
            directives[objtype] = type(
                f"Asdl{objtype.title()}Directive",
                (AsdlObjectDirective,),
                {"objtype": objtype},
            )
        return directives


    class AsdlDomain(Domain):
        """Sphinx domain for ASDL reference targets."""

        name = ASDL_DOMAIN_NAME
        label = "ASDL"
        object_types = {obj: ObjType(obj, obj) for obj in ASDL_OBJECT_TYPES}
        roles = {obj: XRefRole() for obj in ASDL_OBJECT_TYPES}
        directives = _build_directives()
        initial_data = {"objects": {}}

        def note_object(
            self,
            objtype: str,
            name: str,
            docname: Optional[str] = None,
            display_name: Optional[str] = None,
        ) -> AsdlObjectEntry:
            """Record an ASDL object for later cross-reference resolution."""
            entry = register_asdl_object(
                self.data.setdefault("objects", {}),
                objtype,
                name,
                docname or self.env.docname,
                display_name=display_name,
            )
            return entry

        def clear_doc(self, docname: str) -> None:
            to_remove = [
                key
                for key, entry in self.data.get("objects", {}).items()
                if entry.docname == docname
            ]
            for key in to_remove:
                del self.data["objects"][key]

        def merge_domaindata(self, docnames: Iterable[str], otherdata: dict) -> None:
            for key, entry in otherdata.get("objects", {}).items():
                if entry.docname in docnames:
                    self.data.setdefault("objects", {})[key] = entry

        def resolve_xref(
            self,
            env: "Environment",
            fromdocname: str,
            builder: "Builder",
            typ: str,
            target: str,
            node: nodes.Node,
            contnode: nodes.Node,
        ) -> Optional[nodes.Node]:
            entry = self.data.get("objects", {}).get((typ, target))
            if entry is None:
                return None
            return make_refnode(
                builder,
                fromdocname,
                entry.docname,
                entry.target_id,
                contnode,
                entry.display_name,
            )

        def resolve_any_xref(
            self,
            env: "Environment",
            fromdocname: str,
            builder: "Builder",
            target: str,
            node: nodes.Node,
            contnode: nodes.Node,
        ) -> list[tuple[str, nodes.Node]]:
            results: list[tuple[str, nodes.Node]] = []
            for entry in self.data.get("objects", {}).values():
                if entry.name != target:
                    continue
                ref = make_refnode(
                    builder,
                    fromdocname,
                    entry.docname,
                    entry.target_id,
                    contnode,
                    entry.display_name,
                )
                results.append((entry.objtype, ref))
            return results

        def get_objects(self) -> Iterable[tuple[str, str, str, str, str, int]]:
            for entry in self.data.get("objects", {}).values():
                yield (
                    entry.name,
                    entry.display_name,
                    entry.objtype,
                    entry.docname,
                    entry.target_id,
                    1,
                )


else:

    class AsdlDomain:  # pragma: no cover - Sphinx optional.
        """Placeholder when Sphinx is unavailable."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            raise RuntimeError("Sphinx is required to use the ASDL domain.")


def setup(app: "Sphinx") -> dict[str, object]:
    """Register the ASDL Sphinx domain."""
    if not SPHINX_AVAILABLE:
        raise RuntimeError("Sphinx is required to register the ASDL domain.")

    app.add_domain(AsdlDomain)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


__all__ = [
    "ASDL_DOMAIN_NAME",
    "ASDL_OBJECT_TYPES",
    "AsdlDomain",
    "AsdlDomainError",
    "AsdlObjectEntry",
    "SPHINX_AVAILABLE",
    "make_asdl_target_id",
    "register_asdl_object",
    "setup",
]
