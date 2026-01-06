# ASDL (Analog Structured Description Language)

ASDL is a Python-first framework for describing analog circuits as structured YAML, elaborating them into an xDSL-based IR stack, validating constraints, and emitting deterministic ngspice netlists from configurable backend templates. The current MVP focuses on a clean pipeline that walks from AST → NFIR → IFIR → emit, so every downstream pass can rely on lexemes, diagnostics, and order-preserving nets that originated in the source files.

## MVP status highlights
- Pydantic v2 AST models with ruamel-based parsing that preserve `nets` order, pattern tokens, and diagnostic spans.
- NFIR (net-first IR) and IFIR dialects modeled with xDSL; conversions retain pattern metadata (`expansion_len`) and emit diagnostics instead of raising exceptions.
- Pattern tooling: raw tokens survive through AST/NFIR/IFIR, a standalone expansion engine, binding verification, and an elaboration pass that produces concrete names before emission.
- ngspice emitter driven by `config/backends.yaml`; five required system devices (header/footer, subckt call, netlist header/footer) isolate backend syntax from the IR.
- CLI `asdlc` orchestrates parsing, lowering, and emission; `--backend` selects outputs (default `sim.ngspice`), and schema generation/testing helpers ensure regressions are caught.
- Specs and documentation: MVP specs live under `docs/specs_mvp/` while the canonical `docs/specs/` set is being reconciled with the current stack.

## Repository layout
- `src/asdl/`: active refactor (AST, diagnostics, IR, CLI, emit, imports, etc.).
- `docs/specs_mvp/`: current MVP specs (AST, NFIR, IFIR, ngspice emission).
- `docs/specs/`: canonical specs that are being aligned with the MVP pipeline.
- `config/backends.yaml`: backend templates and required system device definitions.
- `agents/`: multi-agent coordination helpers (`context/`, `roles/`, `scratchpads/`).
- `tests/unit_tests/`: pytest suites covering parser, AST, IR, emit, netlist, e2e, and CLI tooling.

## Development environment setup
1. Install Python 3.10+ and ensure `python` points to the desired interpreter.
2. Clone this repo and enter it:
   ```bash
   git clone git@github.com:Jianxun/ASDL.git
   cd ASDL
   ```
3. Create an isolated virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate      # macOS/Linux
   .\\venv\\Scripts\\activate    # Windows PowerShell
   ```
4. Install runtime and developer deps:
   ```bash
   pip install --upgrade pip
   pip install -e ".[dev]"
   ```
   The xDSL toolchain is optional; install it alongside dev deps with `pip install -e ".[dev,xdsl]"` when you need xDSL-specific tooling or passes.
5. Ensure the backend config is reachable (default `config/backends.yaml`). Override it with `ASDL_BACKEND_CONFIG=/path/to/backends.yaml` when needed (tests use temporary overrides).
6. Run `asdlc --help` to verify the CLI entry point and inspect available commands (`parse`, `emit`, `schema`, etc.).

## Verification & common commands
- `pytest tests/unit_tests/parser -v`
- `pytest tests/unit_tests/ast -v`
- `pytest tests/unit_tests/ir -v`
- `pytest tests/unit_tests/emit -v`
- `pytest tests/unit_tests/netlist`
- `pytest tests/unit_tests/cli`
- `pytest tests/unit_tests/e2e`
- `python -m py_compile src/asdl/emit/netlist/*.py`
- `asdlc schema --out-dir path/to/output` (when schema generation work is in flight)

## Notes
- Keep active development aligned with the Architect-managed tasks (`agents/context/tasks.yaml`), contract, and project status files under `agents/context/`.
- Use `docs/specs_mvp/` for MVP behaviour expectations; only reconcile with `docs/specs/` once major refactors land.
- Preserve diagnostics and deterministic ordering across AST → NFIR → IFIR; converters should never drop references or raise unsanctioned exceptions.

Happy hacking—and keep the pipeline faithful to AST → NFIR → IFIR → emit.
