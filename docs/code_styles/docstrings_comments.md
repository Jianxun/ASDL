# Docstrings and Comments Style

This standard keeps API intent obvious for humans and agents without digging
through implementation details.

## Scope
- Applies to `src/asdl/**` Python code.
- Required for public modules, classes, and functions.
- Required for non-trivial private helpers (logic, invariants, ordering).

## Docstrings
- Follow PEP 257 (summary line, blank line, detail).
- Use Google-style sections: `Args`, `Returns`, `Raises`, `Yields`, `Notes`
  (optional), `Invariants` (optional).
- Keep type hints in signatures; docstrings focus on semantics and constraints.
- Call out determinism, ordering, side effects, and diagnostics emitted.
- For dataclasses: class docstring; add field notes only if non-obvious.

## Comments
- Explain "why" and tricky behavior, not "what".
- Place comments above the relevant block.
- Keep comments current; delete stale commentary.
- Use `NOTE:` for nuance and `TODO(T-XXX):` for tracked follow-ups.
- Avoid commented-out code.

## Examples
```python
def load_backend_config(backend_name: str, config_path: Path | None = None) -> BackendConfig:
    """Load backend configuration from YAML.

    Args:
        backend_name: Backend ID (e.g., "sim.ngspice").
        config_path: Optional explicit path; defaults to ASDL_BACKEND_CONFIG.
    Returns:
        Parsed backend configuration.
    Raises:
        FileNotFoundError: If the config file is missing.
        KeyError: If the backend entry is absent or incomplete.
    """
```
