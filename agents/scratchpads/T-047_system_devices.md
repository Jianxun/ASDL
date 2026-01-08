# T-047: System Devices for Backend Structural Templates

**Status**: Ready
**Owner**: Executor
**Created**: 2026-01-03

---

## Objective

Refactor the ngspice emitter to use external backend configuration with system devices per ADR-0006. This decouples backend-specific syntax from emitter logic and enables extensibility for future backends (spectre, hspice, etc.).

---

## Files to Create

- `src/asdl/emit/backend_config.py` (new)
- `config/backends.yaml` (new, move from `examples/scratch/`)
- `tests/unit_tests/emit/test_backend_config.py` (new)
- `tests/unit_tests/netlist/test_system_devices.py` (new)


## Success Criteria

- [x] Backend config loading works with env var and explicit path
- [x] Validation catches missing required system devices
- [x] Emitter uses system devices for headers, footers, module calls
- [x] Hardcoded ngspice syntax removed from emitter
- [x] All existing netlist tests pass with identical output
- [x] New tests for backend config and system devices
- [x] Code is clean, well-documented, and follows existing patterns

### Verification

```bash
pytest tests/unit_tests/emit -v          # 6 passed ✅
pytest tests/unit_tests/netlist -v       # 7 passed ✅
```

### Files Changed

**Created:**
- `src/asdl/emit/backend_config.py`
- `config/backends.yaml`
- `tests/unit_tests/emit/test_backend_config.py`

**Modified:**
- `src/asdl/emit/ngspice.py`:
  - Added imports for backend_config, Path, yaml
  - Updated `EmitOptions` with `backend_config` field
  - Updated `emit_ngspice()` signature and implementation
  - Added `_render_system_device()` helper
  - Refactored `_emit_module()` to use system devices
  - Refactored `_emit_instance()` for module calls
  - Updated `_emit_design()` to render netlist header/footer
  - Removed `_format_subckt_line()` function

### Notes

- Backend config file uses empty templates for `__netlist_header__` and `__netlist_footer__` to maintain byte-for-byte compatibility with existing output
- Top module wrapper commenting logic preserved for backward compatibility
- All hardcoded ngspice syntax successfully removed from emitter code
- System devices use the same template mechanism as regular device backends

---

## PR URL
- https://github.com/Jianxun/ASDL/pull/39

