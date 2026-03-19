"""Tests for centralized logging configuration (log_config module)."""

import json
import logging
import subprocess
from io import StringIO
from pathlib import Path


class TestHumanFormatter:
    """Tests for HumanFormatter output format."""

    def test_human_format(self):
        """HumanFormatter output matches 'YYYY-MM-DD HH:MM:SS [LEVEL] logger_name: message'."""
        from log_config import HumanFormatter

        formatter = HumanFormatter()
        handler = logging.StreamHandler(StringIO())
        handler.setFormatter(formatter)

        logger = logging.getLogger("test.human_format")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("hello world")
        output = handler.stream.getvalue().strip()

        # Verify format: YYYY-MM-DD HH:MM:SS [INFO] test.human_format: hello world
        assert "[INFO]" in output
        assert "test.human_format:" in output
        assert "hello world" in output
        # Verify timestamp pattern (YYYY-MM-DD HH:MM:SS)
        import re
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", output)


class TestJsonFormatter:
    """Tests for JsonFormatter output format."""

    def test_json_format_ci(self):
        """JsonFormatter produces valid JSON with keys: timestamp, level, logger, message."""
        from log_config import JsonFormatter

        formatter = JsonFormatter()
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(formatter)

        logger = logging.getLogger("test.json_format")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("test message")
        output = stream.getvalue().strip()
        parsed = json.loads(output)

        assert "timestamp" in parsed
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test.json_format"
        assert parsed["message"] == "test message"

    def test_json_parseable(self):
        """JSON output is parseable by json.loads() and contains correct values."""
        from log_config import JsonFormatter

        formatter = JsonFormatter()
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(formatter)

        logger = logging.getLogger("test.json_parseable")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)

        logger.warning("something went wrong")
        output = stream.getvalue().strip()
        parsed = json.loads(output)

        assert parsed["level"] == "WARNING"
        assert parsed["message"] == "something went wrong"
        assert parsed["logger"] == "test.json_parseable"
        # Timestamp should be ISO format
        assert "T" in parsed["timestamp"]

    def test_json_includes_provider(self):
        """When LoggerAdapter sets provider extra, JSON output contains 'provider' key."""
        from log_config import JsonFormatter

        formatter = JsonFormatter()
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(formatter)

        base_logger = logging.getLogger("test.json_provider")
        base_logger.handlers.clear()
        base_logger.addHandler(handler)
        base_logger.setLevel(logging.INFO)

        adapter = logging.LoggerAdapter(base_logger, {"provider": "openai"})
        adapter.info("fetching models")

        output = stream.getvalue().strip()
        parsed = json.loads(output)
        assert parsed["provider"] == "openai"
        assert parsed["message"] == "fetching models"

    def test_json_includes_exception(self):
        """When logging with exc_info, JSON output contains 'exception' key."""
        from log_config import JsonFormatter

        formatter = JsonFormatter()
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(formatter)

        logger = logging.getLogger("test.json_exception")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)

        try:
            raise ValueError("test error")
        except ValueError:
            logger.error("something failed", exc_info=True)

        output = stream.getvalue().strip()
        parsed = json.loads(output)
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]
        assert "test error" in parsed["exception"]


class TestSetupLogging:
    """Tests for the setup_logging() function."""

    def test_setup_logging_human_default(self, monkeypatch):
        """With no CI env var, setup_logging() configures HumanFormatter on root logger."""
        from log_config import HumanFormatter, setup_logging

        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

        setup_logging()

        root = logging.getLogger()
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0].formatter, HumanFormatter)

    def test_setup_logging_json_ci(self, monkeypatch):
        """With CI=true, setup_logging() configures JsonFormatter on root logger."""
        from log_config import JsonFormatter, setup_logging

        monkeypatch.setenv("CI", "true")

        setup_logging()

        root = logging.getLogger()
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0].formatter, JsonFormatter)

    def test_setup_logging_clears_handlers(self, monkeypatch):
        """Calling setup_logging() twice does not duplicate handlers."""
        from log_config import setup_logging

        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

        setup_logging()
        setup_logging()

        root = logging.getLogger()
        assert len(root.handlers) == 1

    def test_log_levels(self, monkeypatch):
        """INFO/WARNING/ERROR messages emit at correct levels through configured handler."""
        from log_config import setup_logging

        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

        setup_logging()

        stream = StringIO()
        handler = logging.StreamHandler(stream)
        from log_config import HumanFormatter
        handler.setFormatter(HumanFormatter())

        logger = logging.getLogger("test.levels")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.info("info msg")
        logger.warning("warn msg")
        logger.error("error msg")

        output = stream.getvalue()
        assert "[INFO]" in output
        assert "[WARNING]" in output
        assert "[ERROR]" in output


def test_no_print_calls_in_scripts():
    """Verify no print() calls remain in scripts/ (except update.py UI and test files)."""
    result = subprocess.run(
        ["grep", "-rn", "--include=*.py", "print(", str(Path(__file__).parent.parent)],
        capture_output=True, text=True
    )
    allowed_files = {"update.py", "test_"}
    violations = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        filepath = line.split(":")[0]
        filename = Path(filepath).name
        # Allow print() in update.py (interactive UI) and test files
        if any(allowed in filename for allowed in allowed_files):
            continue
        # Allow print() in log_config.py (none expected, but don't flag if present)
        if "log_config.py" in filepath:
            continue
        # Skip __pycache__
        if "__pycache__" in filepath:
            continue
        violations.append(line)
    assert not violations, f"print() found in disallowed files:\n" + "\n".join(violations)
