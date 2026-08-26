from __future__ import annotations

import subprocess
import sys


def _run(code: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)


def test_importing_cli_does_not_initialize_logging():
    """Importing the CLI must not load config or set up logging.

    factory/__init__.py used to read factory.logger and factory.logging at
    import time, so anything importing plextraktsync.cli (including `--help`)
    loaded the config and initialized logging as a side effect, which also
    emitted a log line.
    """
    result = _run("import plextraktsync.cli")

    assert result.stdout == ""
    assert result.stderr == ""


def test_importing_cli_leaves_logging_deps_unimported():
    """The deferred path is what keeps the import cheap."""
    result = _run("import plextraktsync.cli, sys;print(sorted(m for m in ('yaml', 'dotenv', 'rich.logging') if m in sys.modules))")

    assert result.stdout.strip() == "[]"


def test_logging_and_logger_are_still_importable():
    """`from plextraktsync.factory import logging` must keep working."""
    result = _run("from plextraktsync.factory import logger, logging;print(logger.name, type(logging).__name__)")

    assert "plextraktsync" in result.stdout


def test_unknown_attribute_still_raises_attribute_error():
    """The module __getattr__ must not swallow genuine typos."""
    result = subprocess.run(
        [sys.executable, "-c", "import plextraktsync.factory as f; f.nope"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "has no attribute 'nope'" in result.stderr
