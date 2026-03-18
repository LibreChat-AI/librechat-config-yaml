"""Tests for --dry-run mode in update_models and automated_update."""

import logging
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest

from update_models import main as update_main
from providers.base import FetchResult, FetchStatus


def _make_registry():
    """Return a mock registry with one provider returning SUCCESS."""
    fetcher = MagicMock()
    fetcher.return_value.run.return_value = FetchResult(
        provider_name="test_provider",
        models=["model-a"],
        status=FetchStatus.SUCCESS,
    )
    return {"test_provider": fetcher}


def _make_yaml_data():
    """Return mock YAML data with one endpoint."""
    return {
        "version": "1.0",
        "endpoints": {
            "custom": [
                {
                    "name": "test_provider",
                    "models": {"default": ["old-model"], "fetch": False},
                }
            ]
        },
    }


# Shared patch targets
_PATCHES = {
    "discover": "update_models.discover_providers",
    "load": "update_models.load_yaml_file",
    "save": "update_models.save_yaml_file",
    "backup": "update_models.create_backup",
    "cleanup": "update_models.cleanup_temp_files",
    "staleness": "update_models.check_staleness",
    "update_yaml": "update_models.update_yaml_models",
}


class TestDryRunUpdateModels:
    """Tests for update_models.main(dry_run=...) parameter."""

    @patch(_PATCHES["cleanup"])
    @patch(_PATCHES["save"])
    @patch(_PATCHES["backup"], return_value=Path("/tmp/backup.yaml.bak"))
    @patch(_PATCHES["update_yaml"], return_value=True)
    @patch(_PATCHES["staleness"], return_value=(False, 1, 1))
    @patch(_PATCHES["load"])
    @patch(_PATCHES["discover"])
    @patch("update_models.Path")
    def test_main_accepts_dry_run_param(
        self, mock_path, mock_discover, mock_load, mock_stale,
        mock_update, mock_backup, mock_save, mock_cleanup,
    ):
        """update_models.main(dry_run=True) does not raise TypeError."""
        mock_discover.return_value = _make_registry()
        mock_load.return_value = _make_yaml_data()
        mock_path_inst = MagicMock()
        mock_path_inst.exists.return_value = True
        mock_path.return_value = mock_path_inst
        result = update_main(dry_run=True)
        assert result is not None

    @patch(_PATCHES["cleanup"])
    @patch(_PATCHES["save"])
    @patch(_PATCHES["backup"], return_value=Path("/tmp/backup.yaml.bak"))
    @patch(_PATCHES["update_yaml"], return_value=True)
    @patch(_PATCHES["staleness"], return_value=(False, 1, 1))
    @patch(_PATCHES["load"])
    @patch(_PATCHES["discover"])
    @patch("update_models.Path")
    def test_dry_run_skips_save(
        self, mock_path, mock_discover, mock_load, mock_stale,
        mock_update, mock_backup, mock_save, mock_cleanup,
    ):
        """When dry_run=True, save_yaml_file is never called."""
        mock_discover.return_value = _make_registry()
        mock_load.return_value = _make_yaml_data()
        mock_path_inst = MagicMock()
        mock_path_inst.exists.return_value = True
        mock_path.return_value = mock_path_inst
        update_main(dry_run=True)
        mock_save.assert_not_called()

    @patch(_PATCHES["cleanup"])
    @patch(_PATCHES["save"])
    @patch(_PATCHES["backup"], return_value=Path("/tmp/backup.yaml.bak"))
    @patch(_PATCHES["update_yaml"], return_value=True)
    @patch(_PATCHES["staleness"], return_value=(False, 1, 1))
    @patch(_PATCHES["load"])
    @patch(_PATCHES["discover"])
    @patch("update_models.Path")
    def test_dry_run_skips_backup(
        self, mock_path, mock_discover, mock_load, mock_stale,
        mock_update, mock_backup, mock_save, mock_cleanup,
    ):
        """When dry_run=True, create_backup is never called."""
        mock_discover.return_value = _make_registry()
        mock_load.return_value = _make_yaml_data()
        mock_path_inst = MagicMock()
        mock_path_inst.exists.return_value = True
        mock_path.return_value = mock_path_inst
        update_main(dry_run=True)
        mock_backup.assert_not_called()

    @patch(_PATCHES["cleanup"])
    @patch(_PATCHES["save"])
    @patch(_PATCHES["backup"], return_value=Path("/tmp/backup.yaml.bak"))
    @patch(_PATCHES["update_yaml"], return_value=True)
    @patch(_PATCHES["staleness"], return_value=(False, 1, 1))
    @patch(_PATCHES["load"])
    @patch(_PATCHES["discover"])
    @patch("update_models.Path")
    def test_dry_run_skips_cleanup(
        self, mock_path, mock_discover, mock_load, mock_stale,
        mock_update, mock_backup, mock_save, mock_cleanup,
    ):
        """When dry_run=True, cleanup_temp_files is never called."""
        mock_discover.return_value = _make_registry()
        mock_load.return_value = _make_yaml_data()
        mock_path_inst = MagicMock()
        mock_path_inst.exists.return_value = True
        mock_path.return_value = mock_path_inst
        update_main(dry_run=True)
        mock_cleanup.assert_not_called()

    @patch(_PATCHES["cleanup"])
    @patch(_PATCHES["save"])
    @patch(_PATCHES["backup"], return_value=Path("/tmp/backup.yaml.bak"))
    @patch(_PATCHES["update_yaml"], return_value=True)
    @patch(_PATCHES["staleness"], return_value=(False, 1, 1))
    @patch(_PATCHES["load"])
    @patch(_PATCHES["discover"])
    @patch("update_models.Path")
    def test_dry_run_fetches_providers(
        self, mock_path, mock_discover, mock_load, mock_stale,
        mock_update, mock_backup, mock_save, mock_cleanup,
    ):
        """When dry_run=True, discover_providers is still called."""
        mock_discover.return_value = _make_registry()
        mock_load.return_value = _make_yaml_data()
        mock_path_inst = MagicMock()
        mock_path_inst.exists.return_value = True
        mock_path.return_value = mock_path_inst
        update_main(dry_run=True)
        mock_discover.assert_called_once()

    @patch(_PATCHES["cleanup"])
    @patch(_PATCHES["save"])
    @patch(_PATCHES["backup"], return_value=Path("/tmp/backup.yaml.bak"))
    @patch(_PATCHES["update_yaml"], return_value=True)
    @patch(_PATCHES["staleness"], return_value=(False, 1, 1))
    @patch(_PATCHES["load"])
    @patch(_PATCHES["discover"])
    @patch("update_models.Path")
    def test_dry_run_checks_staleness(
        self, mock_path, mock_discover, mock_load, mock_stale,
        mock_update, mock_backup, mock_save, mock_cleanup,
    ):
        """When dry_run=True, check_staleness is still called for each provider."""
        mock_discover.return_value = _make_registry()
        mock_load.return_value = _make_yaml_data()
        mock_path_inst = MagicMock()
        mock_path_inst.exists.return_value = True
        mock_path.return_value = mock_path_inst
        update_main(dry_run=True)
        assert mock_stale.call_count > 0

    @patch(_PATCHES["cleanup"])
    @patch(_PATCHES["save"])
    @patch(_PATCHES["backup"], return_value=Path("/tmp/backup.yaml.bak"))
    @patch(_PATCHES["update_yaml"], return_value=True)
    @patch(_PATCHES["staleness"], return_value=(False, 1, 1))
    @patch(_PATCHES["load"])
    @patch(_PATCHES["discover"])
    @patch("update_models.Path")
    def test_dry_run_calls_print_summary(
        self, mock_path, mock_discover, mock_load, mock_stale,
        mock_update, mock_backup, mock_save, mock_cleanup,
    ):
        """When dry_run=True, stats.print_summary() is still called."""
        mock_discover.return_value = _make_registry()
        mock_load.return_value = _make_yaml_data()
        mock_path_inst = MagicMock()
        mock_path_inst.exists.return_value = True
        mock_path.return_value = mock_path_inst
        with patch("update_models.UpdateStats") as mock_stats_cls:
            mock_stats = MagicMock()
            mock_stats_cls.return_value = mock_stats
            update_main(dry_run=True)
            mock_stats.print_summary.assert_called_once()

    @patch(_PATCHES["cleanup"])
    @patch(_PATCHES["save"])
    @patch(_PATCHES["backup"], return_value=Path("/tmp/backup.yaml.bak"))
    @patch(_PATCHES["update_yaml"], return_value=True)
    @patch(_PATCHES["staleness"], return_value=(False, 1, 1))
    @patch(_PATCHES["load"])
    @patch(_PATCHES["discover"])
    @patch("update_models.Path")
    def test_dry_run_logs_mode(
        self, mock_path, mock_discover, mock_load, mock_stale,
        mock_update, mock_backup, mock_save, mock_cleanup, caplog,
    ):
        """When dry_run=True, log output contains 'DRY RUN'."""
        mock_discover.return_value = _make_registry()
        mock_load.return_value = _make_yaml_data()
        mock_path_inst = MagicMock()
        mock_path_inst.exists.return_value = True
        mock_path.return_value = mock_path_inst
        with caplog.at_level(logging.INFO):
            update_main(dry_run=True)
        assert "DRY RUN" in caplog.text

    @patch(_PATCHES["cleanup"])
    @patch(_PATCHES["save"])
    @patch(_PATCHES["backup"], return_value=Path("/tmp/backup.yaml.bak"))
    @patch(_PATCHES["update_yaml"], return_value=True)
    @patch(_PATCHES["staleness"], return_value=(False, 1, 1))
    @patch(_PATCHES["load"])
    @patch(_PATCHES["discover"])
    @patch("update_models.Path")
    def test_normal_run_still_saves(
        self, mock_path, mock_discover, mock_load, mock_stale,
        mock_update, mock_backup, mock_save, mock_cleanup,
    ):
        """When dry_run=False (default), save_yaml_file IS called when updates exist."""
        mock_discover.return_value = _make_registry()
        mock_load.return_value = _make_yaml_data()
        mock_path_inst = MagicMock()
        mock_path_inst.exists.return_value = True
        mock_path.return_value = mock_path_inst
        update_main(dry_run=False)
        assert mock_save.call_count > 0
