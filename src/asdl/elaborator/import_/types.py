"""
Types for the ASDL import system.

Defines simple data structures used to pass information between
import coordination steps (dependency graph, validation, flattening).
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Set

from ...data_structures import ASDLFile


# Map of file path -> (import alias -> resolved absolute path or None if not found)
AliasResolutionMap = Dict[Path, Dict[str, Optional[Path]]]


@dataclass
class GraphNode:
    """A node in the import dependency graph."""
    file_path: Path
    asdl_file: ASDLFile
    # Raw imports as declared in the file (alias -> relative path string)
    imports: Dict[str, str] = field(default_factory=dict)
    # Resolved imports (alias -> absolute Path or None if unresolved)
    resolved_imports: Dict[str, Optional[Path]] = field(default_factory=dict)


@dataclass
class ImportGraph:
    """Directed graph of ASDL file import relationships."""
    # All nodes keyed by absolute file path
    nodes: Dict[Path, GraphNode] = field(default_factory=dict)
    # Edges keyed by node path to a set of dependency paths
    edges: Dict[Path, Set[Path]] = field(default_factory=dict)


