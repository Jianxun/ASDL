import pytest

from src.asdl.data_structures import Module


def test_module_primitive_ok():
    m = Module(spice_template="M @D @G @S @B model L={L} W={W}")
    assert m.is_primitive() and not m.is_hierarchical()


def test_module_hierarchical_ok():
    m = Module(instances={})
    assert m.is_hierarchical() and not m.is_primitive()


def test_module_both_set_raises():
    with pytest.raises(ValueError):
        Module(spice_template="X", instances={})


def test_module_neither_set_raises():
    with pytest.raises(ValueError):
        Module()


