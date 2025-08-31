import os
from typing import Dict, Any

import pytest

from src.asdl.elaborator.diagnostics import create_elaborator_diagnostic  # noqa: F401  # ensure module importable


def _make_params(**kwargs: Any) -> Dict[str, Any]:
    return dict(**kwargs)


class TestEnvVarResolution:
    def setup_method(self):
        # Ensure a clean environment for each test
        for key in ["WIDTH", "CORNER", "TEMP"]:
            if key in os.environ:
                del os.environ[key]

    def test_resolves_valid_env_reference_in_parameters(self):
        from src.asdl.elaborator.env_var_resolver import EnvVarResolver

        os.environ["WIDTH"] = "6u"
        params = _make_params(L="0.28u", W="${WIDTH}", M=1)

        resolver = EnvVarResolver()
        resolved, diagnostics = resolver.resolve_in_parameters(
            parameters=params,
            owner_name="nfet_03v3",
            owner_kind="module",
            locatable=None,
        )

        assert diagnostics == []
        assert resolved["L"] == "0.28u"
        assert resolved["W"] == "6u"
        assert resolved["M"] == 1

    @pytest.mark.parametrize(
        "value",
        [
            "$WIDTH",
            "${WIDTH:-3u}",
            "${WIDTH}/path",
            "${WIDTH}x",
            "x${WIDTH}",
        ],
    )
    def test_invalid_formats_emit_E0502_and_leave_value_unchanged(self, value: str):
        from src.asdl.elaborator.env_var_resolver import EnvVarResolver

        params = _make_params(W=value)

        resolver = EnvVarResolver()
        resolved, diagnostics = resolver.resolve_in_parameters(
            parameters=params,
            owner_name="nfet_03v3",
            owner_kind="module",
            locatable=None,
        )

        assert any(d.code == "E0502" for d in diagnostics)
        assert resolved["W"] == value

    def test_missing_env_emits_E0501(self):
        from src.asdl.elaborator.env_var_resolver import EnvVarResolver

        params = _make_params(W="${WIDTH}")

        resolver = EnvVarResolver()
        resolved, diagnostics = resolver.resolve_in_parameters(
            parameters=params,
            owner_name="nfet_03v3",
            owner_kind="module",
            locatable=None,
        )

        assert any(d.code == "E0501" for d in diagnostics)
        # Value remains unchanged on error
        assert resolved["W"] == "${WIDTH}"

    def test_non_string_parameter_values_are_unchanged(self):
        from src.asdl.elaborator.env_var_resolver import EnvVarResolver

        params = _make_params(M=2, SCALE=1.5, FLAG=True)

        resolver = EnvVarResolver()
        resolved, diagnostics = resolver.resolve_in_parameters(
            parameters=params,
            owner_name="nfet_03v3",
            owner_kind="module",
            locatable=None,
        )

        assert diagnostics == []
        assert resolved["M"] == 2
        assert resolved["SCALE"] == 1.5
        assert resolved["FLAG"] is True


