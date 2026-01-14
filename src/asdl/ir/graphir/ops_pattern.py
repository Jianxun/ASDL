"""GraphIR pattern ops for bundles and pattern expressions."""

from __future__ import annotations

from typing import Iterable

from xdsl.dialects.builtin import ArrayAttr, DictionaryAttr, StringAttr
from xdsl.ir import Attribute
from xdsl.irdl import IRDLOperation, attr_def, irdl_op_definition, opt_attr_def
from xdsl.utils.exceptions import VerifyException

from .attrs import (
    GraphIdAttr,
    GraphParamRefAttr,
    _coerce_graph_id,
    _coerce_graph_param_ref,
)

_PATTERN_KINDS = {"net", "endpoint", "param", "inst"}
_PATTERN_TYPES = {"literal", "numeric"}


def _require_pattern_kind(kind: StringAttr, *, owner: str) -> str:
    """Validate and return a pattern kind string.

    Args:
        kind: Kind attribute to validate.
        owner: Context string for error messages.

    Returns:
        The validated kind string.
    """
    kind_value = kind.data
    if kind_value not in _PATTERN_KINDS:
        kinds = ", ".join(sorted(_PATTERN_KINDS))
        raise VerifyException(f"{owner} kind must be one of: {kinds}")
    return kind_value


def _require_pattern_type(pattern_type: StringAttr) -> None:
    """Validate a pattern type string.

    Args:
        pattern_type: Pattern type attribute to validate.
    """
    if pattern_type.data not in _PATTERN_TYPES:
        types = ", ".join(sorted(_PATTERN_TYPES))
        raise VerifyException(f"bundle pattern_type must be one of: {types}")


def _coerce_bundle_member(value: object) -> Attribute:
    """Coerce a bundle member input into a GraphIR attribute.

    Args:
        value: Bundle member input.

    Returns:
        A GraphIdAttr or GraphParamRefAttr instance.
    """
    if isinstance(value, GraphParamRefAttr):
        return value
    if isinstance(value, tuple) and len(value) == 2:
        return _coerce_graph_param_ref(value)
    if isinstance(value, (GraphIdAttr, StringAttr, str, int)):
        return _coerce_graph_id(value)
    raise TypeError(f"Unsupported bundle member: {value!r}")


@irdl_op_definition
class BundleOp(IRDLOperation):
    """GraphIR bundle definition for pattern metadata.

    Attributes:
        bundle_id: Stable bundle identifier.
        kind: Pattern kind (net, endpoint, param, inst).
        base_name: Base name for the bundle.
        pattern_type: Pattern type ("literal" or "numeric").
        members: Ordered bundle members.
        annotations: Optional annotations.
    """

    name = "graphir.bundle"

    bundle_id = attr_def(GraphIdAttr)
    kind = attr_def(StringAttr)
    base_name = attr_def(StringAttr)
    pattern_type = attr_def(StringAttr)
    members = attr_def(ArrayAttr[Attribute])
    annotations = opt_attr_def(DictionaryAttr)

    assembly_format = "attr-dict"

    def __init__(
        self,
        *,
        bundle_id: GraphIdAttr | StringAttr | str | int,
        kind: StringAttr | str,
        base_name: StringAttr | str,
        pattern_type: StringAttr | str,
        members: ArrayAttr[Attribute] | Iterable[object],
        annotations: DictionaryAttr | None = None,
    ) -> None:
        """Initialize a bundle op.

        Args:
            bundle_id: Stable bundle identifier.
            kind: Pattern kind (net, endpoint, param, inst).
            base_name: Base name for the bundle.
            pattern_type: Pattern type ("literal" or "numeric").
            members: Ordered bundle members.
            annotations: Optional annotations dictionary.
        """
        if isinstance(kind, str):
            kind = StringAttr(kind)
        if isinstance(base_name, str):
            base_name = StringAttr(base_name)
        if isinstance(pattern_type, str):
            pattern_type = StringAttr(pattern_type)
        bundle_id = _coerce_graph_id(bundle_id)
        if not isinstance(members, ArrayAttr):
            members = ArrayAttr([_coerce_bundle_member(member) for member in members])
        attributes = {
            "bundle_id": bundle_id,
            "kind": kind,
            "base_name": base_name,
            "pattern_type": pattern_type,
            "members": members,
        }
        if annotations is not None:
            attributes["annotations"] = annotations
        super().__init__(attributes=attributes)

    def verify_(self) -> None:
        """Verify bundle attributes."""
        kind = _require_pattern_kind(self.kind, owner="bundle")
        _require_pattern_type(self.pattern_type)
        if kind == "param":
            for member in self.members.data:
                if not isinstance(member, GraphParamRefAttr):
                    raise VerifyException("param bundle members must be param_ref")
        else:
            for member in self.members.data:
                if not isinstance(member, GraphIdAttr):
                    raise VerifyException(
                        f"{kind} bundle members must be graph_id attributes"
                    )


@irdl_op_definition
class PatternExprOp(IRDLOperation):
    """GraphIR pattern expression definition.

    Attributes:
        pattern_id: Stable pattern expression identifier.
        kind: Pattern kind (net, endpoint, param, inst).
        owner: Pattern owner (GraphIdAttr or GraphParamRefAttr).
        bundles: Ordered bundle identifiers.
        annotations: Optional annotations.
    """

    name = "graphir.pattern_expr"

    pattern_id = attr_def(GraphIdAttr)
    kind = attr_def(StringAttr)
    owner = attr_def(Attribute)
    bundles = attr_def(ArrayAttr[GraphIdAttr])
    annotations = opt_attr_def(DictionaryAttr)

    assembly_format = "attr-dict"

    def __init__(
        self,
        *,
        pattern_id: GraphIdAttr | StringAttr | str | int,
        kind: StringAttr | str,
        owner: GraphIdAttr
        | GraphParamRefAttr
        | StringAttr
        | str
        | int
        | tuple[GraphIdAttr | StringAttr | str | int, StringAttr | str],
        bundles: ArrayAttr[GraphIdAttr]
        | Iterable[GraphIdAttr | StringAttr | str | int],
        annotations: DictionaryAttr | None = None,
    ) -> None:
        """Initialize a pattern expression op.

        Args:
            pattern_id: Stable pattern expression identifier.
            kind: Pattern kind (net, endpoint, param, inst).
            owner: Pattern owner.
            bundles: Ordered bundle identifiers.
            annotations: Optional annotations dictionary.
        """
        if isinstance(kind, str):
            kind = StringAttr(kind)
        pattern_id = _coerce_graph_id(pattern_id)
        if isinstance(owner, GraphParamRefAttr):
            owner_attr: Attribute = owner
        elif isinstance(owner, tuple) and len(owner) == 2:
            owner_attr = _coerce_graph_param_ref(owner)
        elif isinstance(owner, (GraphIdAttr, StringAttr, str, int)):
            owner_attr = _coerce_graph_id(owner)
        else:
            raise TypeError(f"Unsupported pattern owner: {owner!r}")
        if not isinstance(bundles, ArrayAttr):
            bundles = ArrayAttr([_coerce_graph_id(bundle_id) for bundle_id in bundles])
        attributes = {
            "pattern_id": pattern_id,
            "kind": kind,
            "owner": owner_attr,
            "bundles": bundles,
        }
        if annotations is not None:
            attributes["annotations"] = annotations
        super().__init__(attributes=attributes)

    def verify_(self) -> None:
        """Verify pattern expression attributes."""
        kind = _require_pattern_kind(self.kind, owner="pattern_expr")
        if kind == "param":
            if not isinstance(self.owner, GraphParamRefAttr):
                raise VerifyException("param pattern_expr owner must be param_ref")
        else:
            if not isinstance(self.owner, GraphIdAttr):
                raise VerifyException("pattern_expr owner must be a graph_id")


__all__ = ["BundleOp", "PatternExprOp"]
