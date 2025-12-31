from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple, Union

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ..diagnostics import SourcePos, SourceSpan

PathSegment = Union[str, int]
Path = Tuple[PathSegment, ...]


@dataclass(frozen=True)
class Locatable:
    file: str
    start_line: Optional[int]
    start_col: Optional[int]
    end_line: Optional[int]
    end_col: Optional[int]

    def to_source_span(self) -> Optional[SourceSpan]:
        if (
            self.start_line is None
            or self.start_col is None
            or self.end_line is None
            or self.end_col is None
        ):
            return None
        return SourceSpan(
            file=self.file,
            start=SourcePos(self.start_line, self.start_col),
            end=SourcePos(self.end_line, self.end_col),
        )


class LocationIndex:
    def __init__(self, file_label: str) -> None:
        self.file_label = file_label
        self._value_locations: Dict[Path, Locatable] = {}
        self._key_locations: Dict[Path, Locatable] = {}

    @classmethod
    def from_yaml(cls, data: Any, file_label: str) -> "LocationIndex":
        index = cls(file_label)
        index._index_node(data, ())
        return index

    def lookup(self, path: Iterable[PathSegment], *, prefer_key: bool = False) -> Optional[Locatable]:
        key = tuple(path)
        if prefer_key:
            return self._key_locations.get(key) or self._value_locations.get(key)
        return self._value_locations.get(key) or self._key_locations.get(key)

    def lookup_with_fallback(
        self, path: Iterable[PathSegment], *, prefer_key: bool = False
    ) -> Optional[Locatable]:
        key = tuple(path)
        for idx in range(len(key), -1, -1):
            loc = self.lookup(key[:idx], prefer_key=prefer_key)
            if loc is not None:
                return loc
        return None

    def _index_node(self, node: Any, path: Path) -> None:
        node_loc = _loc_from_node(node, self.file_label)
        if node_loc is not None:
            self._value_locations[path] = node_loc

        if isinstance(node, (CommentedMap, dict)):
            for key, value in node.items():
                key_path = path + (key,)
                key_loc = _loc_from_map_key(node, key, self.file_label)
                if key_loc is not None:
                    self._key_locations[key_path] = key_loc
                value_loc = _loc_from_map_value(node, key, value, self.file_label)
                if value_loc is not None:
                    self._value_locations[key_path] = value_loc
                self._index_node(value, key_path)
            return

        if isinstance(node, (CommentedSeq, list)):
            for index, value in enumerate(node):
                item_path = path + (index,)
                item_loc = _loc_from_seq_item(node, index, value, self.file_label)
                if item_loc is not None:
                    self._value_locations[item_path] = item_loc
                self._index_node(value, item_path)


def to_plain(node: Any) -> Any:
    if isinstance(node, CommentedMap):
        return {key: to_plain(value) for key, value in node.items()}
    if isinstance(node, CommentedSeq):
        return [to_plain(value) for value in node]
    if isinstance(node, dict):
        return {key: to_plain(value) for key, value in node.items()}
    if isinstance(node, list):
        return [to_plain(value) for value in node]
    return node


def _loc_from_map_key(parent: Any, key: Any, file_label: str) -> Optional[Locatable]:
    line_col = _safe_line_col(getattr(parent, "lc", None), "key", key)
    if line_col is None:
        return None
    return _loc_from_line_col(line_col, file_label, length=len(str(key)))


def _loc_from_map_value(parent: Any, key: Any, value: Any, file_label: str) -> Optional[Locatable]:
    line_col = _safe_line_col(getattr(parent, "lc", None), "value", key)
    if line_col is None:
        line_col = _node_line_col(value)
    if line_col is None:
        return None
    return _loc_from_line_col(line_col, file_label, length=_scalar_length(value))


def _loc_from_seq_item(
    parent: Any, index: int, value: Any, file_label: str
) -> Optional[Locatable]:
    line_col = _safe_line_col(getattr(parent, "lc", None), "item", index)
    if line_col is None:
        line_col = _node_line_col(value)
    if line_col is None:
        return None
    return _loc_from_line_col(line_col, file_label, length=_scalar_length(value))


def _loc_from_node(node: Any, file_label: str) -> Optional[Locatable]:
    line_col = _node_line_col(node)
    if line_col is None:
        return None
    return _loc_from_line_col(line_col, file_label, length=0)


def _node_line_col(node: Any) -> Optional[Tuple[int, int]]:
    lc = getattr(node, "lc", None)
    if lc is None:
        return None
    line = getattr(lc, "line", None)
    col = getattr(lc, "col", None)
    if line is None or col is None:
        return None
    return line, col


def _safe_line_col(lc: Any, method: str, key: Any) -> Optional[Tuple[int, int]]:
    if lc is None:
        return None
    try:
        line, col = getattr(lc, method)(key)
    except Exception:
        return None
    if line is None or col is None:
        return None
    return line, col


def _loc_from_line_col(line_col: Tuple[int, int], file_label: str, length: int) -> Locatable:
    line, col = line_col
    start_line = line + 1
    start_col = col + 1
    if length <= 0:
        end_line = start_line
        end_col = start_col
    else:
        end_line = start_line
        end_col = start_col + max(length - 1, 0)
    return Locatable(
        file=file_label,
        start_line=start_line,
        start_col=start_col,
        end_line=end_line,
        end_col=end_col,
    )


def _scalar_length(value: Any) -> int:
    if isinstance(value, (str, int, float, bool)):
        return len(str(value))
    return 0


__all__ = ["Locatable", "LocationIndex", "Path", "PathSegment", "to_plain"]
