"""GraphIR pattern bundle metadata helpers."""

from __future__ import annotations

from dataclasses import dataclass
from xdsl.dialects.builtin import ArrayAttr, IntegerAttr, StringAttr
from xdsl.ir import Attribute

from .ops_pattern import (
    BUNDLE_PATTERN_ELIGIBLE_KEY,
    BUNDLE_PATTERN_TOKENS_KEY,
    BundleOp,
)


@dataclass(frozen=True)
class PatternBundleMetadata:
    """Decoded bundle metadata needed for rebundling.

    Attributes:
        base_name: Bundle base name.
        pattern_type: Pattern type ("literal" or "numeric").
        tokens: Token metadata aligned to bundle members.
        eligible: Eligibility flags aligned to bundle members.
    """

    base_name: str
    pattern_type: str
    tokens: list[str | int]
    eligible: list[bool]


def bundle_metadata(bundle: BundleOp) -> PatternBundleMetadata:
    """Extract pattern metadata from a bundle op.

    Args:
        bundle: Bundle op to decode.

    Returns:
        Parsed PatternBundleMetadata instance.

    Raises:
        ValueError: If required metadata is missing or invalid.
    """
    if bundle.annotations is None:
        raise ValueError("bundle annotations are required for pattern rebundling")
    tokens_attr = bundle.annotations.data.get(BUNDLE_PATTERN_TOKENS_KEY)
    eligible_attr = bundle.annotations.data.get(BUNDLE_PATTERN_ELIGIBLE_KEY)
    if tokens_attr is None or eligible_attr is None:
        raise ValueError("bundle annotations must include pattern_tokens and pattern_eligible")
    if not isinstance(tokens_attr, ArrayAttr) or not isinstance(eligible_attr, ArrayAttr):
        raise ValueError("bundle pattern metadata must provide array attributes")

    token_values: list[str | int] = []
    pattern_type = bundle.pattern_type.data
    for token in tokens_attr.data:
        token_values.append(_decode_token(token, pattern_type))

    eligible_values = [_decode_bool(value) for value in eligible_attr.data]
    member_count = len(bundle.members.data)
    if len(token_values) != member_count or len(eligible_values) != member_count:
        raise ValueError("bundle pattern metadata length must match bundle members")

    return PatternBundleMetadata(
        base_name=bundle.base_name.data,
        pattern_type=pattern_type,
        tokens=token_values,
        eligible=eligible_values,
    )


def _decode_token(value: Attribute, pattern_type: str) -> str | int:
    """Decode a pattern token attribute into a Python value.

    Args:
        value: Attribute containing the token payload.
        pattern_type: Pattern type ("literal" or "numeric").

    Returns:
        Decoded token value.
    """
    if pattern_type == "numeric":
        if isinstance(value, IntegerAttr):
            return value.value.data
        if isinstance(value, StringAttr):
            return _coerce_int(value.data)
        raise ValueError("numeric pattern tokens must be integer attributes")
    if isinstance(value, StringAttr):
        return value.data
    raise ValueError("literal pattern tokens must be string attributes")


def _decode_bool(value: Attribute) -> bool:
    """Decode a boolean eligibility attribute.

    Args:
        value: Attribute containing the eligibility flag.

    Returns:
        Parsed boolean flag.
    """
    if isinstance(value, IntegerAttr) and value.type.width.data == 1:
        return bool(value.value.data)
    raise ValueError("pattern_eligible entries must be boolean attributes")


def _coerce_int(value: str | int) -> int:
    """Coerce a numeric token into an integer.

    Args:
        value: Token value to coerce.

    Returns:
        Parsed integer value.
    """
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid numeric token '{value}'") from exc

