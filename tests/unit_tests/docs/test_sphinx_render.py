from pathlib import Path

from docutils import nodes

from asdl.ast.parser import parse_file
from asdl.docs.docstrings import extract_docstrings_from_file
from asdl.docs.sphinx_render import render_docutils


SWMATRIX_TGATE = Path("examples/libs/sw_matrix/swmatrix_Tgate/swmatrix_Tgate.asdl")
FULL_SWITCH = Path(
    "examples/libs/sw_matrix/full_switch_matrix_130_by_25/"
    "full_switch_matrix_130_by_25.asdl"
)


def _render_docutils(path: Path) -> nodes.section:
    document, diagnostics = parse_file(str(path))
    assert diagnostics == []
    assert document is not None
    docstrings = extract_docstrings_from_file(path)
    return render_docutils(document, docstrings, file_path=path)


def _section_titles(node: nodes.Node) -> list[str]:
    titles: list[str] = []
    for section in node.findall(nodes.section):
        if not section:
            continue
        if isinstance(section[0], nodes.title):
            titles.append(section[0].astext())
    return titles


def _table_headers(table: nodes.table) -> list[str]:
    thead = next(table.findall(nodes.thead), None)
    if thead is None:
        return []
    row = next(thead.findall(nodes.row), None)
    if row is None:
        return []
    return [entry.astext() for entry in row.findall(nodes.entry)]


def _find_section(node: nodes.Node, title: str) -> nodes.section | None:
    for section in node.findall(nodes.section):
        if not section:
            continue
        if isinstance(section[0], nodes.title) and section[0].astext() == title:
            return section
    return None


def _find_sections(node: nodes.Node, title: str) -> list[nodes.section]:
    matches: list[nodes.section] = []
    for section in node.findall(nodes.section):
        if not section:
            continue
        if isinstance(section[0], nodes.title) and section[0].astext() == title:
            matches.append(section)
    return matches


def test_sphinx_render_swmatrix_structure_and_content() -> None:
    rendered = _render_docutils(SWMATRIX_TGATE)
    titles = _section_titles(rendered)

    assert titles[0] == "swmatrix_Tgate.asdl"
    assert "Top module" not in titles
    assert "Imports" in titles
    assert "Modules" in titles
    assert "swmatrix_Tgate" in titles
    assert "Overview" in titles
    assert "Interface" in titles
    assert "Variables" in titles
    assert "Instances" in titles
    assert "Nets" in titles
    assert titles.index("Imports") < titles.index("Modules")
    assert titles.index("Modules") < titles.index("swmatrix_Tgate")
    overview_indices = [
        index for index, title in enumerate(titles) if title == "Overview"
    ]
    assert len(overview_indices) >= 2
    assert overview_indices[0] < titles.index("Imports")
    assert titles.index("swmatrix_Tgate") < overview_indices[1]

    text = rendered.astext()
    assert "Transimssion gate analog switch for MOSbius V3 switch Matrix" in text
    assert "Transmission-gate switch with control logic." in text
    assert "nominal 3.3V" in text
    assert "PMOS/NMOS ratio is 3:1" in text
    assert "net1" in text
    assert "nand2.Y, inv1.A" in text

    headers = {tuple(_table_headers(table)) for table in rendered.findall(nodes.table)}
    assert ("Alias", "Path", "Description") in headers
    assert ("Name", "Description") in headers
    assert ("Name", "Default", "Description") in headers
    assert ("Instance", "Ref", "Params", "Description") in headers
    assert ("Name", "Endpoints", "Description") in headers


def test_sphinx_render_full_switch_sections() -> None:
    rendered = _render_docutils(FULL_SWITCH)
    titles = _section_titles(rendered)

    assert titles[0] == "full_switch_matrix_130_by_25.asdl"
    assert "Top module" in titles
    assert "Overview" not in titles
    assert "Modules" in titles
    assert titles.index("Imports") < titles.index("Top module")
    assert titles.index("Top module") < titles.index("Modules")
    assert titles.index("Modules") < titles.index("full_switch_matrix_130_by_25_no_probes")

    patterns_index = titles.index("Patterns")
    assert patterns_index < titles.index("Interface")
    assert patterns_index < titles.index("Instances")
    assert patterns_index < titles.index("Nets")

    nets_index = titles.index("Nets")
    assert titles.index("data chain") > nets_index
    assert titles.index("clock broadcast") > nets_index
    assert titles.index("buses and pins") > nets_index
    assert titles.index("power") > nets_index

    text = rendered.astext()
    assert "$BUS<@BUS>" in text
    assert "bus broadcast to all rows" in text

    top_section = _find_section(rendered, "Top module")
    assert top_section is not None
    assert "full_switch_matrix_130_by_25_no_probes" in top_section.astext()


def test_sphinx_render_overview_preserves_line_breaks(tmp_path: Path) -> None:
    path = tmp_path / "demo.asdl"
    path.write_text(
        "\n".join(
            [
                "# File line 1",
                "# File line 2",
                "modules:",
                "  # Module line 1",
                "  # Module line 2",
                "  Foo:",
                "    instances: {}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    rendered = _render_docutils(path)
    overview_sections = _find_sections(rendered, "Overview")
    assert len(overview_sections) == 2
    for section in overview_sections:
        assert list(section.findall(nodes.line))
