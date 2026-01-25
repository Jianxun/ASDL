from .ast_to_graphir import convert_document, convert_import_graph
from .graphir_to_ifir import convert_program as convert_graphir_to_ifir

__all__ = ["convert_document", "convert_graphir_to_ifir", "convert_import_graph"]
