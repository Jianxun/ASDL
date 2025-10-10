import pytest

from asdl.ir import register_asdl_dialect


@pytest.mark.skipif(register_asdl_dialect is None, reason="xDSL extra not installed")
def test_register_asdl_dialect_smoke():
    ctx = register_asdl_dialect()
    assert ctx is not None

