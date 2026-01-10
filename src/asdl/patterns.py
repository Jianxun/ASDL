from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from .diagnostics import Diagnostic, Severity, format_code

MAX_EXPANSION_SIZE = 10_000
NO_SPAN_NOTE = "No source span available."

PATTERN_INVALID_RANGE = format_code("PASS", 101)
PATTERN_EMPTY_ENUM = format_code("PASS", 102)
PATTERN_EMPTY_SPLICE = format_code("PASS", 103)
PATTERN_DUPLICATE_ATOM = format_code("PASS", 104)
PATTERN_TOO_LARGE = format_code("PASS", 105)
PATTERN_UNEXPANDED = format_code("PASS", 106)


def expand_pattern(
    token: str, *, max_atoms: int = MAX_EXPANSION_SIZE
) -> Tuple[Optional[List[str]], List[Diagnostic]]:
    diagnostics: List[Diagnostic] = []
    if not token:
        diagnostics.append(_diagnostic(PATTERN_UNEXPANDED, "Pattern token is empty."))
        return None, diagnostics

    segments, diag = _split_splice_segments(token)
    if diag is not None:
        return None, [diag]
    if any(segment == "" for segment in segments):
        return None, [_diagnostic(PATTERN_EMPTY_SPLICE, _empty_splice_message(token))]

    expanded: List[str] = []
    for segment in segments:
        segment_expansion, diag = _expand_segment(segment, token, max_atoms)
        if diag is not None:
            return None, [diag]
        if len(expanded) + len(segment_expansion) > max_atoms:
            return None, [_diagnostic(PATTERN_TOO_LARGE, _too_large_message(token, max_atoms))]
        expanded.extend(segment_expansion)

    duplicates = _find_duplicates(expanded)
    if duplicates:
        return None, [_diagnostic(PATTERN_DUPLICATE_ATOM, _duplicate_message(duplicates, token))]

    return expanded, diagnostics


def expand_endpoint(
    inst: str, pin: str, *, max_atoms: int = MAX_EXPANSION_SIZE
) -> Tuple[Optional[List[Tuple[str, str]]], List[Diagnostic]]:
    token = f"{inst}.{pin}"
    inst_expanded, inst_diags = expand_pattern(inst, max_atoms=max_atoms)
    if inst_expanded is None:
        return None, inst_diags
    pin_expanded, pin_diags = expand_pattern(pin, max_atoms=max_atoms)
    diagnostics = [*inst_diags, *pin_diags]
    if pin_expanded is None:
        return None, diagnostics

    product_size = len(inst_expanded) * len(pin_expanded)
    if product_size > max_atoms:
        diagnostics.append(
            _diagnostic(
                PATTERN_TOO_LARGE,
                _too_large_message(token, max_atoms),
            )
        )
        return None, diagnostics

    endpoints: List[Tuple[str, str]] = []
    for inst_atom in inst_expanded:
        for pin_atom in pin_expanded:
            endpoints.append((inst_atom, pin_atom))

    return endpoints, diagnostics


def _split_splice_segments(token: str) -> Tuple[Optional[List[str]], Optional[Diagnostic]]:
    segments: List[str] = []
    buffer: List[str] = []
    state: Optional[str] = None

    for char in token:
        if state is None:
            if char == ";":
                segments.append("".join(buffer))
                buffer = []
                continue
            if char == "<":
                state = "enum"
            elif char == "[":
                state = "range"
            elif char in ("]", ">"):
                return None, _diagnostic(
                    PATTERN_UNEXPANDED,
                    f"Unexpected '{char}' in pattern token '{token}'.",
                )
        else:
            if char == ";":
                return None, _diagnostic(
                    PATTERN_UNEXPANDED,
                    f"Splice delimiter ';' is not allowed inside pattern groups in '{token}'.",
                )
            if char in ("<", "["):
                return None, _diagnostic(
                    PATTERN_UNEXPANDED,
                    f"Nested pattern delimiters are not allowed in '{token}'.",
                )
            if state == "enum" and char == ">":
                state = None
            elif state == "range" and char == "]":
                state = None
        buffer.append(char)

    if state is not None:
        return None, _diagnostic(
            PATTERN_UNEXPANDED,
            f"Unterminated pattern delimiter in '{token}'.",
        )

    segments.append("".join(buffer))
    return segments, None


def _expand_segment(
    segment: str, token: str, max_atoms: int
) -> Tuple[Optional[List[str]], Optional[Diagnostic]]:
    if _has_whitespace(segment):
        return None, _diagnostic(
            PATTERN_UNEXPANDED,
            f"Whitespace is not allowed in pattern token '{token}'.",
        )

    tokens, diag = _tokenize_segment(segment, token)
    if diag is not None:
        return None, diag

    current: List[str] = [""]
    for kind, payload in tokens:
        if kind == "literal":
            current = [value + payload for value in current]
            continue

        if kind == "enum":
            alts = payload
            next_size = len(current) * len(alts)
            if next_size > max_atoms:
                return None, _diagnostic(PATTERN_TOO_LARGE, _too_large_message(token, max_atoms))
            current = [
                _join_with_suffix(prefix, suffix)
                for prefix in current
                for suffix in alts
            ]
            continue

        if kind == "range":
            start, end = payload
            value_count = abs(end - start) + 1
            next_size = len(current) * value_count
            if next_size > max_atoms:
                return None, _diagnostic(PATTERN_TOO_LARGE, _too_large_message(token, max_atoms))
            current = [
                _join_with_suffix(prefix, str(value))
                for prefix in current
                for value in _range_values(start, end)
            ]
            continue

        return None, _diagnostic(
            PATTERN_UNEXPANDED,
            f"Unhandled pattern token '{token}'.",
        )

    return current, None


def _tokenize_segment(
    segment: str, token: str
) -> Tuple[Optional[List[Tuple[str, object]]], Optional[Diagnostic]]:
    tokens: List[Tuple[str, object]] = []
    literal: List[str] = []
    index = 0

    while index < len(segment):
        char = segment[index]
        if char == "<":
            if literal:
                tokens.append(("literal", "".join(literal)))
                literal = []
            close = segment.find(">", index + 1)
            if close == -1:
                return None, _diagnostic(
                    PATTERN_UNEXPANDED,
                    f"Unterminated enumeration in '{token}'.",
                )
            content = segment[index + 1 : close]
            diag = _validate_enum_content(content, token)
            if diag is not None:
                return None, diag
            alts = content.split("|") if content else []
            if any(alt == "" for alt in alts):
                return None, _diagnostic(PATTERN_EMPTY_ENUM, _empty_enum_message(token))
            tokens.append(("enum", alts))
            index = close + 1
            continue

        if char == "[":
            if literal:
                tokens.append(("literal", "".join(literal)))
                literal = []
            close = segment.find("]", index + 1)
            if close == -1:
                return None, _diagnostic(
                    PATTERN_UNEXPANDED,
                    f"Unterminated numeric range in '{token}'.",
                )
            content = segment[index + 1 : close]
            range_value, diag = _parse_range_content(content, token)
            if diag is not None:
                return None, diag
            tokens.append(("range", range_value))
            index = close + 1
            continue

        if char in "|]>":
            return None, _diagnostic(
                PATTERN_UNEXPANDED,
                f"Unexpected '{char}' in pattern token '{token}'.",
            )

        literal.append(char)
        index += 1

    if literal:
        tokens.append(("literal", "".join(literal)))
    return tokens, None


def _validate_enum_content(content: str, token: str) -> Optional[Diagnostic]:
    if content == "":
        return _diagnostic(PATTERN_EMPTY_ENUM, _empty_enum_message(token))
    if _has_whitespace(content):
        return _diagnostic(
            PATTERN_UNEXPANDED,
            f"Whitespace is not allowed around '|' in '{token}'.",
        )
    if "," in content:
        return _diagnostic(
            PATTERN_UNEXPANDED,
            f"Enumeration alternatives must use '|' in '{token}'.",
        )
    if any(char in "<>[];" for char in content):
        return _diagnostic(
            PATTERN_UNEXPANDED,
            f"Nested pattern delimiters are not allowed in '{token}'.",
        )
    return None


def _parse_range_content(content: str, token: str) -> Tuple[Optional[Tuple[int, int]], Optional[Diagnostic]]:
    if content.count(":") != 1:
        return None, _diagnostic(PATTERN_INVALID_RANGE, _invalid_range_message(token))
    if _has_whitespace(content):
        return None, _diagnostic(PATTERN_INVALID_RANGE, _invalid_range_message(token))
    if any(char in "<>[];|" for char in content):
        return None, _diagnostic(PATTERN_INVALID_RANGE, _invalid_range_message(token))

    start_text, end_text = content.split(":", 1)
    if start_text == "" or end_text == "":
        return None, _diagnostic(PATTERN_INVALID_RANGE, _invalid_range_message(token))
    try:
        start = int(start_text)
        end = int(end_text)
    except ValueError:
        return None, _diagnostic(PATTERN_INVALID_RANGE, _invalid_range_message(token))

    return (start, end), None


def _range_values(start: int, end: int) -> Iterable[int]:
    if start <= end:
        return range(start, end + 1)
    return range(start, end - 1, -1)


def _join_with_suffix(prefix: str, suffix: str) -> str:
    if prefix:
        return f"{prefix}{suffix}"
    return suffix


def _find_duplicates(items: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    duplicates: List[str] = []
    for item in items:
        if item in seen and item not in duplicates:
            duplicates.append(item)
            continue
        seen.add(item)
    return duplicates


def _has_whitespace(value: str) -> bool:
    return any(char.isspace() for char in value)


def _diagnostic(code: str, message: str) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=None,
        notes=[NO_SPAN_NOTE],
        source="pattern",
    )


def _empty_enum_message(token: str) -> str:
    return f"Empty enumeration in pattern token '{token}'."


def _empty_splice_message(token: str) -> str:
    return f"Empty splice segment in pattern token '{token}'."


def _invalid_range_message(token: str) -> str:
    return f"Invalid numeric range in pattern token '{token}'."


def _too_large_message(token: str, max_atoms: int) -> str:
    return f"Pattern token '{token}' expands beyond {max_atoms} atoms."


def _duplicate_message(duplicates: Iterable[str], token: str) -> str:
    dupes = list(duplicates)
    preview = ", ".join(dupes[:5])
    extra = ""
    if len(dupes) > 5:
        extra = f" (+{len(dupes) - 5} more)"
    return f"Pattern token '{token}' expands to duplicate atoms: {preview}{extra}."


__all__ = [
    "MAX_EXPANSION_SIZE",
    "PATTERN_INVALID_RANGE",
    "PATTERN_EMPTY_ENUM",
    "PATTERN_EMPTY_SPLICE",
    "PATTERN_DUPLICATE_ATOM",
    "PATTERN_TOO_LARGE",
    "PATTERN_UNEXPANDED",
    "expand_endpoint",
    "expand_pattern",
]
