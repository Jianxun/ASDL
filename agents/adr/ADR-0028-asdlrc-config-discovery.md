ADR-0028: Project .asdlrc discovery and config precedence

Status: Proposed

Context
- `asdlc` currently relies on process environment variables and the current working
  directory for backend config discovery and import search roots.
- VS Code extensions do not inherit shell-sourced environment variables by
  default, which makes `asdlc` behavior differ between terminal and extension.
- A project-local rc file provides a deterministic, repo-checked way to configure
  ASDL paths, backend config, and environment variables without relying on shell
  session state.

Decision
- Add an optional `.asdlrc` YAML file, discovered by walking parents from the
  **entry file directory** to filesystem root (first match wins).
- Add `--config <path>` to override discovery and load an explicit rc file.
- `.asdlrc` schema (v1) is a YAML mapping with:
  - `schema_version: 1`
  - `lib_roots`: list of paths (relative to the rc directory unless absolute)
  - `backend_config`: path to backends YAML (relative to rc directory unless absolute)
  - `env`: map of environment variables to set for the `asdlc` process
- Interpolation: values in `env`, `lib_roots`, and `backend_config` may reference
  `${ASDLRC_DIR}` (directory containing the rc file) and `${VAR}` (effective
  environment variables). Expansion uses the effective environment after rc
  env merge (shell env overrides rc values) plus `ASDLRC_DIR`.
- Path resolution: any relative path inside `.asdlrc` is resolved relative to the
  rc file directory.
- Environment merge: keys in `env` are applied **only when not already present**
  in the process environment, allowing explicit overrides via the shell.
- Import search order remains deterministic:
  1) CLI `--lib` roots (existing behavior)
  2) `.asdlrc` `lib_roots`
  3) `ASDL_LIB_PATH` (PATH-style list)
- Backend config precedence:
  1) CLI `--backend-config` (if added)
  2) `ASDL_BACKEND_CONFIG`
  3) `.asdlrc` `backend_config`
  4) default `config/backends.yaml`

Consequences
- `asdlc` gains a stable per-project configuration path, reducing reliance on
  shell session state and improving VS Code extension compatibility.
- Additional CLI options and config parsing are required in the CLI entrypoint.
- Documentation and examples must include `.asdlrc` guidance to avoid confusion.

Alternatives
- Rely solely on shell scripts (e.g., `examples/setup.sh`); rejected because it
  fails for extension hosts and is fragile across sessions.
- Search from current working directory instead of entry file; rejected because
  `asdlc` behavior would vary based on where the command is run.
