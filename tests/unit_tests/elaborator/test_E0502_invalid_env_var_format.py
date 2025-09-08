import pytest
from src.asdl.elaborator.env_var_resolver import EnvVarResolver


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
def test_E0502_invalid_format_values_left_unchanged(value: str):
    resolver = EnvVarResolver()
    resolved, diagnostics = resolver.resolve_in_parameters(
        parameters={"W": value},
        owner_name="nfet_03v3",
        owner_kind="module",
        locatable=None,
    )

    assert any(d.code == "E0502" for d in diagnostics)
    assert resolved["W"] == value

