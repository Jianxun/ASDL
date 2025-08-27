# Ready for Next Session: Generator Ordering + Top-Style, and Elaborator Follow-ups

## ✅ This Session Summary (Generator Refactor)
- Removed automatic PDK `.include` emission from generator
- Removed `XMAIN` emission; preserved top diagnostics (G0102/G0701)
- Modularized generator: `options`, `subckt`, `instances`, `templates`, `calls`, `formatting`, `guards`, `postprocess`
- Refactored `SPICEGenerator.generate()` into helper methods
- All generator unit tests passing (18/18)

## 🚀 Next Priority: Generator Ordering + Top-Style

### Objectives
- Emit hierarchical subckts in dependency order (children before parents), with `top` last
- Support top-level rendering modes:
  - `subckt`: normal wrappers, `top` last
  - `flat`: comment only the `top` `.subckt`/`.ends` lines with `*`; keep body unchanged

### Tasks
- [ ] Implement `ordering.py` (DAG build + DFS postorder with cycle guard)
- [ ] Integrate ordering into `SPICEGenerator` emission (use new helper)
- [ ] Add top-style handling in `subckt` emission for `top` module only
- [ ] Update/add generator unit tests: ordering and top-style
- [ ] CLI: add `--top-style {subckt,flat}` and pass to `GeneratorOptions`

### Notes
- Deterministic traversal via module insertion order (fallback to name-sort)
- Preserve single emission per module (perm_mark)
- Emit cycle diagnostic and skip back-edge if encountered (validator should catch earlier)

## 📦 Elaborator Phase (Follow-up)
- Keep `Phase 1.2.5` elaborator integration plan available (import resolution → pattern → variable)
- CLI `--search-path` already supported; re-run e2e tests after generator changes

**Ready to continue with generator ordering/top-style implementation in a new session.**