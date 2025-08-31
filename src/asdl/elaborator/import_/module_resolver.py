"""
Module resolver for ASDL import system.

Handles three-step module resolution: local modules → model_alias → imported modules.
Provides module reference validation and detailed source information.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import re

from ...data_structures import ASDLFile, Module
from .file_loader import FileLoader


class ModuleResolver:
    """Handles cross-file module lookup and resolution."""
    
    # Pattern for validating qualified references (import_alias.module_name)
    QUALIFIED_REFERENCE_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*$')
    
    def __init__(self, file_loader: Optional[FileLoader] = None):
        """
        Initialize module resolver.
        
        Args:
            file_loader: Optional file loader instance. Creates default if None.
        """
        self.file_loader = file_loader or FileLoader()
    
    def resolve_module_reference(
        self,
        module_ref: str,
        main_file: ASDLFile,
        loaded_files: Dict[Path, ASDLFile]
    ) -> Optional[Tuple[Module, Dict[str, Any]]]:
        """
        Resolve module reference using three-step lookup.
        
        Resolution order (first match wins):
        1. Local modules in main_file
        2. model_alias mappings to imported modules
        3. Qualified imports (import_alias.module_name)
        
        Args:
            module_ref: Module reference to resolve
            main_file: Main ASDL file with imports and local modules
            loaded_files: Cache of already loaded imported files
            
        Returns:
            Tuple of (resolved_module, source_info) or None if not found
            source_info contains details about resolution source for diagnostics
        """
        # Step 1: Check local modules (highest priority)
        if main_file.modules and module_ref in main_file.modules:
            return self._resolve_local_module(module_ref, main_file)
        
        # Step 2: Check model_alias mappings
        if main_file.model_alias and module_ref in main_file.model_alias:
            return self._resolve_model_alias(module_ref, main_file, loaded_files)
        
        # Step 3: Check qualified imports (import_alias.module_name)
        if self._is_qualified_reference(module_ref):
            return self._resolve_qualified_import(module_ref, main_file, loaded_files)
        
        # Module not found in any step
        return None
    
    def _resolve_local_module(
        self, 
        module_ref: str, 
        main_file: ASDLFile
    ) -> Tuple[Module, Dict[str, Any]]:
        """
        Resolve module from local module definitions.
        
        Args:
            module_ref: Module reference name
            main_file: Main ASDL file
            
        Returns:
            Tuple of (module, source_info)
        """
        module = main_file.modules[module_ref]
        source_info = {
            "source": "local",
            "module_name": module_ref,
            "file": main_file
        }
        return module, source_info
    
    def _resolve_model_alias(
        self,
        module_ref: str,
        main_file: ASDLFile, 
        loaded_files: Dict[Path, ASDLFile]
    ) -> Optional[Tuple[Module, Dict[str, Any]]]:
        """
        Resolve module through model_alias mapping.
        
        Args:
            module_ref: Local alias name
            main_file: Main ASDL file
            loaded_files: Cache of loaded imported files
            
        Returns:
            Tuple of (module, source_info) or None if resolution fails
        """
        qualified_ref = main_file.model_alias[module_ref]
        
        # Parse qualified reference (import_alias.module_name)
        if not self._is_qualified_reference(qualified_ref):
            return None  # Invalid format
        
        import_alias, module_name = qualified_ref.split('.', 1)
        
        # Look up the imported file
        resolved_module, imported_file = self._lookup_in_imported_file(
            import_alias, module_name, main_file, loaded_files
        )
        
        if resolved_module is None:
            return None  # Module not found in imported file
        
        source_info = {
            "source": "model_alias",
            "alias": module_ref,
            "qualified_ref": qualified_ref,
            "import_alias": import_alias,
            "module_name": module_name,
            "file": imported_file
        }
        return resolved_module, source_info
    
    def _resolve_qualified_import(
        self,
        module_ref: str,
        main_file: ASDLFile,
        loaded_files: Dict[Path, ASDLFile]
    ) -> Optional[Tuple[Module, Dict[str, Any]]]:
        """
        Resolve qualified module reference (import_alias.module_name).
        
        Args:
            module_ref: Qualified reference (import_alias.module_name)
            main_file: Main ASDL file
            loaded_files: Cache of loaded imported files
            
        Returns:
            Tuple of (module, source_info) or None if resolution fails
        """
        import_alias, module_name = module_ref.split('.', 1)
        
        # Look up the imported file
        resolved_module, imported_file = self._lookup_in_imported_file(
            import_alias, module_name, main_file, loaded_files
        )
        
        if resolved_module is None:
            return None  # Module not found in imported file
        
        source_info = {
            "source": "qualified_import",
            "qualified_ref": module_ref,
            "import_alias": import_alias,
            "module_name": module_name,
            "file": imported_file
        }
        return resolved_module, source_info
    
    def _lookup_in_imported_file(
        self,
        import_alias: str,
        module_name: str,
        main_file: ASDLFile,
        loaded_files: Dict[Path, ASDLFile]
    ) -> Tuple[Optional[Module], Optional[ASDLFile]]:
        """
        Look up module in imported file by import alias.
        
        Args:
            import_alias: Import alias to resolve
            module_name: Module name within imported file
            main_file: Main ASDL file with imports
            loaded_files: Cache of loaded imported files
            
        Returns:
            Tuple of (module_or_None, imported_file_or_None)
        """
        # Check if import alias exists
        if not main_file.imports or import_alias not in main_file.imports:
            return None, None
        
        import_path = main_file.imports[import_alias]
        import_path_obj = Path(import_path)
        
        # Check if file is already loaded
        imported_file = loaded_files.get(import_path_obj)
        if imported_file is None:
            return None, None  # File not loaded (should be handled by orchestrator)
        
        # Look up module in imported file
        if not imported_file.modules or module_name not in imported_file.modules:
            return None, imported_file  # Module not found in file
        
        module = imported_file.modules[module_name]
        return module, imported_file
    
    def _is_qualified_reference(self, module_ref: str) -> bool:
        """
        Check if module reference is a qualified import (import_alias.module_name).
        
        Args:
            module_ref: Module reference to check
            
        Returns:
            True if qualified reference, False otherwise
        """
        if not module_ref or '.' not in module_ref:
            return False
        
        # Validate format using regex
        return bool(self.QUALIFIED_REFERENCE_PATTERN.match(module_ref))
    
    def get_resolution_candidates(
        self, 
        module_ref: str, 
        main_file: ASDLFile
    ) -> Dict[str, Any]:
        """
        Get information about possible resolution candidates for diagnostics.
        
        Used for generating helpful error messages when module resolution fails.
        
        Args:
            module_ref: Module reference that failed to resolve
            main_file: Main ASDL file
            
        Returns:
            Dictionary with candidate information for error messages
        """
        candidates = {
            "local_modules": list(main_file.modules.keys()) if main_file.modules else [],
            "model_aliases": list(main_file.model_alias.keys()) if main_file.model_alias else [],
            "import_aliases": list(main_file.imports.keys()) if main_file.imports else [],
            "is_qualified": self._is_qualified_reference(module_ref)
        }
        
        if candidates["is_qualified"] and '.' in module_ref:
            import_alias, module_name = module_ref.split('.', 1)
            candidates["parsed_import_alias"] = import_alias
            candidates["parsed_module_name"] = module_name
            candidates["import_alias_exists"] = import_alias in (main_file.imports or {})
        
        return candidates