import os
from src.asdl.elaborator.env_var_resolver import EnvVarResolver


def test_E0501_env_var_not_found_in_parameters():
    if "WIDTH" in os.environ:
        del os.environ["WIDTH"]

    resolver = EnvVarResolver()
    resolved, diagnostics = resolver.resolve_in_parameters(
        parameters={"W": "${WIDTH}"},
        owner_name="nfet_03v3",
        owner_kind="module",
        locatable=None,
    )

    assert any(d.code == "E0501" for d in diagnostics)
    assert resolved["W"] == "${WIDTH}"

