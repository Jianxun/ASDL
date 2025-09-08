"""
Import diagnostics for ASDL import system.

Provides structured diagnostic generation for import resolution errors
with E044x error codes and consistent messaging patterns.
"""

from pathlib import Path
from typing import List

from ...diagnostics import Diagnostic, DiagnosticSeverity


class ImportDiagnostics:
    """Handles generation of import-related diagnostic messages."""
    
    def __init__(self):
        """Initialize import diagnostics generator."""
        pass
    
    def create_file_not_found_error(
        self,
        import_alias: str,
        import_path: str, 
        search_paths: List[Path]
    ) -> Diagnostic:
        """
        Create E0441 diagnostic for import file not found.
        
        Args:
            import_alias: Import alias that failed to resolve
            import_path: Relative path that was being searched for
            search_paths: List of paths that were searched
            
        Returns:
            Diagnostic with E0441 error code
        """
        details = f"Import file '{import_path}' for alias '{import_alias}' was not found."
        
        if search_paths:
            search_path_list = "\n".join(f"  - {path}" for path in search_paths)
            details += f"\n\nSearched in the following locations:\n{search_path_list}"
        
        suggestion = (
            "Check that the file path is correct and the file exists. "
            "Ensure the ASDL_PATH environment variable includes the directory containing the file."
        )
        
        return Diagnostic(
            code="E0441",
            title="Import File Not Found",
            details=details,
            severity=DiagnosticSeverity.ERROR,
            suggestion=suggestion
        )
    
    def create_circular_import_error(self, import_cycle: List[Path]) -> Diagnostic:
        """
        Create E0442 diagnostic for circular import dependency.
        
        Args:
            import_cycle: List of file paths showing the circular dependency
            
        Returns:
            Diagnostic with E0442 error code
        """
        # Create human-readable cycle description
        cycle_names = [path.name for path in import_cycle]
        cycle_description = " → ".join(cycle_names)
        
        details = f"Circular import dependency detected: {cycle_description}"
        
        suggestion = (
            "Remove circular imports by restructuring module dependencies. "
            "Consider using forward references, moving common functionality to a separate module, "
            "or reorganizing the import hierarchy to eliminate cycles."
        )
        
        return Diagnostic(
            code="E0442",
            title="Circular Import Detected",
            details=details,
            severity=DiagnosticSeverity.ERROR,
            suggestion=suggestion
        )
    
    def create_module_not_found_error(
        self,
        module_name: str,
        import_alias: str,
        import_file_path: Path,
        available_modules: List[str]
    ) -> Diagnostic:
        """
        Create E0443 diagnostic for module not found in import.
        
        Args:
            module_name: Module name that was not found
            import_alias: Import alias being referenced
            import_file_path: Path to the imported file
            available_modules: List of modules available in the imported file
            
        Returns:
            Diagnostic with E0443 error code
        """
        details = (
            f"Module '{module_name}' was not found in imported file '{import_file_path}' "
            f"(import alias '{import_alias}')."
        )
        
        if available_modules:
            module_list = ", ".join(f"'{mod}'" for mod in available_modules)
            suggestion = f"Available modules in '{import_file_path}': {module_list}. Check the module name for typos."
        else:
            suggestion = f"The imported file '{import_file_path}' contains no modules. Verify the correct file is being imported."
        
        return Diagnostic(
            code="E0443",
            title="Module Not Found in Import",
            details=details,
            severity=DiagnosticSeverity.ERROR,
            suggestion=suggestion
        )
    
    def create_import_alias_not_found_error(
        self,
        unknown_alias: str,
        qualified_ref: str,
        available_imports: List[str]
    ) -> Diagnostic:
        """
        Create E0444 diagnostic for unknown import alias.
        
        Args:
            unknown_alias: Import alias that was not found
            qualified_ref: Full qualified reference that failed
            available_imports: List of available import aliases
            
        Returns:
            Diagnostic with E0444 error code
        """
        details = (
            f"Import alias '{unknown_alias}' in reference '{qualified_ref}' "
            f"is not declared in the imports section."
        )
        
        if available_imports:
            import_list = ", ".join(f"'{alias}'" for alias in available_imports)
            suggestion = f"Available import aliases: {import_list}. Check the import alias name for typos or add the missing import."
        else:
            suggestion = "No import aliases are currently declared. Add the required import to the imports section."
        
        return Diagnostic(
            code="E0444",
            title="Import Alias Not Found",
            details=details,
            severity=DiagnosticSeverity.ERROR,
            suggestion=suggestion
        )
    
    def create_model_alias_collision_error(
        self,
        conflicting_alias: str,
        import_alias: str,
        alias_target: str
    ) -> Diagnostic:
        """
        Create E0445 diagnostic for model alias collision.
        
        Args:
            conflicting_alias: Alias name that causes collision
            import_alias: Import alias that conflicts with the model alias
            alias_target: Target reference of the model alias
            
        Returns:
            Diagnostic with E0445 error code
        """
        details = (
            f"Model alias '{conflicting_alias}' collides with import alias name. "
            f"The model alias '{conflicting_alias}: {alias_target}' conflicts with "
            f"the import alias '{import_alias}'."
        )
        
        suggestion = (
            f"Rename the model alias '{conflicting_alias}' to a different name "
            f"to avoid collision with the import alias. "
            f"Model alias names must be unique from import alias names."
        )
        
        return Diagnostic(
            code="E0445",
            title="Model Alias Collision",
            details=details,
            severity=DiagnosticSeverity.ERROR,
            suggestion=suggestion
        )
    
    def create_invalid_model_alias_format_error(
        self,
        local_alias: str,
        invalid_reference: str
    ) -> Diagnostic:
        """
        Create E0448 diagnostic for invalid model alias format.
        
        Args:
            local_alias: Local alias name
            invalid_reference: Invalid qualified reference
            
        Returns:
            Diagnostic with E0448 error code
        """
        details = (
            f"Model alias '{local_alias}' has invalid qualified reference '{invalid_reference}'. "
            f"Expected format: 'import_alias.module_name'."
        )
        
        suggestion = (
            "Use the format 'import_alias.module_name' for model alias references. "
            "Both import_alias and module_name must be valid identifiers (letters, numbers, underscores, starting with letter or underscore)."
        )
        
        return Diagnostic(
            code="E0448",
            title="Invalid Model Alias Reference",
            details=details,
            severity=DiagnosticSeverity.ERROR,
            suggestion=suggestion
        )

    def create_invalid_qualified_reference_error(self, qualified_ref: str) -> Diagnostic:
        """
        Create E0448 diagnostic for invalid qualified reference format used by instances.

        Args:
            qualified_ref: Invalid qualified reference string

        Returns:
            Diagnostic with E0448 error code
        """
        details = (
            f"Invalid qualified reference '{qualified_ref}'. Expected format: 'import_alias.module_name'."
        )
        suggestion = (
            "Use the format 'import_alias.module_name' where both parts are valid identifiers."
        )
        return Diagnostic(
            code="E0448",
            title="Invalid Qualified Reference",
            details=details,
            severity=DiagnosticSeverity.ERROR,
            suggestion=suggestion
        )

    def create_unused_import_warning(self, import_alias: str) -> Diagnostic:
        """
        Create E0601 diagnostic for unused import alias.

        Args:
            import_alias: Import alias that is declared but never used

        Returns:
            Diagnostic with E0601 warning code
        """
        return Diagnostic(
            code="E0601",
            title="Unused Import Alias",
            details=f"Import alias '{import_alias}' is declared but never referenced by any instance model or model_alias.",
            severity=DiagnosticSeverity.WARNING,
            suggestion="Remove the unused import or reference it in a model or model_alias."
        )

    def create_unused_model_alias_warning(self, local_alias: str) -> Diagnostic:
        """
        Create E0602 diagnostic for unused model_alias entry.

        Args:
            local_alias: Local model alias name that is never used

        Returns:
            Diagnostic with E0602 warning code
        """
        return Diagnostic(
            code="E0602",
            title="Unused Model Alias",
            details=f"Model alias '{local_alias}' is declared but never used by any instance.",
            severity=DiagnosticSeverity.WARNING,
            suggestion="Remove the unused model_alias entry or update instances to use it."
        )

    def create_ambiguous_import_error(
        self,
        import_alias: str,
        import_path: str,
        candidate_paths: List[Path]
    ) -> Diagnostic:
        """
        Create E0447 diagnostic for ambiguous import resolution.

        Args:
            import_alias: Import alias being resolved
            import_path: Relative path specified in imports
            candidate_paths: List of matching files found across search roots

        Returns:
            Diagnostic with E0447 error code
        """
        candidates_list = "\n".join(f"  - {p}" for p in candidate_paths)
        details = (
            f"Ambiguous import resolution for alias '{import_alias}' and path '{import_path}'.\n\n"
            f"Multiple matching files were found:\n{candidates_list}"
        )
        suggestion = (
            "Disambiguate by adjusting ASDL_PATH or using a more specific relative path. "
            "Ensure only one intended copy is present in the effective search roots."
        )
        return Diagnostic(
            code="E0447",
            title="Ambiguous Import Resolution",
            details=details,
            severity=DiagnosticSeverity.ERROR,
            suggestion=suggestion
        )