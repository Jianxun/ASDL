from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TopStyle(str, Enum):
    SUBCKT = "subckt"
    FLAT = "flat"


@dataclass
class GeneratorOptions:
    """Options to control SPICE generation behavior.

    Currently scaffolded for future phases. Defaults preserve pre-refactor behavior.
    """

    top_style: TopStyle = TopStyle.SUBCKT


