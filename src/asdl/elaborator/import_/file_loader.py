"""
File loader for ASDL import system.

Handles file loading with caching, circular dependency detection,
and integration with the ASDL parser system.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading

from ...data_structures import ASDLFile
from ...diagnostics import Diagnostic, DiagnosticSeverity
from ...parser import ASDLParser


class FileLoader:
    """Handles file loading with caching and circular dependency detection."""
    
    def __init__(self, parser: Optional[ASDLParser] = None):
        """
        Initialize file loader.
        
        Args:
            parser: Optional ASDL parser instance. Creates default if None.
        """
        self.parser = parser or ASDLParser()
        self._cache: Dict[Path, Tuple[Optional[ASDLFile], List[Diagnostic]]] = {}
        self._cache_lock = threading.Lock()  # Thread-safe caching for future parallel processing
    
    def load_file(self, file_path: Path) -> Tuple[Optional[ASDLFile], List[Diagnostic]]:
        """
        Load ASDL file with caching.
        
        Files are cached after first load to avoid duplicate parsing.
        Returns cached result on subsequent loads of the same file.
        
        Args:
            file_path: Absolute path to ASDL file to load
            
        Returns:
            Tuple of (ASDLFile or None, list of diagnostics)
        """
        # Normalize path to ensure consistent caching
        normalized_path = file_path.resolve()
        
        # Check cache first
        with self._cache_lock:
            if normalized_path in self._cache:
                return self._cache[normalized_path]
        
        # Load and cache result
        result = self._load_file_uncached(normalized_path)
        
        with self._cache_lock:
            self._cache[normalized_path] = result
            
        return result
    
    def load_file_with_dependency_check(
        self, 
        file_path: Path, 
        loading_stack: Optional[List[Path]] = None
    ) -> Tuple[Optional[ASDLFile], List[Diagnostic]]:
        """
        Load file with circular dependency detection.
        
        Maintains a loading stack to detect circular imports during
        recursive loading process.
        
        Args:
            file_path: Absolute path to ASDL file to load
            loading_stack: Stack of currently loading files for circular detection
            
        Returns:
            Tuple of (ASDLFile or None, list of diagnostics)
        """
        normalized_path = file_path.resolve()
        
        if loading_stack is None:
            loading_stack = []
        else:
            # Normalize stack paths for reliable identity checks
            loading_stack = [p.resolve() for p in loading_stack]
        
        # Check for circular dependency
        if normalized_path in loading_stack:
            return self._create_circular_dependency_error(normalized_path, loading_stack)
        
        # Check cache first (before adding to loading stack)
        with self._cache_lock:
            if normalized_path in self._cache:
                return self._cache[normalized_path]
        
        # Add to loading stack for circular detection
        loading_stack.append(normalized_path)
        
        try:
            # Load file
            result = self._load_file_uncached(normalized_path)
            
            # Cache result
            with self._cache_lock:
                self._cache[normalized_path] = result
                
            return result
            
        finally:
            # Remove from loading stack
            loading_stack.pop()
    
    def _load_file_uncached(self, file_path: Path) -> Tuple[Optional[ASDLFile], List[Diagnostic]]:
        """
        Load file without checking cache.
        
        Args:
            file_path: Absolute path to ASDL file to load
            
        Returns:
            Tuple of (ASDLFile or None, list of diagnostics)
        """
        # Check if file exists
        if not file_path.exists():
            diagnostic = Diagnostic(
                code="E0441",
                title="Import File Not Found",
                details=f"Import file '{file_path}' does not exist.",
                severity=DiagnosticSeverity.ERROR,
                suggestion=f"Check that the file path is correct and the file exists."
            )
            return None, [diagnostic]
        
        # Use parser to load file
        try:
            return self.parser.parse_file(str(file_path))
        except Exception as e:
            # Handle unexpected parser errors (load/parse failures)
            diagnostic = Diagnostic(
                code="E0446",
                title="Import File Load/Parse Failure", 
                details=f"Failed to load or parse import file '{file_path}': {e}",
                severity=DiagnosticSeverity.ERROR
            )
            return None, [diagnostic]
    
    def _create_circular_dependency_error(
        self, 
        current_file: Path, 
        loading_stack: List[Path]
    ) -> Tuple[None, List[Diagnostic]]:
        """
        Create diagnostic for circular dependency detection.
        
        Args:
            current_file: File that would create the cycle
            loading_stack: Current loading stack showing the cycle
            
        Returns:
            Tuple of (None, [circular dependency diagnostic])
        """
        # Find where the cycle starts
        cycle_start_index = loading_stack.index(current_file)
        cycle_files = loading_stack[cycle_start_index:] + [current_file]
        
        # Create human-readable cycle description
        cycle_description = " → ".join([f.name for f in cycle_files])
        
        diagnostic = Diagnostic(
            code="E0442",
            title="Circular Import Detected",
            details=f"Circular import dependency detected: {cycle_description}",
            severity=DiagnosticSeverity.ERROR,
            suggestion="Remove circular imports by restructuring module dependencies or using forward references."
        )
        
        return None, [diagnostic]
    
    def clear_cache(self) -> None:
        """
        Clear the file cache.
        
        Useful for testing or when files may have changed on disk.
        """
        with self._cache_lock:
            self._cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics for debugging/monitoring.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._cache_lock:
            return {
                "cached_files": len(self._cache),
                "cache_hits": 0,  # Could be tracked in future enhancement
                "cache_misses": 0  # Could be tracked in future enhancement
            }