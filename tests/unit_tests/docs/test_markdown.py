from pathlib import Path

from asdl.docs.markdown import render_markdown_from_file


SWMATRIX_TGATE = Path("examples/libs/sw_matrix/swmatrix_Tgate/swmatrix_Tgate.asdl")
FULL_SWITCH = Path(
    "examples/libs/sw_matrix/full_switch_matrix_130_by_25/"
    "full_switch_matrix_130_by_25.asdl"
)


def test_render_markdown_swmatrix_tgate() -> None:
    markdown = render_markdown_from_file(SWMATRIX_TGATE)
    lines = markdown.splitlines()

    assert lines[0] == "# swmatrix_Tgate"
    assert "## Overview" in markdown
    assert "Transimssion gate analog switch for MOSbius V3 switch Matrix" in markdown
    assert "### Interface" in markdown
    assert "| $VDDd |" in markdown
    assert "nominal 3.3V" in markdown

    assert "Transmission-gate switch with control logic." in markdown
    assert "### Instances" in markdown
    assert "| mp | gf.pfet_03v3 | L={L} W={W} NF={NF} m=3 | PMOS/NMOS ratio is 3:1 |" in markdown

    assert "### Nets" in markdown
    assert "| net1 | nand2.Y, inv1.A | intermediate node for control signal |" in markdown


def test_render_markdown_full_switch_matrix_sections() -> None:
    markdown = render_markdown_from_file(FULL_SWITCH)

    assert "#### data chain" in markdown
    assert "#### clock broadcast" in markdown
    assert "#### buses and pins" in markdown
    assert "#### power" in markdown

    section_index = markdown.index("#### buses and pins")
    assert "| $BUS<@BUS> |" in markdown[section_index:]
    assert "bus broadcast to all rows" in markdown
