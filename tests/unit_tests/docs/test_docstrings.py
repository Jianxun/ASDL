from pathlib import Path

from asdl.docs.docstrings import extract_docstrings_from_file


def test_extract_docstrings_swmatrix_tgate() -> None:
    docstrings = extract_docstrings_from_file(
        Path("examples/libs/sw_matrix/swmatrix_Tgate/swmatrix_Tgate.asdl")
    )

    module_path = ("modules", "swmatrix_Tgate")
    module_doc = docstrings.key_docstrings[module_path].text
    assert (
        module_doc
        == "\n".join(
            [
                "Switch Matrix Tgate",
                "power:",
                "  VDDd: nominal 3.3V",
                "  VSSd: nominal 0V",
                "digital:",
                "  inputs:",
                "    - control: active high control signal to close the Tgate",
                "    - enable: active high enable signal shared by all Tgates",
                "analog:",
                "  T1, T2: symmetric analog terminals, rail-to-rail compliance.",
                "specs:",
                "  - Ron < 100 ohms @ 3.3V",
                "  - Cpar < 20fF",
            ]
        )
    )

    assert (
        docstrings.key_docstrings[
            ("modules", "swmatrix_Tgate", "instances", "mp")
        ].text
        == "PMOS/NMOS ratio is 3:1"
    )

    nets_path = ("modules", "swmatrix_Tgate", "nets")
    assert docstrings.sections.get(nets_path) is None

    assert docstrings.key_docstrings[nets_path + ("$VDDd",)].text == "nominal 3.3V"
    assert (
        docstrings.key_docstrings[nets_path + ("$control",)].text
        == "active high control signal to close the Tgate"
    )
    assert (
        docstrings.key_docstrings[nets_path + ("net1",)].text
        == "intermediate node for control signal"
    )
    assert (
        docstrings.key_docstrings[nets_path + ("$T1",)].text
        == "Tgate analog terminal 1"
    )
    assert (
        docstrings.key_docstrings[nets_path + ("$T2",)].text
        == "Tgate analog terminal 2"
    )


def test_extract_docstrings_full_switch_matrix_sections() -> None:
    docstrings = extract_docstrings_from_file(
        Path(
            "examples/libs/sw_matrix/full_switch_matrix_130_by_25/"
            "full_switch_matrix_130_by_25.asdl"
        )
    )

    nets_path = (
        "modules",
        "full_switch_matrix_130_by_25_no_probes",
        "nets",
    )
    sections = docstrings.sections[nets_path]

    assert [section.title for section in sections] == [
        "data chain",
        "clock broadcast",
        "buses and pins",
        "power",
    ]
    assert sections[0].keys == ("$data", "$D_out", "D<129:1>")
    assert sections[1].keys == ("$PHI_1_in", "$PHI_2_in", "$enable_in")
    assert sections[2].keys == ("$BUS<@BUS>", "$pin<@ROW>")
    assert sections[3].keys == ("$VDDd", "$VSSd")

    assert nets_path + ("$data",) not in docstrings.key_docstrings
    assert (
        docstrings.key_docstrings[nets_path + ("$BUS<@BUS>",)].text
        == "bus broadcast to all rows"
    )
