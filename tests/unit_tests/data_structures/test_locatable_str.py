from pathlib import Path

from src.asdl.data_structures import Locatable


def test_locatable_str_path_line_col():
    l = Locatable(file_path=Path("x.asdl"), start_line=3, start_col=5)
    assert str(l) == "x.asdl:3:5"


def test_locatable_str_path_line_only():
    l = Locatable(file_path=Path("x.asdl"), start_line=7)
    assert str(l) == "x.asdl:7"


def test_locatable_str_unknown():
    assert str(Locatable()) == "unknown location"


