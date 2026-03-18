"""Tests for CI validation gating (REQ-S3)."""
from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


REPO_ROOT = Path(__file__).parent.parent.parent
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "update-models.yml"


class TestWorkflowStructure:
    """Smoke tests for CI workflow hardening."""

    def test_no_continue_on_error(self):
        """Workflow must not have continue-on-error on any step."""
        content = WORKFLOW_PATH.read_text()
        assert "continue-on-error" not in content

    def test_no_exit_code_capture(self):
        """UPDATE_EXIT_CODE capture pattern must be removed."""
        content = WORKFLOW_PATH.read_text()
        assert "UPDATE_EXIT_CODE" not in content

    def test_workflow_runs_automated_update(self):
        """Workflow must call automated_update.py directly."""
        content = WORKFLOW_PATH.read_text()
        assert "python automated_update.py" in content


class TestExitCodePropagation:
    """Test that automated_update.py returns correct exit codes."""

    @patch("automated_update.setup_logging")
    @patch("automated_update.update_models")
    def test_success_exit_code(self, mock_um, mock_log):
        """Successful update + validation returns 0."""
        mock_um.main.return_value = True

        with patch("automated_update.validate_yaml_file", return_value=(True, None)), \
             patch("automated_update.Path") as MockPath:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            MockPath.return_value.__truediv__ = MagicMock(return_value=mock_path)
            mock_path.__truediv__ = MagicMock(return_value=mock_path)

            import automated_update
            result = automated_update.main()

        assert result == 0

    @patch("automated_update.setup_logging")
    @patch("automated_update.update_models")
    def test_update_failure_exit_code(self, mock_um, mock_log):
        """Failed update returns 1."""
        mock_um.main.return_value = False

        import automated_update
        result = automated_update.main()

        assert result == 1

    @patch("automated_update.setup_logging")
    @patch("automated_update.update_models")
    def test_validation_failure_exit_code(self, mock_um, mock_log):
        """Validation failure returns 2."""
        mock_um.main.return_value = True

        with patch("automated_update.validate_yaml_file", return_value=(False, "Missing required keys: version")), \
             patch("automated_update.Path") as MockPath, \
             patch.dict("os.environ", {"GITHUB_ENV": "/dev/null"}):
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.name = "librechat-test.yaml"
            MockPath.return_value.__truediv__ = MagicMock(return_value=mock_path)

            import automated_update
            result = automated_update.main()

        assert result == 2

    @patch("automated_update.setup_logging")
    @patch("automated_update.update_models")
    def test_validation_error_message_logged(self, mock_um, mock_log, caplog):
        """Validation failure logs the file name and error."""
        mock_um.main.return_value = True

        with patch("automated_update.validate_yaml_file", return_value=(False, "YAML file is empty")), \
             patch("automated_update.Path") as MockPath, \
             patch.dict("os.environ", {"GITHUB_ENV": "/dev/null"}), \
             caplog.at_level(logging.ERROR, logger="automated_update"):
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.name = "librechat-test.yaml"
            MockPath.return_value.__truediv__ = MagicMock(return_value=mock_path)

            import automated_update
            automated_update.main()

        error_messages = " ".join(r.message for r in caplog.records if r.levelno >= logging.ERROR)
        assert "librechat-test.yaml" in error_messages
        assert "YAML file is empty" in error_messages
