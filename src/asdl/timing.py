import time
from contextlib import contextmanager
from typing import Iterator, Optional


@contextmanager
def time_block(logger, label: str, level: int = None) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        end = time.perf_counter()
        duration_ms = (end - start) * 1000.0
        lvl = level if level is not None else getattr(logger, "level", None)
        if hasattr(logger, "debug"):
            logger.debug(f"{label} took {duration_ms:.2f} ms")


