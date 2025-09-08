"""
Alias resolver for ASDL import system.

Handles model_alias processing including qualified reference parsing,
alias target validation, and collision detection with import names.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

from ...data_structures import ASDLFile
from ...diagnostics import Diagnostic, DiagnosticSeverity
from .diagnostics import ImportDiagnostics


class AliasResolver:
    """Handles model_alias resolution and validation."""

    # Pattern for validating qualified references (import_alias.module_name)
    QUALIFIED_REFERENCE_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*$')

    def __init__(self, diagnostics: Optional[ImportDiagnostics] = None):
        """Initialize alias resolver."""
        self.diagnostics = diagnostics or ImportDiagnostics()
    
    def parse_qualified_reference(self, qualified_ref: str) -> Optional[Tuple[str, str]]:
        """
        Parse qualified reference into import_alias and module_name.
        
        Args:
            qualified_ref: Qualified reference in format "import_alias.module_name"
            
        Returns:
            Tuple of (import_alias, module_name) or None if invalid format
        """
        if not qualified_ref or not isinstance(qualified_ref, str):
            return None
        
        # Check format with regex
        if not self.QUALIFIED_REFERENCE_PATTERN.match(qualified_ref):
            return None
        
        # Split on first dot only
        try:
            import_alias, module_name = qualified_ref.split('.', 1)
            return import_alias, module_name
        except ValueError:
            return None
    
    def validate_model_aliases(
        self,
        main_file: ASDLFile,
        loaded_files: Dict[Path, ASDLFile],
        alias_resolution_map: Dict[Path, Dict[str, Optional[Path]]],
        main_file_path: Path,
    ) -> List[Diagnostic]:
        """
        Validate all model_alias entries in the main file.
        
        Performs comprehensive validation:
        1. Alias target existence validation
        2. Collision detection with import names
        3. Import alias existence validation
        
        Args:
            main_file: Main ASDL file with model_alias section
            loaded_files: Dictionary of loaded imported files
            
        Returns:
            List of diagnostic errors found during validation
        """
        diagnostics = []
        
        # Skip validation if no model_alias section
        if not main_file.model_alias:
            return diagnostics
        
        # Validate each alias
        for local_alias, qualified_ref in main_file.model_alias.items():
            # Parse qualified reference
            parsed = self.parse_qualified_reference(qualified_ref)
            if parsed is None:
                diagnostics.append(self.diagnostics.create_invalid_model_alias_format_error(local_alias, qualified_ref))
                continue
                
            import_alias, module_name = parsed
            
            # Check for collision with import names
            if main_file.imports and local_alias in main_file.imports:
                diagnostics.append(Diagnostic(
                    code="E0445",
                    title="Model Alias Collision",
                    details=f"Model alias '{local_alias}' collides with import alias name. Alias names must be unique from import names.",
                    severity=DiagnosticSeverity.ERROR,
                    suggestion=f"Rename the model alias '{local_alias}' to avoid collision with the import alias."
                ))
                continue
            
            # Validate import alias exists
            if not main_file.imports or import_alias not in main_file.imports:
                diagnostics.append(self.diagnostics.create_import_alias_not_found_error(import_alias, qualified_ref, list(main_file.imports.keys()) if main_file.imports else []))
                continue
            
            # Resolve absolute path via alias_resolution_map, then validate target module
            resolved_map_for_main = alias_resolution_map.get(main_file_path, {})
            resolved_path = resolved_map_for_main.get(import_alias)
            imported_file = loaded_files.get(resolved_path) if resolved_path else None
            available_modules: List[str] = []
            if imported_file and imported_file.modules:
                available_modules = list(imported_file.modules.keys())

            if imported_file is None or module_name not in (imported_file.modules or {}):
                import_file_path = resolved_path if resolved_path else Path(main_file.imports[import_alias])
                diagnostics.append(
                    self.diagnostics.create_module_not_found_error(
                        module_name, import_alias, import_file_path, available_modules
                    )
                )
                continue
        
        return diagnostics
    
    def resolve_alias_target(
        self, 
        local_alias: str, 
        main_file: ASDLFile, 
        loaded_files: Dict[Path, ASDLFile]
    ) -> Optional[Tuple[str, str, Path]]:
        """
        Resolve a model alias to its target module information.
        
        Args:
            local_alias: Local alias name to resolve
            main_file: Main ASDL file with model_alias section
            loaded_files: Dictionary of loaded imported files
            
        Returns:
            Tuple of (import_alias, module_name, file_path) or None if resolution fails
        """
        if not main_file.model_alias or local_alias not in main_file.model_alias:
            return None
        
        qualified_ref = main_file.model_alias[local_alias]
        parsed = self.parse_qualified_reference(qualified_ref)
        if parsed is None:
            return None
        
        import_alias, module_name = parsed
        
        # Check import alias exists
        if not main_file.imports or import_alias not in main_file.imports:
            return None
        
        import_path = main_file.imports[import_alias]
        return import_alias, module_name, Path(import_path)
    
    def get_alias_suggestions(self, main_file: ASDLFile) -> Dict[str, List[str]]:
        """
        Get suggestions for alias resolution errors.
        
        Used for generating helpful error messages with available options.
        
        Args:
            main_file: Main ASDL file
            
        Returns:
            Dictionary with suggestion lists for error messages
        """
        suggestions = {
            "available_imports": list(main_file.imports.keys()) if main_file.imports else [],
            "available_aliases": list(main_file.model_alias.keys()) if main_file.model_alias else [],
            "local_modules": list(main_file.modules.keys()) if main_file.modules else []
        }
        
        return suggestions