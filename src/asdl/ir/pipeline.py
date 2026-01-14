from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Type, TypeVar

from xdsl.context import Context
from xdsl.dialects import builtin
from xdsl.ir import Operation
from xdsl.passes import ModulePass, PassPipeline
from xdsl.utils.exceptions import VerifyException

from asdl.ast import AsdlDocument
from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.diagnostics.collector import DiagnosticCollector
from asdl.imports.resolver import resolve_import_graph
from asdl.ir.converters.ast_to_graphir import convert_document, convert_import_graph
from asdl.ir.converters.graphir_to_ifir import convert_program as convert_graphir_to_ifir
from asdl.ir.graphir import ASDL_GRAPHIR, ProgramOp as GraphProgramOp
from asdl.ir.ifir import ASDL_IFIR, DesignOp as IfirDesignOp
from asdl.ir.pattern_atomization import PatternAtomizePass, PatternAtomizeState

NO_SPAN_NOTE = "No source span available."

VERIFY_GRAPHIR_FAILED = format_code("PASS", 1)
GRAPHIR_PROGRAM_MISSING = format_code("PASS", 2)
VERIFY_IFIR_FAILED = format_code("PASS", 3)
IFIR_DESIGN_MISSING = format_code("PASS", 4)
PIPELINE_CRASH = format_code("PASS", 999)

DesignOpT = TypeVar("DesignOpT", bound=Operation)


class PipelineAbort(Exception):
    pass


@dataclass
class PipelineState:
    diagnostics: DiagnosticCollector
    failed: bool = False
    ifir_design: Optional[IfirDesignOp] = None


@dataclass(frozen=True)
class VerifyGraphirPass(ModulePass):
    name = "verify-graphir"

    state: PipelineState

    def apply(self, ctx: Context, op: builtin.ModuleOp) -> None:
        self._verify(op, "GraphIR", VERIFY_GRAPHIR_FAILED)

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
class GraphirToIfirPass(ModulePass):
    name = "graphir-to-ifir"

    state: PipelineState

    def apply(self, ctx: Context, op: builtin.ModuleOp) -> None:
        program = _find_single_program(
            op,
            GRAPHIR_PROGRAM_MISSING,
            diagnostics=self.state.diagnostics,
        )
        if program is None:
            self.state.failed = True
            raise PipelineAbort()

        ifir_design, diagnostics = convert_graphir_to_ifir(program)
        self.state.diagnostics.extend(diagnostics)
        if ifir_design is None:
            self.state.failed = True
            raise PipelineAbort()

        block = op.body.block
        block.insert_op_before(ifir_design, program)
        block.erase_op(program)
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


def run_mvp_pipeline(
    document: Optional[AsdlDocument] = None,
    *,
    entry_file: Optional[Path] = None,
    lib_roots: Optional[Iterable[Path]] = None,
    verify: bool = True,
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
        program, program_diags = lower_import_graph_to_graphir(
            entry_file, lib_roots=lib_roots
        )
        diagnostics.extend(program_diags)
    else:
        if document is None:
            diagnostics.emit(
                _diagnostic(
                    PIPELINE_CRASH,
                    "Pipeline requires a document or entry file.",
                )
            )
            return None, diagnostics.to_list()
        program, program_diags = convert_document(document)
        diagnostics.extend(program_diags)
    if program is None or _has_error_diagnostics(diagnostics.to_list()):
        return None, diagnostics.to_list()

    return _run_pipeline(program, diagnostics, verify)


def _run_pipeline(
    program: GraphProgramOp,
    diagnostics: DiagnosticCollector,
    verify: bool,
) -> tuple[IfirDesignOp | None, list[Diagnostic]]:
    module = builtin.ModuleOp([program])
    state = PipelineState(diagnostics=diagnostics)
    passes: list[ModulePass] = []
    if verify:
        passes.append(VerifyGraphirPass(state=state))
    passes.append(GraphirToIfirPass(state=state))
    passes.append(AtomizeIfirPass(state=state))
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


def lower_import_graph_to_graphir(
    entry_file: Path,
    *,
    lib_roots: Optional[Iterable[Path]] = None,
) -> tuple[GraphProgramOp | None, list[Diagnostic]]:
    """Resolve imports and build a GraphIR program.

    Args:
        entry_file: Entry file path.
        lib_roots: Optional library roots for import resolution.

    Returns:
        Tuple of GraphIR program op (or None) and diagnostics.
    """
    diagnostics = DiagnosticCollector()
    graph, import_diags = resolve_import_graph(
        entry_file,
        lib_roots=lib_roots,
    )
    diagnostics.extend(import_diags)
    if graph is None:
        return None, diagnostics.to_list()

    program, graph_diags = convert_import_graph(graph)
    diagnostics.extend(graph_diags)
    if program is None or _has_error_diagnostics(diagnostics.to_list()):
        return None, diagnostics.to_list()
    return program, diagnostics.to_list()


def _build_context() -> Context:
    ctx = Context()
    ctx.load_dialect(builtin.Builtin)
    ctx.load_dialect(ASDL_GRAPHIR)
    ctx.load_dialect(ASDL_IFIR)
    return ctx


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


def _find_single_program(
    module: builtin.ModuleOp,
    code: str,
    *,
    diagnostics: Optional[DiagnosticCollector] = None,
) -> Optional[GraphProgramOp]:
    found = [op for op in module.body.block.ops if isinstance(op, GraphProgramOp)]
    if len(found) == 1:
        return found[0]
    if diagnostics is not None:
        count = len(found)
        diagnostics.emit(
            _diagnostic(
                code,
                f"Expected single {GraphProgramOp.name} in module, found {count}",
            )
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


__all__ = ["lower_import_graph_to_graphir", "run_mvp_pipeline"]
