"""
E0445: Model Alias Collision

Validates diagnostic creation for collisions between model alias and import alias.
"""

from asdl.elaborator.import_.diagnostics import ImportDiagnostics
from asdl.diagnostics import DiagnosticSeverity


class TestE0445ModelAliasCollision:
    def test_diagnostic_generation(self):
        diag_gen = ImportDiagnostics()
        conflicting_alias = "std_lib"
        import_alias = "std_lib"
        alias_target = "other_lib.some_module"

        diagnostic = diag_gen.create_model_alias_collision_error(
            conflicting_alias, import_alias, alias_target
        )

        assert diagnostic.code == "E0445"
        assert diagnostic.title == "Model Alias Collision"
        assert diagnostic.severity == DiagnosticSeverity.ERROR
        assert conflicting_alias in diagnostic.details
        assert "collides with import alias" in diagnostic.details
        assert alias_target in diagnostic.details
        assert "rename the model alias" in diagnostic.suggestion.lower()
        assert "avoid collision" in diagnostic.suggestion.lower()


