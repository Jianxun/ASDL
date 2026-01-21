"""Extract comment-based docstrings from ASDL YAML sources."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

DocPath = tuple[str, ...]


@dataclass(frozen=True)
class KeyDocstring:
    """Docstring attached to a mapping key."""

    path: DocPath
    block: Optional[str]
    inline: Optional[str]

    @property
    def text(self) -> str:
        """Return the combined docstring text."""
        if self.block and self.inline:
            return f"{self.block}\n\n{self.inline}"
        return self.block or self.inline or ""


@dataclass(frozen=True)
class SectionDocstring:
    """Docstring that groups a bundle of keys within a mapping."""

    path: DocPath
    title: str
    keys: tuple[str, ...]


@dataclass(frozen=True)
class DocstringIndex:
    """Structured docstrings extracted from an ASDL YAML document."""

    file_docstring: Optional[str]
    key_docstrings: dict[DocPath, KeyDocstring]
    sections: dict[DocPath, tuple[SectionDocstring, ...]]

    def key_docstring(self, path: DocPath) -> Optional[KeyDocstring]:
        """Look up a key docstring by its YAML path."""
        return self.key_docstrings.get(path)

    def section_docstrings(self, path: DocPath) -> tuple[SectionDocstring, ...]:
        """Return section docstrings for a mapping path."""
        return self.sections.get(path, ())


@dataclass(frozen=True)
class _KeyInfo:
    key: str
    pre_tokens: tuple[object, ...]
    block_comment: Optional[str]
    inline_comment: Optional[str]

    @property
    def has_pre_tokens(self) -> bool:
        return bool(self.pre_tokens)


def extract_docstrings_from_file(path: str | Path) -> DocstringIndex:
    """Load an ASDL file from disk and extract comment docstrings."""
    file_path = Path(path)
    content = file_path.read_text(encoding="utf-8")
    return extract_docstrings(content)


def extract_docstrings(yaml_content: str) -> DocstringIndex:
    """Extract comment-based docstrings from ASDL YAML content."""
    yaml = YAML(typ="rt")
    data = yaml.load(yaml_content)

    file_docstring = _extract_file_docstring(yaml_content)
    key_docstrings: dict[DocPath, KeyDocstring] = {}
    sections: dict[DocPath, tuple[SectionDocstring, ...]] = {}

    if isinstance(data, CommentedMap):
        _extract_map_docstrings(
            data,
            (),
            key_docstrings,
            sections,
            skip_first_key_comment=file_docstring is not None,
        )

    return DocstringIndex(
        file_docstring=file_docstring,
        key_docstrings=key_docstrings,
        sections=sections,
    )


def _extract_file_docstring(yaml_content: str) -> Optional[str]:
    lines = yaml_content.splitlines()
    index = 0
    while index < len(lines) and lines[index].strip() == "":
        index += 1
    if index >= len(lines) or not lines[index].lstrip().startswith("#"):
        return None

    comment_lines: list[str] = []
    while index < len(lines) and lines[index].lstrip().startswith("#"):
        comment_lines.append(lines[index])
        index += 1

    return _normalize_comment_lines(comment_lines)


def _extract_map_docstrings(
    mapping: CommentedMap,
    path: DocPath,
    key_docstrings: dict[DocPath, KeyDocstring],
    sections: dict[DocPath, tuple[SectionDocstring, ...]],
    *,
    skip_first_key_comment: bool,
) -> None:
    keys = list(mapping.keys())
    key_infos = [_build_key_info(mapping, key, idx, skip_first_key_comment) for idx, key in enumerate(keys)]

    section_starts: set[str] = set()
    section_entries: list[SectionDocstring] = []
    for idx, info in enumerate(key_infos):
        if info.block_comment is None:
            continue
        bundle_keys = [info.key]
        next_idx = idx + 1
        while next_idx < len(key_infos) and not key_infos[next_idx].has_pre_tokens:
            bundle_keys.append(key_infos[next_idx].key)
            next_idx += 1
        if len(bundle_keys) >= 2:
            section_entries.append(
                SectionDocstring(
                    path=path,
                    title=info.block_comment,
                    keys=tuple(bundle_keys),
                )
            )
            section_starts.add(info.key)

    if section_entries:
        sections[path] = tuple(section_entries)

    for info in key_infos:
        block = None if info.key in section_starts else info.block_comment
        if block is None and info.inline_comment is None:
            continue
        key_path = path + (info.key,)
        key_docstrings[key_path] = KeyDocstring(
            path=key_path,
            block=block,
            inline=info.inline_comment,
        )

    for key in keys:
        value = mapping.get(key)
        if isinstance(value, CommentedMap):
            _extract_map_docstrings(
                value,
                path + (key,),
                key_docstrings,
                sections,
                skip_first_key_comment=False,
            )


def _build_key_info(
    mapping: CommentedMap,
    key: str,
    index: int,
    skip_first_key_comment: bool,
) -> _KeyInfo:
    pre_tokens: list[object] = []
    if index == 0 and not skip_first_key_comment:
        pre_tokens.extend(_mapping_comment_tokens(mapping))
    item = mapping.ca.items.get(key)
    if item and item[1]:
        pre_tokens.extend(item[1])
    key_line = _key_line(mapping, key)
    block_comment = _block_comment_from_tokens(pre_tokens, key_line)
    inline_comment = _inline_comment_from_item(item)

    return _KeyInfo(
        key=key,
        pre_tokens=tuple(pre_tokens),
        block_comment=block_comment,
        inline_comment=inline_comment,
    )


def _mapping_comment_tokens(mapping: CommentedMap) -> Iterable[object]:
    comment = getattr(mapping, "ca", None)
    if comment is None or comment.comment is None:
        return []
    tokens = comment.comment[1]
    return tokens or []


def _block_comment_from_tokens(tokens: Iterable[object], key_line: Optional[int]) -> Optional[str]:
    comment_tokens = [tok for tok in tokens if _is_comment_token(tok)]
    if not comment_tokens:
        return None

    last_line = _last_comment_line(comment_tokens)
    if key_line is not None and last_line is not None and key_line - last_line != 1:
        return None

    lines: list[str] = []
    for token in comment_tokens:
        value = getattr(token, "value", "")
        for line in str(value).splitlines():
            if line.strip() == "":
                continue
            if line.lstrip().startswith("#"):
                lines.append(line)
    return _normalize_comment_lines(lines)


def _inline_comment_from_item(item: Optional[list[object]]) -> Optional[str]:
    if not item or len(item) < 3 or item[2] is None:
        return None
    tokens = item[2] if isinstance(item[2], list) else [item[2]]

    lines: list[str] = []
    for token in tokens:
        value = getattr(token, "value", "")
        if not value:
            continue
        line = str(value).splitlines()[0]
        if line.strip() == "":
            continue
        lines.append(line)

    return _normalize_comment_lines(lines)


def _normalize_comment_lines(lines: Iterable[str]) -> Optional[str]:
    normalized: list[str] = []
    for line in lines:
        stripped = line.lstrip()
        if not stripped.startswith("#"):
            continue
        text = stripped[1:]
        if text.startswith(" "):
            text = text[1:]
        normalized.append(text.rstrip())

    while normalized and normalized[0].strip() == "":
        normalized.pop(0)
    while normalized and normalized[-1].strip() == "":
        normalized.pop()

    if not normalized:
        return None
    return "\n".join(normalized)


def _is_comment_token(token: object) -> bool:
    value = getattr(token, "value", None)
    if value is None:
        return False
    return str(value).lstrip().startswith("#")


def _last_comment_line(tokens: Iterable[object]) -> Optional[int]:
    last_line = None
    for token in tokens:
        line = getattr(token, "line", None)
        if line is None:
            continue
        last_line = line
    return last_line


def _key_line(mapping: CommentedMap, key: str) -> Optional[int]:
    lc = getattr(mapping, "lc", None)
    if lc is None:
        return None
    try:
        line_col = lc.key(key)
    except Exception:
        return None
    if not line_col:
        return None
    return line_col[0]


__all__ = [
    "DocPath",
    "DocstringIndex",
    "KeyDocstring",
    "SectionDocstring",
    "extract_docstrings",
    "extract_docstrings_from_file",
]
