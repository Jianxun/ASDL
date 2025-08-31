#!/usr/bin/env python3
"""
Generate ASDL schema artifacts from Pydantic models.

Outputs:
- schema.json: JSON Schema for the ASDL YAML document
- schema.txt:  Human-readable overview (like ams-compose)

Usage:
  python -m ASDL.scripts.generate_schema [--out DIR]
  or run directly: ./generate_schema.py --out DIR
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from asdl.data_structures import build_json_schema, render_text_schema


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ASDL schema artifacts")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Output directory (defaults to this scripts directory)",
    )
    args = parser.parse_args()

    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    # JSON Schema
    json_schema = build_json_schema()
    (out_dir / "schema.json").write_text(
        json.dumps(json_schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Human-readable text schema
    txt_schema = render_text_schema()
    (out_dir / "schema.txt").write_text(txt_schema, encoding="utf-8")

    print(f"Wrote: {out_dir / 'schema.json'}")
    print(f"Wrote: {out_dir / 'schema.txt'}")


if __name__ == "__main__":
    main()


