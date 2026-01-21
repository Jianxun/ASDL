"""Generate Markdown documentation from ASDL sources."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from asdl.docs.markdown import MarkdownRenderError, render_markdown_from_file


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Markdown documentation from an ASDL source file."
    )
    parser.add_argument(
        "source",
        help="Path to the ASDL YAML file.",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output directory for generated Markdown.",
    )
    return parser.parse_args()


def _output_path(source: Path, out_dir: Path) -> Path:
    return out_dir / f"{source.stem}.md"


def main() -> int:
    args = _parse_args()
    source = Path(args.source)
    out_dir = Path(args.out)

    try:
        markdown = render_markdown_from_file(source)
    except MarkdownRenderError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = _output_path(source, out_dir)
    output_path.write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
