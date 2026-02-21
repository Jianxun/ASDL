"""Semantic completion engine reused by ASDL language tooling workers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlparse

from asdl.ast import AsdlDocument, DeviceDecl, ModuleDecl, parse_file, parse_string
from asdl.ast.instance_expr import parse_inline_instance_expr
from asdl.cli.config import load_asdlrc
from asdl.imports import NameEnv, ProgramDB, resolve_import_path

from .context import CompletionContext, detect_completion_context


@dataclass(frozen=True)
class CompletionItem:
    """Completion payload item for worker/frontend transport.

    Args:
        label: UI display label.
        kind: Item category identifier.
        insert_text: Text inserted when completion is accepted.
        detail: Short human-readable context.
        sort_text: Stable sort key.
    """

    label: str
    kind: str
    insert_text: str
    detail: str
    sort_text: str

    def to_dict(self) -> dict[str, str]:
        """Return JSON-serializable dictionary payload."""
        return asdict(self)


@dataclass(frozen=True)
class _DocumentSnapshot:
    version: int
    text: str


class CompletionEngine:
    """Stateful completion engine for ASDL documents.

    The engine stores latest document snapshots and computes semantic completion
    candidates by reusing parser, import resolver, and `.asdlrc` semantics.
    """

    def __init__(self) -> None:
        self._workspace_roots: list[Path] = []
        self._override_lib_roots: list[Path] = []
        self._config_path: Optional[Path] = None
        self._documents: dict[str, _DocumentSnapshot] = {}

    def initialize(
        self,
        *,
        workspace_roots: Optional[list[Path | str]] = None,
        lib_roots: Optional[list[Path | str]] = None,
        config_path: Optional[Path | str] = None,
    ) -> dict[str, object]:
        """Initialize workspace-scoped engine settings.

        Args:
            workspace_roots: Workspace root directories from the editor host.
            lib_roots: Optional explicit import root overrides.
            config_path: Optional explicit `.asdlrc` path override.

        Returns:
            Lightweight state summary for diagnostics/logging.
        """
        self._workspace_roots = [Path(root).absolute() for root in (workspace_roots or [])]
        self._override_lib_roots = [Path(root).absolute() for root in (lib_roots or [])]
        self._config_path = Path(config_path).absolute() if config_path else None
        return {
            "workspace_roots": [str(path) for path in self._workspace_roots],
            "lib_roots": [str(path) for path in self._override_lib_roots],
            "config_path": str(self._config_path) if self._config_path else None,
        }

    def update_document(self, *, uri: str, version: int, text: str) -> dict[str, int | str]:
        """Store latest document text snapshot.

        Args:
            uri: Document URI.
            version: Host document version.
            text: Full document text.

        Returns:
            Metadata describing the cached snapshot.
        """
        self._documents[uri] = _DocumentSnapshot(version=version, text=text)
        return {"uri": uri, "version": version}

    def complete(self, *, uri: str, line: int, character: int) -> list[CompletionItem]:
        """Compute completion candidates for a cursor location.

        Args:
            uri: Document URI.
            line: Zero-based line index.
            character: Zero-based line character index.

        Returns:
            Completion candidates sorted by stable insert text order.
        """
        path = _uri_to_path(uri)
        if path is None:
            return []
        text = self._document_text(uri, path)
        context = detect_completion_context(text, line, character)
        if context is None:
            return []

        document, _diagnostics = parse_string(text, file_path=path)
        if document is None:
            return []

        lib_roots = self._effective_lib_roots(path)
        imported_documents, imports_by_namespace = self._load_imported_documents(
            document,
            path,
            lib_roots,
        )

        all_documents = {path.absolute(): document, **imported_documents}
        program_db, _db_diags = ProgramDB.build(all_documents)
        name_env = NameEnv(file_id=path.absolute(), bindings=imports_by_namespace)

        if context.kind == "import_symbol":
            return self._complete_import_symbols(document, imports_by_namespace, program_db, context)
        if context.kind == "param":
            return self._complete_params(document, path.absolute(), program_db, name_env, context)
        if context.kind == "endpoint":
            return self._complete_endpoints(document, path.absolute(), program_db, name_env, context)
        return []

    def shutdown(self) -> dict[str, bool]:
        """Release cached state and return shutdown acknowledgement."""
        self._documents.clear()
        return {"shutdown": True}

    def _document_text(self, uri: str, path: Path) -> str:
        snapshot = self._documents.get(uri)
        if snapshot is not None:
            return snapshot.text
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def _effective_lib_roots(self, entry_file: Path) -> list[Path]:
        roots = list(self._override_lib_roots)
        rc = load_asdlrc(entry_file, config_path=self._config_path)
        if rc is not None:
            roots.extend(rc.lib_roots)
        return roots

    def _load_imported_documents(
        self,
        document: AsdlDocument,
        entry_file: Path,
        lib_roots: list[Path],
    ) -> tuple[dict[Path, AsdlDocument], dict[str, Path]]:
        imported_documents: dict[Path, AsdlDocument] = {}
        imports_by_namespace: dict[str, Path] = {}
        for namespace, import_path in (document.imports or {}).items():
            resolved, _diags = resolve_import_path(
                import_path,
                importing_file=entry_file,
                lib_roots=lib_roots,
            )
            if resolved is None:
                continue
            imports_by_namespace[namespace] = resolved
            parsed, _parse_diags = parse_file(str(resolved))
            if parsed is None:
                continue
            imported_documents[resolved] = parsed
        return imported_documents, imports_by_namespace

    def _complete_import_symbols(
        self,
        document: AsdlDocument,
        imports_by_namespace: dict[str, Path],
        program_db: ProgramDB,
        context: CompletionContext,
    ) -> list[CompletionItem]:
        prefix = context.prefix
        items: list[CompletionItem] = []

        ns_filter = ""
        symbol_filter = ""
        if "." in prefix:
            ns_filter, symbol_filter = prefix.split(".", 1)

        for namespace in sorted((document.imports or {}).keys()):
            if ns_filter and not namespace.startswith(ns_filter):
                continue
            resolved = imports_by_namespace.get(namespace)
            if resolved is None:
                continue
            symbols = program_db.symbols.get(resolved, {})
            for symbol_name, symbol_def in sorted(symbols.items()):
                if symbol_filter and not symbol_name.startswith(symbol_filter):
                    continue
                qualified = f"{namespace}.{symbol_name}"
                items.append(
                    CompletionItem(
                        label=qualified,
                        kind="symbol",
                        insert_text=qualified,
                        detail=f"imported {symbol_def.kind}",
                        sort_text=qualified,
                    )
                )
        return items

    def _complete_params(
        self,
        document: AsdlDocument,
        entry_file: Path,
        program_db: ProgramDB,
        name_env: NameEnv,
        context: CompletionContext,
    ) -> list[CompletionItem]:
        module = _module_by_name(document, context.module_name)
        if module is None or not module.instances or context.instance_name is None:
            return []

        expr = module.instances.get(context.instance_name)
        if not isinstance(expr, str):
            return []

        ref, _params = _parse_instance_expr(expr)
        if ref is None:
            return []
        decl = _resolve_reference_decl(ref, entry_file, program_db, name_env)
        if decl is None:
            return []

        names = sorted((decl.parameters or {}).keys()) if isinstance(decl, DeviceDecl) else []
        return [
            CompletionItem(
                label=f"{name}=",
                kind="param",
                insert_text=f"{name}=",
                detail="instance parameter",
                sort_text=name,
            )
            for name in names
        ]

    def _complete_endpoints(
        self,
        document: AsdlDocument,
        entry_file: Path,
        program_db: ProgramDB,
        name_env: NameEnv,
        context: CompletionContext,
    ) -> list[CompletionItem]:
        module = _module_by_name(document, context.module_name)
        if module is None or not module.instances:
            return []

        prefix_instance = ""
        if "." in context.prefix:
            prefix_instance = context.prefix.split(".", 1)[0]

        items: list[CompletionItem] = []
        for inst_name, expr in sorted(module.instances.items()):
            if prefix_instance and not inst_name.startswith(prefix_instance):
                continue
            ref, _params = _parse_instance_expr(expr)
            if ref is None:
                continue
            decl = _resolve_reference_decl(ref, entry_file, program_db, name_env)
            ports = _decl_ports(decl)
            for port in ports:
                endpoint = f"{inst_name}.{port}"
                items.append(
                    CompletionItem(
                        label=endpoint,
                        kind="endpoint",
                        insert_text=endpoint,
                        detail="instance endpoint",
                        sort_text=endpoint,
                    )
                )
        return items


def _uri_to_path(uri: str) -> Optional[Path]:
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        return None
    return Path(unquote(parsed.path)).absolute()


def _module_by_name(document: AsdlDocument, module_name: Optional[str]) -> Optional[ModuleDecl]:
    if not module_name or not document.modules:
        return None
    return document.modules.get(module_name)


def _parse_instance_expr(expr: str) -> tuple[Optional[str], dict[str, str]]:
    ref, params, error = parse_inline_instance_expr(expr, strict_params=False)
    if error is not None or ref is None:
        return None, {}
    return ref, dict(params)


def _resolve_reference_decl(
    ref: str,
    entry_file: Path,
    program_db: ProgramDB,
    name_env: NameEnv,
) -> Optional[ModuleDecl | DeviceDecl]:
    if "." in ref:
        namespace, symbol = ref.split(".", 1)
        resolved = name_env.resolve(namespace)
        if resolved is None:
            return None
        symbol_def = program_db.lookup(resolved, symbol)
        return symbol_def.decl if symbol_def else None

    symbol_def = program_db.lookup(entry_file, ref)
    return symbol_def.decl if symbol_def else None


def _decl_ports(decl: Optional[ModuleDecl | DeviceDecl]) -> list[str]:
    if decl is None:
        return []
    if isinstance(decl, DeviceDecl):
        return list(decl.ports or [])

    ports: list[str] = []
    for net_name in (decl.nets or {}).keys():
        if net_name.startswith("$"):
            ports.append(net_name[1:])
    return ports


__all__ = ["CompletionEngine", "CompletionItem"]
