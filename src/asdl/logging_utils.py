import json
import logging
import os
from datetime import datetime
from typing import Optional


# Custom TRACE level below DEBUG
TRACE_LEVEL_NUM = 5


def _trace(self, message: str, *args, **kwargs) -> None:
    if self.isEnabledFor(TRACE_LEVEL_NUM):
        self._log(TRACE_LEVEL_NUM, message, args, **kwargs)


def ensure_trace_level_registered() -> None:
    if not hasattr(logging, "TRACE"):
        logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")
        setattr(logging, "TRACE", TRACE_LEVEL_NUM)
        setattr(logging.Logger, "trace", _trace)


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.utcfromtimestamp(record.created).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "component": record.name.replace("asdlc.", ""),
            "message": record.getMessage(),
        }
        return json.dumps(payload, ensure_ascii=False)


class HumanLogFormatter(logging.Formatter):
    DEFAULT_FMT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"

    def __init__(self) -> None:
        super().__init__(fmt=self.DEFAULT_FMT, datefmt=self.DEFAULT_DATEFMT)


def _coerce_level(level_str: Optional[str]) -> Optional[int]:
    if not level_str:
        return None
    level_up = level_str.upper()
    if level_up == "TRACE":
        return TRACE_LEVEL_NUM
    try:
        return getattr(logging, level_up)
    except AttributeError:
        return None


def determine_log_level(verbose: bool, debug: bool, trace: bool) -> int:
    ensure_trace_level_registered()
    if trace:
        return TRACE_LEVEL_NUM
    if debug:
        return logging.DEBUG
    if verbose:
        return logging.INFO
    # Environment override when no explicit flags
    env_level = _coerce_level(os.getenv("ASDL_LOG_LEVEL"))
    if env_level is not None:
        return env_level
    return logging.WARNING


def configure_logging(
    *,
    verbose: bool = False,
    debug: bool = False,
    trace: bool = False,
    log_file: Optional[str] = None,
    log_json: Optional[bool] = None,
) -> None:
    """Configure logging for the ASDL compiler CLI.

    log_json: if None, read ASDL_LOG_FORMAT env var ("json" or "human").
    log_file: if None, read ASDL_LOG_FILE env var.
    """
    ensure_trace_level_registered()

    # Root logger for the toolchain
    root_logger = logging.getLogger("asdlc")
    root_logger.setLevel(TRACE_LEVEL_NUM)

    # Clean existing handlers to avoid duplicate logs when invoked repeatedly
    if root_logger.handlers:
        for h in list(root_logger.handlers):
            root_logger.removeHandler(h)

    # Resolve handler level and formatter
    level = determine_log_level(verbose, debug, trace)

    # Determine output format
    if log_json is None:
        env_format = os.getenv("ASDL_LOG_FORMAT", "human").lower()
        log_json = env_format == "json"

    formatter = JsonLogFormatter() if log_json else HumanLogFormatter()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Optional file handler
    if log_file is None:
        log_file = os.getenv("ASDL_LOG_FILE")
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(component: str) -> logging.Logger:
    """Get a hierarchical logger under the asdlc namespace.

    Example: get_logger("cli"), get_logger("parser"), get_logger("elaborator.imports")
    """
    return logging.getLogger(f"asdlc.{component}")


