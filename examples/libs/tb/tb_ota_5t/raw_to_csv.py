#!/usr/bin/env python3
"""Convert Xyce RAW (binary) output to CSV and HDF5."""

from __future__ import annotations

import argparse
import csv
import re
import struct
import sys
from pathlib import Path


HEADER_INT_PATTERNS = {
    "No. Variables": re.compile(rb"^No\. Variables:\s*(\d+)\s*$", re.MULTILINE),
    "No. Points": re.compile(rb"^No\. Points:\s*(\d+)\s*$", re.MULTILINE),
}


VAR_LINE_RE = re.compile(rb"^\s*\d+\s+(\S+)\s+(\S+)\s*$")
VECTOR_NAME_RE = re.compile(r"^([A-Za-z_]\w*)\((.*)\)$")


def _parse_header(raw_bytes: bytes) -> tuple[list[str], int, int, int]:
    marker = b"\nBinary:\n"
    start = raw_bytes.find(marker)
    if start < 0:
        raise ValueError("RAW file missing 'Binary:' marker")

    header_bytes = raw_bytes[:start]
    data_start = start + len(marker)

    values: dict[str, int] = {}
    for key, pattern in HEADER_INT_PATTERNS.items():
        m = pattern.search(header_bytes)
        if not m:
            raise ValueError(f"RAW header missing '{key}'")
        values[key] = int(m.group(1))

    var_count = values["No. Variables"]
    point_count = values["No. Points"]

    lines = header_bytes.splitlines()
    var_section_idx = None
    for i, line in enumerate(lines):
        if line.strip() == b"Variables:":
            var_section_idx = i
            break
    if var_section_idx is None:
        raise ValueError("RAW header missing 'Variables:' section")

    var_names: list[str] = []
    for line in lines[var_section_idx + 1 :]:
        m = VAR_LINE_RE.match(line)
        if not m:
            continue
        var_names.append(m.group(1).decode("utf-8", errors="replace"))

    if len(var_names) != var_count:
        raise ValueError(
            f"Variable count mismatch: header says {var_count}, parsed {len(var_names)}"
        )

    return var_names, var_count, point_count, data_start


def _decode_payload(
    payload: bytes,
    var_count: int,
    point_count: int,
) -> list[tuple[float, ...]]:
    total_vals = var_count * point_count
    expected_len = total_vals * 8
    if len(payload) < expected_len:
        raise ValueError(
            f"Payload too short: expected {expected_len} bytes, got {len(payload)}"
        )

    payload = payload[:expected_len]

    # Xyce RAW binary is double-precision. Try little-endian first.
    little = struct.unpack("<" + "d" * total_vals, payload)

    if point_count >= 2 and not (little[0] <= little[var_count]):
        # Fallback for unusual big-endian cases.
        big = struct.unpack(">" + "d" * total_vals, payload)
        data = big
    else:
        data = little

    rows: list[tuple[float, ...]] = []
    for i in range(point_count):
        offset = i * var_count
        rows.append(tuple(data[offset : offset + var_count]))
    return rows


def _load_raw_vectors(input_path: Path) -> tuple[list[str], list[tuple[float, ...]]]:
    raw_bytes = input_path.read_bytes()
    names, var_count, point_count, data_start = _parse_header(raw_bytes)
    rows = _decode_payload(raw_bytes[data_start:], var_count, point_count)
    return names, rows


def convert_raw_to_csv(input_path: Path, output_path: Path, drop_sweep: bool) -> None:
    names, rows = _load_raw_vectors(input_path)

    col_start = 1 if drop_sweep else 0
    out_names = names[col_start:]

    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(out_names)
        for row in rows:
            writer.writerow([f"{val:.8e}" for val in row[col_start:]])


def convert_raw_to_hdf5(input_path: Path, output_path: Path) -> None:
    try:
        import h5py
        import numpy as np
    except ImportError as exc:  # pragma: no cover - runtime dependency guard
        raise RuntimeError(
            "HDF5 export requires 'h5py' (and numpy). Install with: pip install h5py"
        ) from exc

    names, rows = _load_raw_vectors(input_path)
    matrix = np.asarray(rows, dtype=np.float64)

    def escape_hdf5_component(name: str) -> str:
        # "/" is a path separator in HDF5.
        return name.replace("/", "%2F")

    def xyce_name_to_hdf5_path(vector_name: str) -> tuple[list[str], str]:
        """
        Convert Xyce vector names to hierarchical HDF5 paths.
        Examples:
          V(OUT)        -> signals/V(OUT)
          V(XOTA:D)     -> signals/XOTA/V(D)
          V(XA:XB:N1)   -> signals/XA/XB/V(N1)
          sweep         -> signals/raw/sweep
        """
        match = VECTOR_NAME_RE.match(vector_name)
        if not match:
            return ["raw"], escape_hdf5_component(vector_name)

        quantity, target = match.groups()
        target = target.strip()
        quantity = quantity.strip()

        if ":" not in target:
            return [], escape_hdf5_component(f"{quantity}({target})")

        parts = [p.strip() for p in target.split(":") if p.strip()]
        if not parts:
            return [], escape_hdf5_component(f"{quantity}({target})")

        inst_path = [escape_hdf5_component(p) for p in parts[:-1]] or ["top"]
        leaf = escape_hdf5_component(parts[-1])
        dataset_name = escape_hdf5_component(f"{quantity}({leaf})")
        return inst_path, dataset_name

    def unique_dataset_name(group, base: str) -> str:
        if base not in group:
            return base
        i = 1
        while f"{base}__{i}" in group:
            i += 1
        return f"{base}__{i}"

    with h5py.File(output_path, "w") as h5:
        h5.attrs["source_file"] = str(input_path)
        h5.attrs["format"] = "xyce_raw"
        h5.attrs["num_points"] = matrix.shape[0]
        h5.attrs["num_variables"] = matrix.shape[1]
        h5.attrs["indep_var_index"] = 0
        h5.attrs["indep_var_name"] = names[0] if names else ""

        h5.create_dataset(
            "vectors",
            data=matrix,
            compression="gzip",
            compression_opts=4,
        )
        h5.create_dataset("vector_names", data=np.asarray(names, dtype="S"))

        indep_var_grp = h5.create_group("indep_var")
        signals_grp = h5.create_group("signals")
        src = h5py.VirtualSource(h5["vectors"])
        if names:
            indep_name = unique_dataset_name(indep_var_grp, escape_hdf5_component(names[0]))
            indep_layout = h5py.VirtualLayout(shape=(matrix.shape[0],), dtype=np.float64)
            indep_layout[:] = src[:, 0]
            indep_ds = indep_var_grp.create_virtual_dataset(indep_name, indep_layout)
            indep_ds.attrs["original_name"] = names[0]
            indep_ds.attrs["index"] = 0

        for idx, name in enumerate(names[1:], start=1):
            group_parts, dataset_name = xyce_name_to_hdf5_path(name)

            current_group = signals_grp
            for part in group_parts:
                current_group = current_group.require_group(part)

            dataset_name = unique_dataset_name(current_group, dataset_name)
            layout = h5py.VirtualLayout(shape=(matrix.shape[0],), dtype=np.float64)
            layout[:] = src[:, idx]
            dset = current_group.create_virtual_dataset(dataset_name, layout)
            dset.attrs["original_name"] = name
            dset.attrs["index"] = idx


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert Xyce RAW binary to CSV/HDF5")
    parser.add_argument("input", type=Path, help="Input .raw file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output CSV path (default: <input>.csv)",
    )
    parser.add_argument(
        "--drop-sweep",
        action="store_true",
        help="Drop first RAW variable (typically sweep) from output CSV",
    )
    parser.add_argument(
        "--hdf5-out",
        type=Path,
        default=None,
        help="Optional HDF5 output path (default: <input>.h5 when flag is present without value)",
        nargs="?",
        const=Path("__AUTO__"),
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    out = args.output or args.input.with_suffix(args.input.suffix + ".csv")
    hdf5_out = args.hdf5_out
    if hdf5_out == Path("__AUTO__"):
        hdf5_out = args.input.with_suffix(args.input.suffix + ".h5")

    try:
        convert_raw_to_csv(args.input, out, drop_sweep=args.drop_sweep)
        if hdf5_out is not None:
            convert_raw_to_hdf5(args.input, hdf5_out)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"wrote {out}")
    if hdf5_out is not None:
        print(f"wrote {hdf5_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
