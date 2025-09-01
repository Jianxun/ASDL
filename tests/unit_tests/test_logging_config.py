import logging
import os
from importlib import reload

import asdl.logging_utils as lu


def test_trace_level_registration_idempotent():
    lu.ensure_trace_level_registered()
    assert hasattr(logging, "TRACE")
    assert isinstance(logging.TRACE, int)
    before = logging.getLogger("asdlc.test").isEnabledFor(logging.TRACE)
    lu.ensure_trace_level_registered()
    after = logging.getLogger("asdlc.test").isEnabledFor(logging.TRACE)
    assert before == after


def test_configure_logging_human_console(tmp_path, monkeypatch):
    monkeypatch.delenv("ASDL_LOG_LEVEL", raising=False)
    monkeypatch.setenv("ASDL_LOG_FORMAT", "human")
    lu.configure_logging(verbose=True, debug=False, trace=False, log_file=None, log_json=None)
    log = lu.get_logger("unit")
    log.info("hello human")
    # No assertion on stdout capture here; just ensure no exceptions


def test_configure_logging_json_file(tmp_path, monkeypatch):
    logfile = tmp_path / "test.log"
    monkeypatch.setenv("ASDL_LOG_FILE", str(logfile))
    monkeypatch.setenv("ASDL_LOG_FORMAT", "json")
    lu.configure_logging(verbose=False, debug=True, trace=False, log_file=None, log_json=None)
    log = lu.get_logger("unit")
    log.debug("hello json")
    contents = logfile.read_text(encoding="utf-8")
    assert "\"level\": \"DEBUG\"" in contents
    assert "hello json" in contents


def test_determine_log_level_precedence(monkeypatch):
    monkeypatch.setenv("ASDL_LOG_LEVEL", "WARNING")
    # trace overrides all
    assert lu.determine_log_level(verbose=True, debug=True, trace=True) == lu.TRACE_LEVEL_NUM
    # debug overrides verbose
    assert lu.determine_log_level(verbose=True, debug=True, trace=False) == logging.DEBUG
    # verbose when no debug/trace
    assert lu.determine_log_level(verbose=True, debug=False, trace=False) == logging.INFO
    # env considered when no flags
    assert lu.determine_log_level(verbose=False, debug=False, trace=False) == logging.WARNING


