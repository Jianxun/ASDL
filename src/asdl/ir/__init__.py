"""ASDL xDSL IR layers and conversions."""

from .converters.ast_to_nfir import convert_document

__all__ = ["convert_document"]
