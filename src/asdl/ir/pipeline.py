from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional, Type, TypeVar

from xdsl.context import Context
from xdsl.dialects import builtin
from xdsl.ir import Operation
from xdsl.passes import ModulePass, PassPipeline
from xdsl.printer import Printer
from xdsl.utils.exceptions import VerifyException

from asdl.ast import AsdlDocument
from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.diagnostics.collector import DiagnosticCollector
from asdl.imports.resolver import ImportGraph, resolve_import_graph
from asdl.ir.converters.ast_to_nfir import convert_document
from asdl.ir.converters.nfir_to_ifir import convert_design as convert_nfir_to_ifir
from asdl.ir.ifir import ASDL_IFIR, DesignOp as IfirDesignOp
from asdl.ir.nfir import ASDL_NFIR, DesignOp as NfirDesignOp
from asdl.ir.pattern_atomization import PatternAtomizePass, PatternAtomizeState

NO_SPAN_NOTE = "No source span available."

VERIFY_NFIR_FAILED = format_code("PASS", 1)
NFIR_DESIGN_MISSING = format_code("PASS", 2)
VERIFY_IFIR_FAILED = format_code("PASS", 3)
IFIR_DESIGN_MISSING = format_code("PASS", 4)
PIPELINE_CRASH = format_code("PASS", 999)

DUMP_STAGE_NFIR = "nfir"
DUMP_STAGE_IFIR = "ifir"
DUMP_STAGE_ATOMIZED_IFIR = "ifir_atomized"
PIPELINE_DUMP_FILENAMES = {
    DUMP_STAGE_NFIR: "nfir.mlir",
    DUMP_STAGE_IFIR: "ifir.mlir",
    DUMP_STAGE_ATOMIZED_IFIR: "ifir_atomized.mlir",
}
PIPELINE_DUMP_STAGE_ORDER = tuple(PIPELINE_DUMP_FILENAMES.keys())

DesignOpT = TypeVar("DesignOpT", bound=Operation)
DumpCallback = Callable[[str, str], None]


class PipelineAbort(Exception):
    pass


@dataclass
class PipelineState:
    diagnostics: DiagnosticCollector
    failed: bool = False
    ifir_design: Optional[IfirDesignOp] = None


@dataclass(frozen=True)
class PipelineDumpOptions:
    """Configure optional IR dump hooks for the MVP pipeline.

    Attributes:
        stages: Stage names to dump; empty means all stages.
        dump_dir: Directory to write dump files into.
        dump_callback: Optional callback for capturing dump text.
    """

    stages: tuple[str, ...] = ()
    dump_dir: Optional[Path] = None
    dump_callback: Optional[DumpCallback] = None


@dataclass(frozen=True)
class VerifyNfirPass(ModulePass):
    name = "verify-nfir"

    state: PipelineState

    def apply(self, ctx: Context, op: builtin.ModuleOp) -> None:
        self._verify(op, "NFIR", VERIFY_NFIR_FAILED)

    def _verify(self, op: builtin.ModuleOp, label: str, code: str) -> None:
        try:
            op.verify()
        except VerifyException as exc:
            self.state.diagnostics.emit(
                _diagnostic(code, f"{label} verification failed: {exc}")
            )
            self.state.failed = True
            raise PipelineAbort() from exc


@dataclass(frozen=True)
class VerifyIfirPass(ModulePass):
    name = "verify-ifir"

    state: PipelineState

    def apply(self, ctx: Context, op: builtin.ModuleOp) -> None:
        self._verify(op, "IFIR", VERIFY_IFIR_FAILED)

    def _verify(self, op: builtin.ModuleOp, label: str, code: str) -> None:
        try:
            op.verify()
        except VerifyException as exc:
            self.state.diagnostics.emit(
                _diagnostic(code, f"{label} verification failed: {exc}")
            )
            self.state.failed = True
            raise PipelineAbort() from exc


@dataclass(frozen=True)
class NfirToIfirPass(ModulePass):
    name = "nfir-to-ifir"

    state: PipelineState

    def apply(self, ctx: Context, op: builtin.ModuleOp) -> None:
        design = _find_single_design(
            op,
            NfirDesignOp,
            NFIR_DESIGN_MISSING,
            diagnostics=self.state.diagnostics,
        )
        if design is None:
            self.state.failed = True
            raise PipelineAbort()

        ifir_design, diagnostics = convert_nfir_to_ifir(design)
        self.state.diagnostics.extend(diagnostics)
        if ifir_design is None:
            self.state.failed = True
            raise PipelineAbort()

        block = op.body.block
        block.insert_op_before(ifir_design, design)
        block.erase_op(design)
        self.state.ifir_design = ifir_design


@dataclass(frozen=True)
class AtomizeIfirPass(ModulePass):
    name = "atomize-patterns"

    state: PipelineState

    def apply(self, ctx: Context, op: builtin.ModuleOp) -> None:
        atom_state = PatternAtomizeState(diagnostics=self.state.diagnostics)
        PatternAtomizePass(state=atom_state).apply(ctx, op)
        if atom_state.failed:
            self.state.failed = True
            raise PipelineAbort()
        if atom_state.design is None:
            self.state.ifir_design = None
            return
        self.state.ifir_design = atom_state.design


@dataclass(frozen=True)
class DumpIrPass(ModulePass):
    """Pipeline pass that emits textual dumps of the current IR module."""

    name = "dump-ir"

    stage: str
    dump_options: PipelineDumpOptions

    def apply(self, ctx: Context, op: builtin.ModuleOp) -> None:
        _dump_ir(self.stage, op, self.dump_options)


def run_mvp_pipeline(
    document: Optional[AsdlDocument] = None,
    *,
    entry_file: Optional[Path] = None,
    lib_roots: Optional[Iterable[Path]] = None,
    verify: bool = True,
    dump_options: Optional[PipelineDumpOptions] = None,
) -> tuple[IfirDesignOp | None, list[Diagnostic]]:
    diagnostics = DiagnosticCollector()

    if entry_file is not None:
        if document is not None:
            diagnostics.emit(
                _diagnostic(
                    PIPELINE_CRASH,
                    "Provide either document or entry_file, not both.",
                )
            )
            return None, diagnostics.to_list()
        nfir_design = _lower_import_graph(entry_file, lib_roots, diagnostics)
    else:
        if document is None:
            diagnostics.emit(
                _diagnostic(
                    PIPELINE_CRASH,
                    "Pipeline requires a document or entry file.",
                )
            )
            return None, diagnostics.to_list()
        nfir_design, nfir_diags = convert_document(document)
        diagnostics.extend(nfir_diags)
    if nfir_design is None or _has_error_diagnostics(diagnostics.to_list()):
        return None, diagnostics.to_list()

    return _run_pipeline(nfir_design, diagnostics, verify, dump_options)


def _run_pipeline(
    nfir_design: NfirDesignOp,
    diagnostics: DiagnosticCollector,
    verify: bool,
    dump_options: Optional[PipelineDumpOptions],
) -> tuple[IfirDesignOp | None, list[Diagnostic]]:
    module = builtin.ModuleOp([nfir_design])
    state = PipelineState(diagnostics=diagnostics)
    passes: list[ModulePass] = []
    dump_stages = _resolve_dump_stages(dump_options)
    dump_enabled = dump_options is not None and (
        dump_options.dump_dir is not None or dump_options.dump_callback is not None
    )
    if dump_enabled and DUMP_STAGE_NFIR in dump_stages:
        passes.append(
            DumpIrPass(stage=DUMP_STAGE_NFIR, dump_options=dump_options)
        )
    if verify:
        passes.append(VerifyNfirPass(state=state))
    passes.append(NfirToIfirPass(state=state))
    if dump_enabled and DUMP_STAGE_IFIR in dump_stages:
        passes.append(
            DumpIrPass(stage=DUMP_STAGE_IFIR, dump_options=dump_options)
        )
    passes.append(AtomizeIfirPass(state=state))
    if dump_enabled and DUMP_STAGE_ATOMIZED_IFIR in dump_stages:
        passes.append(
            DumpIrPass(
                stage=DUMP_STAGE_ATOMIZED_IFIR,
                dump_options=dump_options,
            )
        )
    if verify:
        passes.append(VerifyIfirPass(state=state))

    pipeline = PassPipeline(tuple(passes))
    ctx = _build_context()
    try:
        pipeline.apply(ctx, module)
    except PipelineAbort:
        return None, diagnostics.to_list()
    except Exception as exc:  # pragma: no cover - defensive: unexpected pipeline error
        diagnostics.emit(_diagnostic(PIPELINE_CRASH, f"Pipeline failed: {exc}"))
        return None, diagnostics.to_list()

    if state.ifir_design is None:
        state.ifir_design = _find_single_design(
            module,
            IfirDesignOp,
            IFIR_DESIGN_MISSING,
            diagnostics=diagnostics,
        )
        if state.ifir_design is None:
            return None, diagnostics.to_list()

    return state.ifir_design, diagnostics.to_list()


def _lower_import_graph(
    entry_file: Path,
    lib_roots: Optional[Iterable[Path]],
    diagnostics: DiagnosticCollector,
) -> Optional[NfirDesignOp]:
    graph, import_diags = resolve_import_graph(
        entry_file,
        lib_roots=lib_roots,
    )
    diagnostics.extend(import_diags)
    if graph is None:
        return None

    return _build_import_design(graph, diagnostics)


def _build_import_design(
    graph: ImportGraph,
    diagnostics: DiagnosticCollector,
) -> Optional[NfirDesignOp]:
    ops: list[Operation] = []
    had_error = False
    entry_document = graph.documents.get(graph.entry_file)

    for file_id, document in graph.documents.items():
        name_env = graph.name_envs.get(file_id)
        nfir_design, nfir_diags = convert_document(
            document,
            name_env=name_env,
            program_db=graph.program_db,
        )
        diagnostics.extend(nfir_diags)
        if nfir_design is None:
            had_error = True
            continue
        ops.extend(op.clone() for op in nfir_design.body.block.ops)

    if had_error:
        return None
    if entry_document is None:
        diagnostics.emit(
            _diagnostic(
                PIPELINE_CRASH,
                "Entry document missing from import graph.",
            )
        )
        return None

    return NfirDesignOp(
        region=ops,
        top=entry_document.top,
        entry_file_id=str(graph.entry_file),
    )


def _build_context() -> Context:
    ctx = Context()
    ctx.load_dialect(builtin.Builtin)
    ctx.load_dialect(ASDL_NFIR)
    ctx.load_dialect(ASDL_IFIR)
    return ctx


def _resolve_dump_stages(
    dump_options: Optional[PipelineDumpOptions],
) -> frozenset[str]:
    """Normalize the dump stage selection into a set."""
    if dump_options is None:
        return frozenset()
    if not dump_options.stages:
        return frozenset(PIPELINE_DUMP_STAGE_ORDER)
    return frozenset(dump_options.stages)


def _dump_ir(
    stage: str,
    module: builtin.ModuleOp,
    dump_options: PipelineDumpOptions,
) -> None:
    """Write or emit the textual IR dump for the selected stage."""
    if (
        dump_options.dump_dir is None
        and dump_options.dump_callback is None
    ):
        return
    output = _render_module_text(module)
    if dump_options.dump_dir is not None:
        dump_options.dump_dir.mkdir(parents=True, exist_ok=True)
        dump_path = dump_options.dump_dir / PIPELINE_DUMP_FILENAMES[stage]
        dump_path.write_text(output, encoding="utf-8")
    if dump_options.dump_callback is not None:
        dump_options.dump_callback(stage, output)


def _render_module_text(module: builtin.ModuleOp) -> str:
    """Render an xDSL module operation as text for debugging."""
    buffer = io.StringIO()
    Printer(stream=buffer).print_op(module)
    return buffer.getvalue()


def _find_single_design(
    module: builtin.ModuleOp,
    design_type: Type[DesignOpT],
    code: str,
    *,
    diagnostics: Optional[DiagnosticCollector] = None,
) -> Optional[DesignOpT]:
    found = [op for op in module.body.block.ops if isinstance(op, design_type)]
    if len(found) == 1:
        return found[0]
    if diagnostics is not None:
        count = len(found)
        label = getattr(design_type, "name", design_type.__name__)
        diagnostics.emit(
            _diagnostic(code, f"Expected single {label} in module, found {count}")
        )
    return None


def _has_error_diagnostics(diagnostics: Iterable[Diagnostic]) -> bool:
    return any(
        diagnostic.severity in (Severity.ERROR, Severity.FATAL)
        for diagnostic in diagnostics
    )


def _diagnostic(code: str, message: str) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=None,
        notes=[NO_SPAN_NOTE],
        source="pass",
    )


__all__ = [
    "DUMP_STAGE_ATOMIZED_IFIR",
    "DUMP_STAGE_IFIR",
    "DUMP_STAGE_NFIR",
    "PIPELINE_DUMP_FILENAMES",
    "PipelineDumpOptions",
    "run_mvp_pipeline",
]
