from .ast_to_nfir import convert_document
from .nfir_to_ifir import convert_design as convert_nfir_to_ifir

__all__ = ["convert_document", "convert_nfir_to_ifir"]
