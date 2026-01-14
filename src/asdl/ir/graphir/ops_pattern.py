"""GraphIR pattern ops for bundles and pattern expressions."""

from __future__ import annotations

from typing import Iterable

from xdsl.dialects.builtin import (
    ArrayAttr,
    BoolAttr,
    DictionaryAttr,
    IntegerAttr,
    StringAttr,
)
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
BUNDLE_PATTERN_TOKENS_KEY = "pattern_tokens"
BUNDLE_PATTERN_ELIGIBLE_KEY = "pattern_eligible"


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


def _coerce_pattern_token(value: object) -> Attribute:
    """Coerce a pattern token into an attribute.

    Args:
        value: Pattern token input (string or int).

    Returns:
        Attribute representing the token.
    """
    if isinstance(value, (StringAttr, IntegerAttr)):
        return value
    if isinstance(value, int):
        return IntegerAttr.from_int_and_width(value, 64)
    if isinstance(value, str):
        return StringAttr(value)
    raise TypeError(f"Unsupported pattern token: {value!r}")


def _coerce_pattern_tokens(
    tokens: ArrayAttr[Attribute] | Iterable[object],
) -> ArrayAttr[Attribute]:
    """Coerce a sequence of pattern tokens into an ArrayAttr.

    Args:
        tokens: Pattern token inputs.

    Returns:
        ArrayAttr of token attributes.
    """
    if isinstance(tokens, ArrayAttr):
        return tokens
    return ArrayAttr([_coerce_pattern_token(token) for token in tokens])


def _coerce_pattern_eligible(
    eligible: ArrayAttr[BoolAttr] | Iterable[bool],
) -> ArrayAttr[BoolAttr]:
    """Coerce pattern eligibility flags into an ArrayAttr.

    Args:
        eligible: Eligibility inputs.

    Returns:
        ArrayAttr of BoolAttr entries.
    """
    if isinstance(eligible, ArrayAttr):
        return eligible
    return ArrayAttr([BoolAttr.from_bool(bool(value)) for value in eligible])


def _merge_bundle_annotations(
    annotations: DictionaryAttr | None,
    pattern_tokens: ArrayAttr[Attribute] | Iterable[object] | None,
    pattern_eligible: ArrayAttr[BoolAttr] | Iterable[bool] | None,
) -> DictionaryAttr | None:
    """Merge bundle annotations with pattern metadata.

    Args:
        annotations: Existing annotations dictionary.
        pattern_tokens: Optional pattern token metadata.
        pattern_eligible: Optional eligibility metadata.

    Returns:
        Merged annotations dictionary or None.
    """
    merged = dict(annotations.data) if annotations is not None else {}
    if pattern_tokens is not None:
        if BUNDLE_PATTERN_TOKENS_KEY in merged:
            raise ValueError("bundle annotations already define pattern_tokens")
        merged[BUNDLE_PATTERN_TOKENS_KEY] = _coerce_pattern_tokens(pattern_tokens)
    if pattern_eligible is not None:
        if BUNDLE_PATTERN_ELIGIBLE_KEY in merged:
            raise ValueError("bundle annotations already define pattern_eligible")
        merged[BUNDLE_PATTERN_ELIGIBLE_KEY] = _coerce_pattern_eligible(pattern_eligible)
    return DictionaryAttr(merged) if merged else None


def _is_numeric_token(value: Attribute) -> bool:
    """Return true if the attribute is a numeric token.

    Args:
        value: Attribute to inspect.

    Returns:
        True when the token is numeric.
    """
    if isinstance(value, IntegerAttr):
        return True
    if isinstance(value, StringAttr):
        try:
            int(value.data)
            return True
        except ValueError:
            return False
    return False


@irdl_op_definition
class BundleOp(IRDLOperation):
    """GraphIR bundle definition for pattern metadata.

    Attributes:
        bundle_id: Stable bundle identifier.
        kind: Pattern kind (net, endpoint, param, inst).
        base_name: Base name for the bundle.
        pattern_type: Pattern type ("literal" or "numeric").
        members: Ordered bundle members.
        pattern_tokens: Optional pattern token metadata for each member.
        pattern_eligible: Optional eligibility flags for each member.
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
        pattern_tokens: ArrayAttr[Attribute] | Iterable[object] | None = None,
        pattern_eligible: ArrayAttr[BoolAttr] | Iterable[bool] | None = None,
        annotations: DictionaryAttr | None = None,
    ) -> None:
        """Initialize a bundle op.

        Args:
            bundle_id: Stable bundle identifier.
            kind: Pattern kind (net, endpoint, param, inst).
            base_name: Base name for the bundle.
            pattern_type: Pattern type ("literal" or "numeric").
            members: Ordered bundle members.
            pattern_tokens: Optional pattern token metadata aligned to members.
            pattern_eligible: Optional eligibility flags aligned to members.
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
        merged_annotations = _merge_bundle_annotations(
            annotations, pattern_tokens, pattern_eligible
        )
        if merged_annotations is not None:
            attributes["annotations"] = merged_annotations
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
        if self.annotations is None:
            return
        tokens_attr = self.annotations.data.get(BUNDLE_PATTERN_TOKENS_KEY)
        eligible_attr = self.annotations.data.get(BUNDLE_PATTERN_ELIGIBLE_KEY)
        if tokens_attr is None and eligible_attr is None:
            return
        if tokens_attr is None or eligible_attr is None:
            raise VerifyException(
                "bundle annotations must include pattern_tokens and pattern_eligible"
            )
        if not isinstance(tokens_attr, ArrayAttr) or not isinstance(
            eligible_attr, ArrayAttr
        ):
            raise VerifyException(
                "bundle pattern metadata must use ArrayAttr values in annotations"
            )
        member_count = len(self.members.data)
        if len(tokens_attr.data) != member_count or len(eligible_attr.data) != member_count:
            raise VerifyException(
                "bundle pattern metadata length must match bundle members"
            )
        pattern_type = self.pattern_type.data
        for token in tokens_attr.data:
            if pattern_type == "numeric":
                if not _is_numeric_token(token):
                    raise VerifyException(
                        "numeric bundle pattern_tokens must be integer or numeric strings"
                    )
            else:
                if not isinstance(token, StringAttr):
                    raise VerifyException(
                        "literal bundle pattern_tokens must be string attributes"
                    )
        for value in eligible_attr.data:
            if not isinstance(value, IntegerAttr) or value.type.width.data != 1:
                raise VerifyException(
                    "bundle pattern_eligible entries must be boolean attributes"
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


__all__ = [
    "BUNDLE_PATTERN_ELIGIBLE_KEY",
    "BUNDLE_PATTERN_TOKENS_KEY",
    "BundleOp",
    "PatternExprOp",
]
