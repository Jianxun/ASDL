from src.asdl.data_structures import Port, PortDirection, PortType


def test_port_defaults_to_signal_type():
    p = Port(dir=PortDirection.IN)
    assert p.type == PortType.SIGNAL


def test_port_accepts_enum_type():
    p = Port(dir=PortDirection.OUT, type=PortType.POWER)
    assert p.type == PortType.POWER


