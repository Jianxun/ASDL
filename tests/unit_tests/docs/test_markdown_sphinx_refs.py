from pathlib import Path

from asdl.docs.markdown import render_markdown_from_file

SWMATRIX_TGATE = Path("examples/libs/sw_matrix/swmatrix_Tgate/swmatrix_Tgate.asdl")


def test_markdown_emits_asdl_sphinx_refs() -> None:
    markdown = render_markdown_from_file(SWMATRIX_TGATE)

    assert "(swmatrix_Tgate_doc)=" in markdown
    assert "```{asdl:doc} swmatrix_Tgate_doc" in markdown
    assert "```{asdl:module} swmatrix_Tgate" in markdown
    assert "```{asdl:import} swmatrix_Tgate::gf_std" in markdown
    assert "```{asdl:port} swmatrix_Tgate::$VDDd" in markdown
    assert "```{asdl:net} swmatrix_Tgate::net1" in markdown
    assert "```{asdl:inst} swmatrix_Tgate::mp" in markdown
    assert "```{asdl:var} swmatrix_Tgate::L" in markdown
