"""Tests for CI validation gating (REQ-S3)."""
from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from update_models import UpdateStats


REPO_ROOT = Path(__file__).parent.parent.parent
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "update-models.yml"


def _make_update_stats(updated_files=None):
    """Create an UpdateStats instance with optional updated_files."""
    stats = UpdateStats()
    if updated_files:
        for f in updated_files:
            stats.add_file_result(f, True)
    return stats


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


def _make_fake_path(exists=True):
    """Create a Path mock where parent_dir / 'file.yaml' returns objects with correct .name."""
    # automated_update.py does:  parent_dir = Path(__file__).parent.parent
    # then: parent_dir / 'librechat-test.yaml'  ->  we need .name and .exists() to work
    parent_dir = MagicMock()

    def truediv_side_effect(self_mock, filename):
        child = MagicMock()
        child.name = filename
        child.exists.return_value = exists
        return child

    parent_dir.__truediv__ = truediv_side_effect

    mock_path_cls = MagicMock()
    # Path(__file__) returns instance; .parent.parent returns our parent_dir
    mock_path_cls.return_value.parent.parent = parent_dir
    return mock_path_cls


class TestExitCodePropagation:
    """Test that automated_update.py returns correct exit codes."""

    @patch("automated_update.setup_logging")
    @patch("automated_update.update_models")
    def test_success_exit_code(self, mock_um, mock_log):
        """Successful update + validation returns 0."""
        mock_um.main.return_value = _make_update_stats(["librechat-test.yaml"])

        with patch("automated_update.validate_yaml_file", return_value=(True, None)), \
             patch("automated_update.Path", _make_fake_path(exists=True)):

            import automated_update
            result = automated_update.main()

        assert result == 0

    @patch("automated_update.setup_logging")
    @patch("automated_update.update_models")
    def test_update_failure_exit_code(self, mock_um, mock_log):
        """Failed update returns 1."""
        mock_um.main.return_value = None

        import automated_update
        result = automated_update.main()

        assert result == 1

    @patch("automated_update.setup_logging")
    @patch("automated_update.update_models")
    def test_validation_failure_exit_code(self, mock_um, mock_log):
        """Validation failure returns 2."""
        mock_um.main.return_value = _make_update_stats(["librechat-test.yaml"])

        with patch("automated_update.validate_yaml_file", return_value=(False, "Missing required keys: version")), \
             patch("automated_update.Path", _make_fake_path(exists=True)), \
             patch.dict("os.environ", {"GITHUB_ENV": "/dev/null"}):

            import automated_update
            result = automated_update.main()

        assert result == 2

    @patch("automated_update.setup_logging")
    @patch("automated_update.update_models")
    def test_validation_error_message_logged(self, mock_um, mock_log, caplog):
        """Validation failure logs the file name and error."""
        mock_um.main.return_value = _make_update_stats(["librechat-test.yaml"])

        with patch("automated_update.validate_yaml_file", return_value=(False, "YAML file is empty")), \
             patch("automated_update.Path", _make_fake_path(exists=True)), \
             patch.dict("os.environ", {"GITHUB_ENV": "/dev/null"}), \
             caplog.at_level(logging.ERROR, logger="automated_update"):

            import automated_update
            automated_update.main()

        error_messages = " ".join(r.message for r in caplog.records if r.levelno >= logging.ERROR)
        # At least one of the 5 YAML files should appear in error messages
        yaml_files = [
            "librechat-env-f.yaml", "librechat-env-l.yaml",
            "librechat-up-f.yaml", "librechat-up-l.yaml",
            "librechat-test.yaml",
        ]
        assert any(f in error_messages for f in yaml_files)
        assert "YAML file is empty" in error_messages
