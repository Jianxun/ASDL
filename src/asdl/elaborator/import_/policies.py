"""
Policies and options for the import flattening process.

Focuses on merge precedence and optional metadata retention.
"""

from enum import Enum
from dataclasses import dataclass


class PrecedencePolicy(Enum):
    """Merge precedence policy for conflicting module names."""
    LOCAL_WINS = "local_wins"
    IMPORT_WINS = "import_wins"


@dataclass
class FlattenOptions:
    """Options to control flattening behavior."""
    # When True, drop imports/model_alias metadata in the flattened artifact
    drop_metadata: bool = False


