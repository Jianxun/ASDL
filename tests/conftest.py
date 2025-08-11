import os
import pytest


def pytest_collection_modifyitems(config, items):
    """Skip simulation tests that require the devcontainer/ngspice environment.

    - Any tests under external designs testbenches
    - ASDL inverter integration tests that shell out to ngspice
    """
    skip_reason = "Skipped: requires devcontainer/ngspice runtime"
    skip_marker = pytest.mark.skip(reason=skip_reason)

    for item in items:
        node_path = str(item.fspath)
        node_id = item.nodeid

        if "/designs/libs/tb_analog/" in node_path:
            item.add_marker(skip_marker)
            continue

        if node_id.endswith("tests/integration/test_inverter_simulation.py::test_op"):
            item.add_marker(skip_marker)
            continue

        if "tests/integration/test_inverter_simulation.py" in node_path:
            item.add_marker(skip_marker)


