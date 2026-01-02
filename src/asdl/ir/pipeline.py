from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Type, TypeVar

from xdsl.context import Context
from xdsl.dialects import builtin
from xdsl.ir import Operation
from xdsl.passes import ModulePass, PassPipeline
from xdsl.utils.exceptions import VerifyException

from asdl.ast import AsdlDocument
from asdl.diagnostics import Diagnostic, Severity, format_code
from asdl.diagnostics.collector import DiagnosticCollector
from asdl.ir.converters.ast_to_nfir import convert_document
from asdl.ir.converters.nfir_to_ifir import convert_design as convert_nfir_to_ifir
from asdl.ir.ifir import ASDL_IFIR, DesignOp as IfirDesignOp
from asdl.ir.nfir import ASDL_NFIR, DesignOp as NfirDesignOp

NO_SPAN_NOTE = "No source span available."

VERIFY_NFIR_FAILED = format_code("PASS", 1)
NFIR_DESIGN_MISSING = format_code("PASS", 2)
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


def run_mvp_pipeline(
    document: AsdlDocument, *, verify: bool = True
) -> tuple[IfirDesignOp | None, list[Diagnostic]]:
    diagnostics = DiagnosticCollector()

    nfir_design, nfir_diags = convert_document(document)
    diagnostics.extend(nfir_diags)
    if nfir_design is None:
        return None, diagnostics.to_list()

    module = builtin.ModuleOp([nfir_design])
    state = PipelineState(diagnostics=diagnostics)
    passes: list[ModulePass] = []
    if verify:
        passes.append(VerifyNfirPass(state=state))
    passes.append(NfirToIfirPass(state=state))
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


def _build_context() -> Context:
    ctx = Context()
    ctx.load_dialect(builtin.Builtin)
    ctx.load_dialect(ASDL_NFIR)
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


def _diagnostic(code: str, message: str) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=None,
        notes=[NO_SPAN_NOTE],
        source="pass",
    )


__all__ = ["run_mvp_pipeline"]
