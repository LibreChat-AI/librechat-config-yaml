"""Tests for atomic write and validate_yaml_file in update_models.py."""
from __future__ import annotations

from unittest.mock import patch

import pytest


class TestAtomicWriteSuccess:
    """Test that save_yaml_file writes valid YAML atomically."""

    def test_atomic_write_success(self, tmp_path):
        """save_yaml_file writes valid YAML and target file exists with correct content."""
        from update_models import save_yaml_file, validate_yaml_file

        target = tmp_path / "test.yaml"
        target.write_text("version: '1.0'\nendpoints:\n  custom: []\n")

        data = {"version": "1.0", "endpoints": {"custom": []}}
        save_yaml_file(str(target), data)

        assert target.exists()
        is_valid, error = validate_yaml_file(str(target))
        assert is_valid, "Written file should be valid YAML: %s" % error


class TestAtomicWriteValidation:
    """Test that save_yaml_file validates before replacing."""

    def test_atomic_write_validates(self, tmp_path):
        """save_yaml_file with data that fails validation raises ValueError and original is unchanged."""
        from update_models import save_yaml_file

        target = tmp_path / "test.yaml"
        original_content = "version: '1.0'\nendpoints:\n  custom: []\n"
        target.write_text(original_content)

        # Write a list instead of a dict -- will fail validation (not a dict)
        with pytest.raises(ValueError, match="Validation failed"):
            save_yaml_file(str(target), ["not", "a", "dict"])

        # Original file should be unchanged
        assert target.read_text() == original_content


class TestCleanupOnFailure:
    """Test that temp files are cleaned up on failure."""

    def test_cleanup_on_failure(self, tmp_path):
        """After a failed atomic write, no .yaml.tmp files remain."""
        from update_models import save_yaml_file

        target = tmp_path / "test.yaml"
        target.write_text("version: '1.0'\nendpoints:\n  custom: []\n")

        # Write invalid data that will fail validation
        with pytest.raises((ValueError, Exception)):
            save_yaml_file(str(target), ["not", "a", "dict"])

        # No temp files should remain
        tmp_files = list(tmp_path.glob("*.yaml.tmp"))
        assert len(tmp_files) == 0, "Temp files should be cleaned up: %s" % tmp_files


class TestCrashSafety:
    """Test that a crash during YAML dump leaves original file intact."""

    def test_crash_safety(self, tmp_path):
        """If YAML dump raises mid-write, original file is intact."""
        from update_models import save_yaml_file

        target = tmp_path / "test.yaml"
        original_content = "version: '1.0'\nendpoints:\n  custom: []\n"
        target.write_text(original_content)

        # Mock the YAML dump to raise an error mid-write
        with patch("update_models.YAML") as MockYAML:
            mock_yaml_instance = MockYAML.return_value
            mock_yaml_instance.dump.side_effect = RuntimeError("Simulated crash")

            with pytest.raises(RuntimeError, match="Simulated crash"):
                save_yaml_file(str(target), {"version": "1.0", "endpoints": {"custom": []}})

        # Original file should be unchanged
        assert target.read_text() == original_content

        # No temp files should remain
        tmp_files = list(tmp_path.glob("*.yaml.tmp"))
        assert len(tmp_files) == 0, "Temp files should be cleaned up after crash"


class TestValidateYamlFile:
    """Unit tests for validate_yaml_file function."""

    def test_validate_yaml_file_valid(self, tmp_path):
        """validate_yaml_file on valid LibreChat YAML returns (True, None)."""
        from update_models import validate_yaml_file

        yaml_file = tmp_path / "valid.yaml"
        yaml_file.write_text("version: '1.0'\nendpoints:\n  custom: []\n")

        is_valid, error = validate_yaml_file(str(yaml_file))
        assert is_valid is True
        assert error is None

    def test_validate_yaml_file_invalid(self, tmp_path):
        """validate_yaml_file on broken YAML returns (False, error_string)."""
        from update_models import validate_yaml_file

        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text(":\n  bad yaml {{{\n  ][invalid")

        is_valid, error = validate_yaml_file(str(yaml_file))
        assert is_valid is False
        assert error is not None
        assert isinstance(error, str)

    def test_validate_yaml_file_missing_keys(self, tmp_path):
        """validate_yaml_file on YAML without 'version' or 'endpoints' returns (False, 'Missing required keys: ...')."""
        from update_models import validate_yaml_file

        yaml_file = tmp_path / "missing_keys.yaml"
        yaml_file.write_text("some_key: value\n")

        is_valid, error = validate_yaml_file(str(yaml_file))
        assert is_valid is False
        assert "Missing required keys" in error
