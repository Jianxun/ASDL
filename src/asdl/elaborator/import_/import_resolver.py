"""
Import resolver orchestrator for ASDL import system.

Main component that coordinates all import resolution including file loading,
dependency resolution, and flattening into a single ASDLFile output.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import replace

from ...data_structures import ASDLFile
from ...diagnostics import Diagnostic
from ...parser import ASDLParser
from .path_resolver import PathResolver
from .file_loader import FileLoader
from .module_resolver import ModuleResolver
from .alias_resolver import AliasResolver
from .diagnostics import ImportDiagnostics


class ImportResolver:
    """Main orchestrator for import resolution workflow."""
    
    def __init__(
        self,
        parser: Optional[ASDLParser] = None,
        path_resolver: Optional[PathResolver] = None,
        file_loader: Optional[FileLoader] = None,
        module_resolver: Optional[ModuleResolver] = None,
        alias_resolver: Optional[AliasResolver] = None,
        diagnostics: Optional[ImportDiagnostics] = None
    ):
        """
        Initialize import resolver with dependency injection.
        
        Args:
            parser: Optional ASDL parser instance
            path_resolver: Optional path resolver instance
            file_loader: Optional file loader instance
            module_resolver: Optional module resolver instance  
            alias_resolver: Optional alias resolver instance
            diagnostics: Optional diagnostics generator instance
        """
        self.parser = parser or ASDLParser()
        self.path_resolver = path_resolver or PathResolver()
        self.file_loader = file_loader or FileLoader(self.parser)
        self.module_resolver = module_resolver or ModuleResolver(self.file_loader)
        self.alias_resolver = alias_resolver or AliasResolver()
        self.diagnostics = diagnostics or ImportDiagnostics()
    
    def resolve_imports(
        self,
        main_file_path: Path,
        search_paths: Optional[List[Path]] = None
    ) -> Tuple[Optional[ASDLFile], List[Diagnostic]]:
        """
        Resolve all imports for a main ASDL file.
        
        Performs complete import resolution workflow:
        1. Parse main file
        2. Discover and load all import dependencies recursively
        3. Validate import references and aliases
        4. Flatten all modules into single ASDLFile output
        
        Args:
            main_file_path: Path to main ASDL file
            search_paths: Optional list of search paths for import resolution
            
        Returns:
            Tuple of (flattened_asdl_file, diagnostics_list)
        """
        all_diagnostics = []
        
        # Step 1: Parse main file
        main_file, parse_diagnostics = self.parser.parse_file(str(main_file_path))
        all_diagnostics.extend(parse_diagnostics)
        
        if main_file is None:
            return None, all_diagnostics
        
        # Step 2: Resolve search paths
        if search_paths is None:
            search_paths = self.path_resolver.get_search_paths()
        
        # Step 3: Load all import dependencies
        loaded_files, alias_resolution_map, load_diagnostics = self._load_all_dependencies(
            main_file, search_paths, main_file_path
        )
        all_diagnostics.extend(load_diagnostics)
        
        # Step 4: Validate import references and aliases
        validation_diagnostics = self._validate_imports_and_aliases(
            main_file, main_file_path, loaded_files, alias_resolution_map
        )
        all_diagnostics.extend(validation_diagnostics)
        
        # Step 5: Flatten all modules into single output file
        flattened_file = self._flatten_modules(main_file, loaded_files)
        
        return flattened_file, all_diagnostics
    
    def _load_all_dependencies(
        self,
        main_file: ASDLFile,
        search_paths: List[Path],
        main_file_path: Path
    ) -> Tuple[Dict[Path, ASDLFile], Dict[Path, Dict[str, Optional[Path]]], List[Diagnostic]]:
        """
        Load all import dependencies recursively with circular detection.
        
        Uses recursive approach with proper loading stack maintenance
        for accurate circular dependency detection.
        
        Args:
            main_file: Main ASDL file with imports
            search_paths: List of paths to search for imports
            main_file_path: Path to main file (for circular detection)
            
        Returns:
            Tuple of (loaded_files_dict, diagnostics_list)
        """
        loaded_files: Dict[Path, ASDLFile] = {}
        # Map of file path -> (import alias -> resolved path or None if not found)
        alias_resolution_map: Dict[Path, Dict[str, Optional[Path]]] = {}
        all_diagnostics = []
        
        # Use recursive helper for proper circular detection
        self._load_file_recursive(
            main_file, main_file_path, search_paths,
            loaded_files, alias_resolution_map, all_diagnostics, []
        )
        
        return loaded_files, alias_resolution_map, all_diagnostics
    
    def _load_file_recursive(
        self,
        current_file: ASDLFile,
        current_path: Path,
        search_paths: List[Path],
        loaded_files: Dict[Path, ASDLFile],
        alias_resolution_map: Dict[Path, Dict[str, Optional[Path]]],
        all_diagnostics: List[Diagnostic],
        loading_stack: List[Path]
    ) -> None:
        """
        Recursively load file dependencies with circular detection.
        
        Args:
            current_file: Current file being processed
            current_path: Path to current file
            search_paths: List of search paths
            loaded_files: Dictionary to populate with loaded files
            all_diagnostics: List to append diagnostics to
            loading_stack: Stack for circular dependency detection
        """
        # Process imports in current file
        if not current_file.imports:
            return
        # Initialize alias map for this file
        if current_path not in alias_resolution_map:
            alias_resolution_map[current_path] = {}
            
        for import_alias, import_path in current_file.imports.items():
            # Resolve import path
            resolved_path = self.path_resolver.resolve_file_path(
                import_path, search_paths
            )
            # Record resolution result (could be None)
            alias_resolution_map[current_path][import_alias] = resolved_path
            
            if resolved_path is None:
                # File not found
                diagnostic = self.diagnostics.create_file_not_found_error(
                    import_alias, import_path, search_paths
                )
                all_diagnostics.append(diagnostic)
                continue
            
            # Check for circular dependency first (before cache check)
            if resolved_path in loading_stack + [current_path]:
                # Circular import detected - create cycle including the current attempt
                cycle_stack = loading_stack + [current_path, resolved_path]
                diagnostic = self.diagnostics.create_circular_import_error(cycle_stack)
                all_diagnostics.append(diagnostic)
                continue
            
            # Check if already loaded (after circular check)
            if resolved_path in loaded_files:
                continue
            
            # Load with circular dependency detection using current loading stack
            loaded_file, load_diagnostics = self.file_loader.load_file_with_dependency_check(
                resolved_path, loading_stack + [current_path]
            )
            all_diagnostics.extend(load_diagnostics)
            
            if loaded_file is not None:
                loaded_files[resolved_path] = loaded_file
                # Recursively process imports in loaded file
                self._load_file_recursive(
                    loaded_file, resolved_path, search_paths,
                    loaded_files, alias_resolution_map, all_diagnostics, loading_stack + [current_path]
                )
    
    def _validate_imports_and_aliases(
        self,
        main_file: ASDLFile,
        main_file_path: Path,
        loaded_files: Dict[Path, ASDLFile],
        alias_resolution_map: Dict[Path, Dict[str, Optional[Path]]]
    ) -> List[Diagnostic]:
        """
        Validate import references and model aliases.
        
        Args:
            main_file: Main ASDL file
            loaded_files: Dictionary of loaded import files
            
        Returns:
            List of validation diagnostics
        """
        diagnostics = []
        
        # Validate model aliases
        alias_diagnostics = self.alias_resolver.validate_model_aliases(
            main_file, loaded_files
        )
        diagnostics.extend(alias_diagnostics)
        
        # Validate qualified module references in instances (E0443/E0444)
        diagnostics.extend(self._validate_instance_model_references(
            main_file, main_file_path, loaded_files, alias_resolution_map
        ))
        
        return diagnostics

    def _validate_instance_model_references(
        self,
        main_file: ASDLFile,
        main_file_path: Path,
        loaded_files: Dict[Path, ASDLFile],
        alias_resolution_map: Dict[Path, Dict[str, Optional[Path]]]
    ) -> List[Diagnostic]:
        """
        Validate instance model references that use qualified import alias syntax.
        Emits E0444 when the import alias is unknown and E0443 when the module
        is not found in the imported file.
        """
        diagnostics: List[Diagnostic] = []

        # Build iterable of (file_path, asdl_file) to validate: main + all imported
        files_to_scan: List[Tuple[Path, ASDLFile]] = [(main_file_path, main_file)]
        files_to_scan.extend(list(loaded_files.items()))

        for file_path, asdl_file in files_to_scan:
            if not asdl_file.modules:
                continue
            imports_for_file: Dict[str, str] = asdl_file.imports or {}
            available_imports = list(imports_for_file.keys())
            alias_map_for_file = alias_resolution_map.get(file_path, {})

            for module in asdl_file.modules.values():
                instances = getattr(module, "instances", None)
                if not instances:
                    continue
                for inst in instances.values():
                    model_ref = getattr(inst, "model", None)
                    if not isinstance(model_ref, str) or '.' not in model_ref:
                        continue
                    # Qualified reference "alias.module"
                    alias, module_name = model_ref.split('.', 1)
                    if alias not in imports_for_file:
                        diagnostics.append(
                            self.diagnostics.create_import_alias_not_found_error(
                                alias, model_ref, available_imports
                            )
                        )
                        continue
                    # Resolve alias to file path used during loading
                    resolved_path = alias_map_for_file.get(alias)
                    imported_file = loaded_files.get(resolved_path) if resolved_path else None
                    available_modules: List[str] = []
                    if imported_file and imported_file.modules:
                        available_modules = list(imported_file.modules.keys())
                    if imported_file is None or module_name not in (imported_file.modules or {}):
                        # Use resolved path if available, else fallback to raw path string
                        import_file_path = resolved_path if resolved_path else Path(imports_for_file[alias])
                        diagnostics.append(
                            self.diagnostics.create_module_not_found_error(
                                module_name, alias, import_file_path, available_modules
                            )
                        )

        return diagnostics
    
    def _flatten_modules(
        self,
        main_file: ASDLFile,
        loaded_files: Dict[Path, ASDLFile]
    ) -> ASDLFile:
        """
        Flatten all modules from imported files into single ASDLFile.
        
        Combines modules from main file and all imported files while
        preserving import and model_alias information for reference.
        
        Args:
            main_file: Main ASDL file
            loaded_files: Dictionary of loaded imported files
            
        Returns:
            Flattened ASDLFile with all modules combined
        """
        # Helper to rewrite instance model references
        def _rewrite_module_instance_models(module, file_model_alias):
            # Make a shallow copy with new instances mapping if present
            if module.instances is None:
                return module
            new_instances = {}
            for inst_id, inst in module.instances.items():
                model_name = inst.model
                # 1) Strip qualified import alias (e.g., op.mod -> mod)
                if isinstance(model_name, str) and '.' in model_name:
                    model_name = model_name.split('.', 1)[1]
                # 2) Apply file-local model_alias mapping (e.g., nmos -> prim.nfet_03v3 -> nfet_03v3)
                if file_model_alias and model_name in file_model_alias:
                    qualified_ref = file_model_alias[model_name]
                    if '.' in qualified_ref:
                        model_name = qualified_ref.split('.', 1)[1]
                    else:
                        model_name = qualified_ref
                new_instances[inst_id] = replace(inst, model=model_name)
            return replace(module, instances=new_instances)

        # Start with main file modules (apply stripping of qualified refs and local model_alias if any)
        all_modules = {}
        if main_file.modules:
            for name, module in main_file.modules.items():
                all_modules[name] = _rewrite_module_instance_models(module, main_file.model_alias)
        
        # Add modules from all imported files, applying their own model_alias rewriting
        for imported_file in loaded_files.values():
            if imported_file.modules:
                for module_name, module in imported_file.modules.items():
                    # Handle potential module name conflicts
                    if module_name in all_modules:
                        # For now, imported modules override local ones
                        # In future, this could generate a warning
                        pass
                    all_modules[module_name] = _rewrite_module_instance_models(module, imported_file.model_alias)
        
        # Create flattened file preserving original metadata
        flattened_file = replace(
            main_file,
            modules=all_modules
            # Note: imports and model_alias are preserved for reference
        )
        
        return flattened_file
    
    def get_loaded_file_info(self) -> Dict[str, any]:
        """
        Get information about loaded files for debugging/monitoring.
        
        Returns:
            Dictionary with loading statistics and file information
        """
        # Delegate to file_loader for cache stats
        return self.file_loader.get_cache_stats()
    
    def clear_cache(self) -> None:
        """
        Clear all internal caches.
        
        Useful for testing or when files may have changed on disk.
        """
        self.file_loader.clear_cache()