from pathlib import Path
from typing import List

from src.asdl.elaborator import Elaborator
from src.asdl.data_structures import ASDLFile, FileInfo, Module, Port, PortDirection
from src.asdl.parser import ASDLParser


def write_file(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def test_toy_import_orchestration(tmp_path: Path) -> None:
    """
    Toy example from documentation adapted to current schema.
    Flow: top.asdl imports libs/opamp.asdl which imports primitives.asdl.
    Phase 0 skeleton should resolve to a flattened ASDL with modules hoisted,
    then pattern/variable phases run without error.
    """
    # primitives.asdl (primitive modules with spice_template)
    primitives = """
file_info:
  name: primitives

modules:
  nfet_03v3:
    ports: {D: {dir: out}, G: {dir: in}, S: {dir: in}, B: {dir: in}}
    spice_template: "M{name} {D} {G} {S} {B} nfet_03v3 L=0.28u W=3u"
  pfet_03v3:
    ports: {D: {dir: out}, G: {dir: in}, S: {dir: in}, B: {dir: in}}
    spice_template: "M{name} {D} {G} {S} {B} pfet_03v3 L=0.28u W=6u"
"""

    # opamp.asdl imports primitives and defines a hierarchical module
    opamp = """
file_info:
  name: opamp

imports:
  prim: primitives.asdl

model_alias:
  nmos: prim.nfet_03v3
  pmos: prim.pfet_03v3

modules:
  ota_diffpair:
    ports:
      in_p: {dir: in}
      in_n: {dir: in}
      out: {dir: out}
      vdd: {dir: in}
      vss: {dir: in}
    instances:
      MN1: {model: nmos, mappings: {D: out, G: in_p, S: vss, B: vss}}
      MN2: {model: nmos, mappings: {D: out, G: in_n, S: vss, B: vss}}
      MP1: {model: pmos, mappings: {D: out, G: in_p, S: vdd, B: vdd}}
"""

    # top.asdl imports opamp and instantiates it
    top = """
file_info:
  name: top

imports:
  op: libs/opamp.asdl

modules:
  top_amp:
    ports:
      in_p: {dir: in}
      in_n: {dir: in}
      vdd: {dir: in}
      vss: {dir: in}
      out: {dir: out}
    instances:
      A1: {model: op.ota_diffpair, mappings: {in_p: in_p, in_n: in_n, vdd: vdd, vss: vss, out: out}}
"""

    libs_dir = tmp_path / "libs"
    write_file(libs_dir / "primitives.asdl", primitives.strip() + "\n")
    write_file(libs_dir / "opamp.asdl", opamp.strip() + "\n")
    write_file(tmp_path / "top.asdl", top.strip() + "\n")

    # Execute Phase 0 skeleton via wrapper
    elab = Elaborator()
    flattened, diags = elab.elaborate_with_imports(tmp_path / "top.asdl", search_paths=[tmp_path, libs_dir])

    # Should succeed without fatal errors
    assert flattened is not None, f"Expected elaborated file, got None. Diagnostics: {[d.code for d in diags]}"

    # Flattened must contain hoisted modules
    modules = flattened.modules
    assert "nfet_03v3" in modules
    assert "pfet_03v3" in modules
    assert "ota_diffpair" in modules
    assert "top_amp" in modules

    # Instance models should ultimately bind to local module names after aliasing
    # (Phase 0 skeleton flattens; binding validations are enhanced in later phases)
    top_amp = modules["top_amp"]
    assert top_amp.instances is not None
    assert "A1" in top_amp.instances
    assert top_amp.instances["A1"].model in ("ota_diffpair", "op.ota_diffpair")

