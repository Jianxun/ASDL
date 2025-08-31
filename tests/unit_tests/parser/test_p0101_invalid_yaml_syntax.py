"""
P0101: Invalid YAML Syntax
"""

from src.asdl.parser import ASDLParser


def test_p0101_invalid_yaml_syntax():
    parser = ASDLParser()
    asdl_file, diagnostics = parser.parse_string("key: [unclosed bracket")

    assert asdl_file is None
    assert len(diagnostics) == 1
    d = diagnostics[0]
    assert d.code == "P0101"


def test_p0101_duplicate_top_level_modules_keys():
    parser = ASDLParser()
    yaml_content = """
file_info:
  top_module: t
modules:
  a: {spice_template: "R{name} n1 n2 1k"}
  a: {spice_template: "R{name} n3 n4 2k"}
"""
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "P0101"


def test_p0101_duplicate_import_aliases():
    parser = ASDLParser()
    yaml_content = """
file_info:
  top_module: t
imports:
  lib: libs/a.asdl
  lib: libs/b.asdl
modules:
  t: { instances: {} }
"""
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "P0101"


def test_p0101_duplicate_ports_in_module():
    parser = ASDLParser()
    yaml_content = """
file_info:
  top_module: t
modules:
  t:
    ports:
      in: {dir: in}
      in: {dir: in}
    spice_template: "X{name} in out dev"
"""
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "P0101"


def test_p0101_duplicate_instances_in_module():
    parser = ASDLParser()
    yaml_content = """
file_info:
  top_module: t
modules:
  t:
    instances:
      X1: { model: dev, mappings: {in: in, out: out} }
      X1: { model: dev, mappings: {in: in2, out: out2} }
"""
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "P0101"


def test_p0101_yaml_merge_key_forbidden():
    parser = ASDLParser()
    yaml_content = """
file_info:
  top_module: t
base: &BASE
  spice_template: "R{name} n1 n2 1k"
modules:
  t:
    <<: *BASE
"""
    asdl_file, diagnostics = parser.parse_string(yaml_content)

    assert asdl_file is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "P0101"
