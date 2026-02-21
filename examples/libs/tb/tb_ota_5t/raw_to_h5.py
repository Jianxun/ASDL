#!/usr/bin/env python3
"""Convert Xyce RAW (real/complex) to HDF5 with hierarchical signal views."""

from __future__ import annotations

import argparse
import re
import struct
import sys
from pathlib import Path


HEADER_INT_PATTERNS = {
    "No. Variables": re.compile(rb"^No\. Variables:\s*(\d+)\s*$", re.MULTILINE),
    "No. Points": re.compile(rb"^No\. Points:\s*(\d+)\s*$", re.MULTILINE),
}

FLAG_RE = re.compile(rb"^Flags:\s*(.+?)\s*$", re.MULTILINE)
VAR_LINE_RE = re.compile(rb"^\s*\d+\s+(\S+)\s+(\S+)\s*$")
VECTOR_NAME_RE = re.compile(r"^([A-Za-z_]\w*)\((.*)\)$")


def _parse_header(raw_bytes: bytes) -> tuple[list[str], list[str], int, int, str, int]:
    marker = b"\nBinary:\n"
    start = raw_bytes.find(marker)
    if start < 0:
        raise ValueError("RAW file missing 'Binary:' marker")

    header_bytes = raw_bytes[:start]
    data_start = start + len(marker)

    values: dict[str, int] = {}
    for key, pattern in HEADER_INT_PATTERNS.items():
        match = pattern.search(header_bytes)
        if not match:
            raise ValueError(f"RAW header missing '{key}'")
        values[key] = int(match.group(1))

    flag_match = FLAG_RE.search(header_bytes)
    if not flag_match:
        raise ValueError("RAW header missing 'Flags'")
    flags = flag_match.group(1).decode("utf-8", errors="replace").strip().lower()

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
    var_kinds: list[str] = []
    for line in lines[var_section_idx + 1 :]:
        match = VAR_LINE_RE.match(line)
        if not match:
            continue
        var_names.append(match.group(1).decode("utf-8", errors="replace"))
        var_kinds.append(match.group(2).decode("utf-8", errors="replace"))

    if len(var_names) != var_count:
        raise ValueError(
            f"Variable count mismatch: header says {var_count}, parsed {len(var_names)}"
        )

    return var_names, var_kinds, var_count, point_count, flags, data_start


def _decode_real_matrix(payload: bytes, var_count: int, point_count: int):
    import numpy as np

    total_vals = var_count * point_count
    expected_len = total_vals * 8
    if len(payload) < expected_len:
        raise ValueError(
            f"Payload too short for real data: expected {expected_len} bytes, got {len(payload)}"
        )
    payload = payload[:expected_len]

    little = np.frombuffer(payload, dtype="<f8", count=total_vals).reshape(point_count, var_count)
    big = np.frombuffer(payload, dtype=">f8", count=total_vals).reshape(point_count, var_count)

    # Prefer the decode where independent variable (col 0) appears non-decreasing.
    little_monotonic = bool(np.all(np.diff(little[:, 0]) >= 0))
    big_monotonic = bool(np.all(np.diff(big[:, 0]) >= 0))
    if little_monotonic and not big_monotonic:
        return little.astype(np.float64)
    if big_monotonic and not little_monotonic:
        return big.astype(np.float64)
    return little.astype(np.float64)


def _decode_complex_matrix(payload: bytes, var_count: int, point_count: int):
    import numpy as np

    total_vals = var_count * point_count
    expected_len = total_vals * 16
    if len(payload) < expected_len:
        raise ValueError(
            f"Payload too short for complex data: expected {expected_len} bytes, got {len(payload)}"
        )
    payload = payload[:expected_len]

    def _to_complex(arr: "np.ndarray") -> "np.ndarray":
        interleaved = arr.reshape(point_count, var_count, 2)
        with np.errstate(invalid="ignore", over="ignore"):
            return interleaved[..., 0] + 1j * interleaved[..., 1]

    little_raw = np.frombuffer(payload, dtype="<f8", count=total_vals * 2)
    big_raw = np.frombuffer(payload, dtype=">f8", count=total_vals * 2)
    little = _to_complex(little_raw)
    big = _to_complex(big_raw)

    # AC independent variable should be real, non-decreasing frequency.
    little_good = bool(np.all(np.diff(little[:, 0].real) >= 0) and np.max(np.abs(little[:, 0].imag)) < 1e-18)
    big_good = bool(np.all(np.diff(big[:, 0].real) >= 0) and np.max(np.abs(big[:, 0].imag)) < 1e-18)
    if little_good and not big_good:
        return little.astype(np.complex128)
    if big_good and not little_good:
        return big.astype(np.complex128)
    return little.astype(np.complex128)


def _load_raw_vectors(input_path: Path):
    raw_bytes = input_path.read_bytes()
    names, kinds, var_count, point_count, flags, data_start = _parse_header(raw_bytes)
    payload = raw_bytes[data_start:]

    if "complex" in flags:
        matrix = _decode_complex_matrix(payload, var_count, point_count)
        is_complex = True
    elif "real" in flags:
        matrix = _decode_real_matrix(payload, var_count, point_count)
        is_complex = False
    else:
        raise ValueError(f"Unsupported RAW flags: {flags}")

    return names, kinds, flags, matrix, is_complex


def _escape_hdf5_component(name: str) -> str:
    return name.replace("/", "%2F")


def _xyce_name_to_hdf5_path(vector_name: str) -> tuple[list[str], str]:
    match = VECTOR_NAME_RE.match(vector_name)
    if not match:
        return ["raw"], _escape_hdf5_component(vector_name)

    quantity, target = match.groups()
    quantity = quantity.strip()
    target = target.strip()

    if ":" not in target:
        return [], _escape_hdf5_component(f"{quantity}({target})")

    parts = [p.strip() for p in target.split(":") if p.strip()]
    if not parts:
        return [], _escape_hdf5_component(f"{quantity}({target})")

    inst_path = [_escape_hdf5_component(p) for p in parts[:-1]] or ["top"]
    leaf = _escape_hdf5_component(parts[-1])
    return inst_path, _escape_hdf5_component(f"{quantity}({leaf})")


def _unique_dataset_name(group, base: str) -> str:
    if base not in group:
        return base
    idx = 1
    while f"{base}__{idx}" in group:
        idx += 1
    return f"{base}__{idx}"


def convert_raw_to_hdf5(input_path: Path, output_path: Path) -> None:
    try:
        import h5py
        import numpy as np
    except ImportError as exc:  # pragma: no cover - runtime dependency guard
        raise RuntimeError(
            "HDF5 export requires 'h5py' and 'numpy'. Install with: pip install h5py numpy"
        ) from exc

    names, kinds, flags, matrix, is_complex = _load_raw_vectors(input_path)

    with h5py.File(output_path, "w") as h5:
        h5.attrs["source_file"] = str(input_path)
        h5.attrs["format"] = "xyce_raw"
        h5.attrs["flags"] = flags
        h5.attrs["num_points"] = int(matrix.shape[0])
        h5.attrs["num_variables"] = int(matrix.shape[1])
        h5.attrs["is_complex"] = bool(is_complex)
        h5.attrs["indep_var_index"] = 0
        h5.attrs["indep_var_name"] = names[0] if names else ""

        h5.create_dataset("vectors", data=matrix, compression="gzip", compression_opts=4)
        h5.create_dataset("vector_names", data=np.asarray(names, dtype="S"))
        h5.create_dataset("vector_kinds", data=np.asarray(kinds, dtype="S"))

        indep_var_grp = h5.create_group("indep_var")
        signals_grp = h5.create_group("signals")
        src = h5py.VirtualSource(h5["vectors"])
        vds_dtype = np.complex128 if is_complex else np.float64

        if names:
            indep_name = _unique_dataset_name(indep_var_grp, _escape_hdf5_component(names[0]))
            indep_kind = kinds[0].lower() if kinds else ""

            # AC RAW files are marked complex, but FREQUENCY must remain a real axis.
            if is_complex and indep_kind == "frequency":
                imag_max = float(np.max(np.abs(matrix[:, 0].imag)))
                if imag_max > 1e-15:
                    raise ValueError(
                        f"Independent variable '{names[0]}' has non-negligible imaginary part ({imag_max:g})"
                    )
                indep_ds = indep_var_grp.create_dataset(
                    indep_name,
                    data=matrix[:, 0].real.astype(np.float64),
                    compression="gzip",
                    compression_opts=4,
                )
                indep_ds.attrs["source"] = "vectors[:,0].real"
            else:
                indep_layout = h5py.VirtualLayout(shape=(matrix.shape[0],), dtype=vds_dtype)
                indep_layout[:] = src[:, 0]
                indep_ds = indep_var_grp.create_virtual_dataset(indep_name, indep_layout)

            indep_ds.attrs["original_name"] = names[0]
            indep_ds.attrs["kind"] = kinds[0]
            indep_ds.attrs["index"] = 0

        for index, name in enumerate(names[1:], start=1):
            group_parts, dataset_name = _xyce_name_to_hdf5_path(name)
            current_group = signals_grp
            for part in group_parts:
                current_group = current_group.require_group(part)

            dataset_name = _unique_dataset_name(current_group, dataset_name)
            layout = h5py.VirtualLayout(shape=(matrix.shape[0],), dtype=vds_dtype)
            layout[:] = src[:, index]
            dset = current_group.create_virtual_dataset(dataset_name, layout)
            dset.attrs["original_name"] = name
            dset.attrs["kind"] = kinds[index]
            dset.attrs["index"] = index


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert Xyce RAW (real/complex) to HDF5")
    parser.add_argument("input", type=Path, help="Input .raw file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output HDF5 path (default: <input>.h5)",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    output = args.output or args.input.with_suffix(args.input.suffix + ".h5")
    try:
        convert_raw_to_hdf5(args.input, output)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
