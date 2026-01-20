"""Tagged-axis analysis helpers for GraphIR net lowering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from asdl.ast import Locatable, ModuleDecl, PatternDecl
from asdl.diagnostics import Diagnostic, format_code
from asdl.ir.converters.ast_to_graphir_utils import diagnostic
from asdl.ir.patterns import AtomizedEndpoint, AtomizedPattern, atomize_pattern
from asdl.ir.patterns.parts import PatternPart

AXIS_ID_DUPLICATE = format_code("IR", 14)
AXIS_ID_MISMATCH = format_code("IR", 15)
AXIS_LENGTH_MISMATCH = format_code("IR", 16)


@dataclass(frozen=True)
class _AxisToken:
    """Metadata for a tagged pattern axis token.

    Attributes:
        axis_id: Axis identifier (tag or pattern name).
        name: Named pattern identifier for the axis.
        length: Expansion length for the pattern group.
        index_by_value: Mapping from pattern part value to ordinal index.
        loc: Optional source location for the token.
        token: Raw token text from the source expression.
    """

    axis_id: str
    name: str
    length: int
    index_by_value: Dict[PatternPart, int]
    loc: Optional[Locatable]
    token: str


@dataclass(frozen=True)
class _AxisMetadata:
    """Axis metadata extracted from a pattern expression.

    Attributes:
        axis_ids: Ordered axis identifiers from the expression.
        axis_tokens: Ordered axis token metadata.
        axis_by_id: Mapping from axis_id to axis token metadata.
        has_unnamed: Whether the expression contains unnamed pattern groups.
        has_splice: Whether the expression uses splice delimiters.
        had_error: Whether axis analysis emitted errors.
    """

    axis_ids: List[str]
    axis_tokens: List[_AxisToken]
    axis_by_id: Dict[str, _AxisToken]
    has_unnamed: bool
    has_splice: bool
    had_error: bool


def _pattern_expr_value(pattern_value: str | PatternDecl) -> str:
    """Return the expression string for a named pattern entry.

    Args:
        pattern_value: Raw pattern value from the module patterns map.

    Returns:
        Pattern expression string.
    """
    if isinstance(pattern_value, PatternDecl):
        return pattern_value.expr
    return pattern_value


def _collect_named_pattern_axes(
    module: ModuleDecl,
    *,
    diagnostics: List[Diagnostic],
) -> Tuple[
    Dict[str, str],
    Dict[str, List[str]],
    Dict[str, int],
    Dict[str, Dict[PatternPart, int]],
    bool,
]:
    """Collect axis metadata for named patterns in a module.

    Args:
        module: Module declaration containing optional patterns.
        diagnostics: Diagnostic collection to append errors to.

    Returns:
        Tuple of (expr_by_name, names_by_expr, length_by_name, index_by_name, had_error).
    """
    expr_by_name: Dict[str, str] = {}
    names_by_expr: Dict[str, List[str]] = {}
    length_by_name: Dict[str, int] = {}
    index_by_name: Dict[str, Dict[PatternPart, int]] = {}
    had_error = False

    for pattern_name, pattern_value in (module.patterns or {}).items():
        expr = _pattern_expr_value(pattern_value)
        expr_by_name[pattern_name] = expr
        names_by_expr.setdefault(expr, []).append(pattern_name)
        atoms, atom_diags = atomize_pattern(expr)
        if atoms is None:
            diagnostics.extend(atom_diags)
            had_error = True
            continue
        length_by_name[pattern_name] = len(atoms)
        index_map: Dict[PatternPart, int] = {}
        for idx, atom in enumerate(atoms):
            if not atom.pattern_parts:
                continue
            index_map[atom.pattern_parts[0]] = idx
        index_by_name[pattern_name] = index_map

    return expr_by_name, names_by_expr, length_by_name, index_by_name, had_error


def _load_expression_text(
    expression: str, loc: Optional[Locatable]
) -> Tuple[str, bool]:
    """Load raw expression text from the source span when available.

    Args:
        expression: Fallback expression string.
        loc: Optional source location.

    Returns:
        Tuple of (expression_text, is_source_text).
    """
    if (
        loc is None
        or loc.file is None
        or loc.start_line is None
        or loc.start_col is None
        or loc.end_line is None
        or loc.end_col is None
    ):
        return expression, False
    if loc.start_line != loc.end_line:
        return expression, False
    path = Path(loc.file)
    if not path.is_file():
        return expression, False
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return expression, False
    line_index = loc.start_line - 1
    if line_index < 0 or line_index >= len(lines):
        return expression, False
    line = lines[line_index]
    start = max(loc.start_col - 1, 0)
    end = max(start, loc.end_col - 1)
    if start > len(line):
        return expression, False
    end = min(len(line), end)
    return line[start:end], True


def _scan_group_tokens(
    expression: str,
) -> Tuple[List[Tuple[int, int, str, Optional[str]]], bool]:
    """Scan expression text for pattern group tokens.

    Args:
        expression: Expression text to scan.

    Returns:
        Tuple of (token tuples, has_splice) where each token tuple contains
        (start, end, token_text, named_pattern_name).
    """
    tokens: List[Tuple[int, int, str, Optional[str]]] = []
    has_splice = False
    index = 0
    while index < len(expression):
        char = expression[index]
        if char == "<":
            close = expression.find(">", index + 1)
            if close == -1:
                break
            token = expression[index : close + 1]
            name = token[2:-1] if token.startswith("<@") else None
            tokens.append((index, close + 1, token, name))
            index = close + 1
            continue
        if char == ";":
            has_splice = True
        index += 1
    return tokens, has_splice


def _token_loc(
    *,
    loc: Optional[Locatable],
    start: int,
    end: int,
    use_loc: bool,
) -> Optional[Locatable]:
    """Create a locatable span for a token inside an expression.

    Args:
        loc: Base location for the full expression.
        start: Start offset within the expression string.
        end: End offset within the expression string.
        use_loc: Whether token spans are trusted for this expression text.

    Returns:
        Locatable span for the token or None.
    """
    if not use_loc or loc is None:
        return None
    if (
        loc.start_line is None
        or loc.start_col is None
        or loc.end_line is None
        or loc.end_col is None
    ):
        return None
    start_col = loc.start_col + start
    end_col = loc.start_col + end
    return Locatable(
        file=loc.file,
        start_line=loc.start_line,
        start_col=start_col,
        end_line=loc.start_line,
        end_col=end_col,
    )


def _axis_token_from_name(
    *,
    name: str,
    token: str,
    token_loc: Optional[Locatable],
    module: ModuleDecl,
    length_by_name: Dict[str, int],
    index_by_name: Dict[str, Dict[PatternPart, int]],
    diagnostics: List[Diagnostic],
    module_name: str,
    context: str,
) -> Optional[_AxisToken]:
    """Build axis token metadata for a named pattern reference.

    Args:
        name: Named pattern identifier.
        token: Raw token string from the expression.
        token_loc: Optional token span location.
        module: Module declaration for axis_id resolution.
        length_by_name: Mapping of pattern name to axis length.
        index_by_name: Mapping of pattern name to part index maps.
        diagnostics: Diagnostic collection to append errors to.
        module_name: Name of the module for diagnostics.
        context: Expression context label.

    Returns:
        Axis token metadata or None on error.
    """
    axis_id = module.pattern_axis_id(name)
    if axis_id is None:
        diagnostics.append(
            diagnostic(
                AXIS_ID_MISMATCH,
                (
                    f"Named pattern '{name}' in {context} expression has no axis "
                    f"metadata in module '{module_name}'."
                ),
                token_loc or module.pattern_axis_id_loc(name),
            )
        )
        return None
    length = length_by_name.get(name)
    index_map = index_by_name.get(name)
    if length is None or index_map is None:
        diagnostics.append(
            diagnostic(
                AXIS_ID_MISMATCH,
                (
                    f"Named pattern '{name}' in {context} expression is missing "
                    f"axis metadata in module '{module_name}'."
                ),
                token_loc or module.pattern_axis_id_loc(name),
            )
        )
        return None
    return _AxisToken(
        axis_id=axis_id,
        name=name,
        length=length,
        index_by_value=index_map,
        loc=token_loc or module.pattern_axis_id_loc(name),
        token=token,
    )


def _axis_metadata(
    *,
    expression: str,
    loc: Optional[Locatable],
    module: ModuleDecl,
    names_by_expr: Dict[str, List[str]],
    length_by_name: Dict[str, int],
    index_by_name: Dict[str, Dict[PatternPart, int]],
    diagnostics: List[Diagnostic],
    module_name: str,
    context: str,
) -> _AxisMetadata:
    """Extract tagged-axis metadata from a pattern expression.

    Args:
        expression: Expression string after named pattern expansion.
        loc: Optional source location for the expression.
        module: Module declaration providing named pattern metadata.
        names_by_expr: Map of pattern expression strings to pattern names.
        length_by_name: Map of pattern name to axis length.
        index_by_name: Map of pattern name to part index mapping.
        diagnostics: Diagnostic collection to append errors to.
        module_name: Name of the module for diagnostics.
        context: Expression context label.

    Returns:
        Axis metadata summary for the expression.
    """
    text, is_source_text = _load_expression_text(expression, loc)
    tokens, has_splice = _scan_group_tokens(text)
    contains_named = "<@" in text
    use_loc = is_source_text
    axis_tokens: List[_AxisToken] = []
    has_unnamed = False
    had_error = False

    for start, end, token, name in tokens:
        token_loc = _token_loc(loc=loc, start=start, end=end, use_loc=use_loc)
        if name is None:
            if contains_named or is_source_text:
                has_unnamed = True
                continue
            matching_names = names_by_expr.get(token)
            if not matching_names:
                has_unnamed = True
                continue
            if len(matching_names) > 1:
                diagnostics.append(
                    diagnostic(
                        AXIS_ID_MISMATCH,
                        (
                            f"Pattern group '{token}' in {context} expression matches "
                            f"multiple named patterns in module '{module_name}'."
                        ),
                        token_loc,
                    )
                )
                had_error = True
                continue
            name = matching_names[0]

        axis_token = _axis_token_from_name(
            name=name,
            token=token,
            token_loc=token_loc,
            module=module,
            length_by_name=length_by_name,
            index_by_name=index_by_name,
            diagnostics=diagnostics,
            module_name=module_name,
            context=context,
        )
        if axis_token is None:
            had_error = True
            continue
        axis_tokens.append(axis_token)

    axis_by_id: Dict[str, _AxisToken] = {}
    axis_ids: List[str] = []
    for axis_token in axis_tokens:
        axis_ids.append(axis_token.axis_id)
        if axis_token.axis_id in axis_by_id:
            diagnostics.append(
                diagnostic(
                    AXIS_ID_DUPLICATE,
                    (
                        f"Duplicate axis id '{axis_token.axis_id}' in {context} "
                        f"expression '{expression}' in module '{module_name}'."
                    ),
                    axis_token.loc or loc,
                )
            )
            had_error = True
            continue
        axis_by_id[axis_token.axis_id] = axis_token

    return _AxisMetadata(
        axis_ids=axis_ids,
        axis_tokens=axis_tokens,
        axis_by_id=axis_by_id,
        has_unnamed=has_unnamed,
        has_splice=has_splice,
        had_error=had_error,
    )


def _axis_subsequence_positions(
    net_axes: List[str],
    endpoint_axes: List[str],
) -> Tuple[Optional[List[int]], Optional[str]]:
    """Find endpoint indices that align to net axes as a subsequence.

    Args:
        net_axes: Ordered axis ids from the net expression.
        endpoint_axes: Ordered axis ids from the endpoint expression.

    Returns:
        Tuple of (positions, missing_axis_id). positions is None when matching fails.
    """
    positions: List[int] = []
    cursor = 0
    for axis_id in net_axes:
        try:
            index = endpoint_axes.index(axis_id, cursor)
        except ValueError:
            return None, axis_id
        positions.append(index)
        cursor = index + 1
    return positions, None


def _axis_broadcast_mapping(
    *,
    net_atoms: List[AtomizedPattern],
    net_axis: _AxisMetadata,
    endpoint_atoms: List[AtomizedEndpoint],
    endpoint_axis: _AxisMetadata,
    module_name: str,
    net_expr: str,
    endpoint_expr: str,
    net_loc: Optional[Locatable],
    endpoint_loc: Optional[Locatable],
    diagnostics: List[Diagnostic],
) -> Tuple[Optional[List[int]], bool, bool]:
    """Compute axis-aware endpoint bindings for tagged-axis broadcast.

    Args:
        net_atoms: Atomized net pattern expansion.
        net_axis: Axis metadata for the net expression.
        endpoint_atoms: Atomized endpoint expansion.
        endpoint_axis: Axis metadata for the endpoint expression.
        module_name: Name of the module for diagnostics.
        net_expr: Net expression string.
        endpoint_expr: Endpoint expression string.
        net_loc: Optional net expression location.
        endpoint_loc: Optional endpoint expression location.
        diagnostics: Diagnostic collection to append errors to.

    Returns:
        Tuple of (mapping, axis_used, had_error). mapping is a list of net indices for
        each endpoint atom when axis_used is true and had_error is false.
    """
    if len(net_atoms) <= 1:
        return None, False, False
    if (
        net_axis.had_error
        or endpoint_axis.had_error
        or net_axis.has_splice
        or endpoint_axis.has_splice
        or net_axis.has_unnamed
        or endpoint_axis.has_unnamed
        or not net_axis.axis_ids
        or not endpoint_axis.axis_ids
    ):
        return None, False, False

    positions, missing_axis = _axis_subsequence_positions(
        net_axis.axis_ids, endpoint_axis.axis_ids
    )
    if positions is None:
        missing_token = net_axis.axis_by_id.get(missing_axis or "")
        diagnostics.append(
            diagnostic(
                AXIS_ID_MISMATCH,
                (
                    f"Endpoint axis order does not include axis '{missing_axis}' "
                    f"from net '{net_expr}' in module '{module_name}'."
                ),
                (missing_token.loc if missing_token is not None else net_loc) or endpoint_loc,
            )
        )
        return None, True, True

    for axis_id in net_axis.axis_ids:
        net_token = net_axis.axis_by_id.get(axis_id)
        endpoint_token = endpoint_axis.axis_by_id.get(axis_id)
        if net_token is None or endpoint_token is None:
            diagnostics.append(
                diagnostic(
                    AXIS_ID_MISMATCH,
                    (
                        f"Axis '{axis_id}' is missing from endpoint '{endpoint_expr}' "
                        f"in module '{module_name}'."
                    ),
                    endpoint_loc or net_loc,
                )
            )
            return None, True, True
        if net_token.length != endpoint_token.length:
            diagnostics.append(
                diagnostic(
                    AXIS_LENGTH_MISMATCH,
                    (
                        f"Axis '{axis_id}' length mismatch between net '{net_expr}' "
                        f"({net_token.length}) and endpoint '{endpoint_expr}' "
                        f"({endpoint_token.length}) in module '{module_name}'."
                    ),
                    net_token.loc or endpoint_token.loc or net_loc or endpoint_loc,
                )
            )
            return None, True, True

    expected_parts = len(net_axis.axis_ids)
    net_coord_map: Dict[Tuple[int, ...], int] = {}
    for index, net_atom in enumerate(net_atoms):
        if len(net_atom.pattern_parts) != expected_parts:
            diagnostics.append(
                diagnostic(
                    AXIS_ID_MISMATCH,
                    (
                        f"Net '{net_expr}' axis metadata does not align with its "
                        f"pattern expansion in module '{module_name}'."
                    ),
                    net_loc,
                )
            )
            return None, True, True
        coords: List[int] = []
        for axis_id, part_value in zip(net_axis.axis_ids, net_atom.pattern_parts):
            axis_token = net_axis.axis_by_id[axis_id]
            part_index = axis_token.index_by_value.get(part_value)
            if part_index is None:
                diagnostics.append(
                    diagnostic(
                        AXIS_ID_MISMATCH,
                        (
                            f"Axis '{axis_id}' values for net '{net_expr}' do not "
                            f"match named pattern '{axis_token.name}' in module "
                            f"'{module_name}'."
                        ),
                        axis_token.loc or net_loc,
                    )
                )
                return None, True, True
            coords.append(part_index)
        net_coord_map[tuple(coords)] = index

    expected_endpoint_parts = len(endpoint_axis.axis_ids)
    mapping: List[int] = []
    for endpoint_atom in endpoint_atoms:
        if len(endpoint_atom.pattern_parts) != expected_endpoint_parts:
            diagnostics.append(
                diagnostic(
                    AXIS_ID_MISMATCH,
                    (
                        f"Endpoint '{endpoint_expr}' axis metadata does not align "
                        f"with its pattern expansion in module '{module_name}'."
                    ),
                    endpoint_loc or net_loc,
                )
            )
            return None, True, True
        coords = []
        for axis_id, endpoint_index in zip(net_axis.axis_ids, positions):
            axis_token = endpoint_axis.axis_by_id[axis_id]
            part_value = endpoint_atom.pattern_parts[endpoint_index]
            part_index = axis_token.index_by_value.get(part_value)
            if part_index is None:
                diagnostics.append(
                    diagnostic(
                        AXIS_ID_MISMATCH,
                        (
                            f"Axis '{axis_id}' values for endpoint '{endpoint_expr}' "
                            f"do not match named pattern '{axis_token.name}' in module "
                            f"'{module_name}'."
                        ),
                        axis_token.loc or endpoint_loc,
                    )
                )
                return None, True, True
            coords.append(part_index)
        net_index = net_coord_map.get(tuple(coords))
        if net_index is None:
            diagnostics.append(
                diagnostic(
                    AXIS_ID_MISMATCH,
                    (
                        f"Endpoint '{endpoint_expr}' axes do not align with net "
                        f"'{net_expr}' in module '{module_name}'."
                    ),
                    endpoint_loc or net_loc,
                )
            )
            return None, True, True
        mapping.append(net_index)

    return mapping, True, False
