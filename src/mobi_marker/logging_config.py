"""Logging configuration for the MoBI Marker application.

Sets up file and console logging with verbose output for diagnostics.
Each application run creates a timestamped log file in a ``logs/`` directory
next to the executable (or cwd).
"""

import logging
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR_NAME = "mobi_marker_logs"
LOG_FORMAT = (
    "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(threadName)-18s | "
    "%(name)-28s | %(funcName)-26s | %(message)s"
)
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
FILE_LOG_LEVEL = logging.DEBUG
CONSOLE_LOG_LEVEL = logging.DEBUG


def _is_test_run() -> bool:
    """Return whether the current process is running under pytest."""
    return "PYTEST_CURRENT_TEST" in os.environ or "pytest" in sys.modules


def _resolve_log_dir() -> Path:
    """Return the directory where log files are stored.

    Creates ``~/mobi_marker_logs/`` so logs survive regardless of cwd.
    Falls back to cwd on permission errors.
    """
    try:
        log_dir = Path.home() / LOG_DIR_NAME
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    except OSError:
        fallback = Path.cwd() / LOG_DIR_NAME
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def setup_logging() -> Path | None:
    """Configure root logger with console and optional file handlers.

    Returns:
        The absolute path to the log file created for this session.
        Returns ``None`` during test runs (no file handler is created).
    """
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    log_file: Path | None = None

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(CONSOLE_LOG_LEVEL)
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()

    if not _is_test_run():
        log_dir = _resolve_log_dir()
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"mobi_marker_{timestamp}.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(FILE_LOG_LEVEL)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    root.addHandler(console_handler)

    return log_file


def log_system_info() -> None:
    """Log runtime / environment info useful for post-mortem analysis."""
    logger = logging.getLogger("mobi_marker.startup")

    logger.info("=" * 72)
    logger.info("MoBI Marker — Diagnostic Session")
    logger.info("=" * 72)
    logger.info("Platform      : %s", platform.platform())
    logger.info("Python        : %s", sys.version)
    logger.info("Executable    : %s", sys.executable)
    logger.info("PID           : %d", os.getpid())
    logger.info("CWD           : %s", os.getcwd())
    logger.info("Machine       : %s", platform.node())

    try:
        from PyQt6.QtCore import PYQT_VERSION_STR, QT_VERSION_STR

        logger.info("Qt version    : %s", QT_VERSION_STR)
        logger.info("PyQt6 version : %s", PYQT_VERSION_STR)
    except Exception:
        logger.warning("Could not determine PyQt6 / Qt version")

    try:
        import pylsl

        logger.info(
            "pylsl version : %s",
            getattr(pylsl, "__version__", "unknown"),
        )
        logger.info(
            "liblsl version: %s",
            getattr(pylsl, "library_version", lambda: "unknown")(),
        )
    except Exception:
        logger.warning("Could not determine pylsl version")

    logger.info("=" * 72)
