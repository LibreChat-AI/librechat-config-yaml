"""Tests for contract-based orchestrator logic in update_models.py."""
from __future__ import annotations

import logging
from typing import Optional
from unittest.mock import MagicMock, patch

from providers.base import BaseFetcher, FetchResult, FetchStatus


def _make_fake_fetcher(name: str, models: list[str], status: FetchStatus = FetchStatus.SUCCESS):
    """Create a fake fetcher class that returns a predetermined FetchResult."""

    class FakeFetcher(BaseFetcher):
        provider_name = name

        def get_api_key(self) -> Optional[str]:
            return None

        def fetch_models(self) -> FetchResult:
            return FetchResult(
                provider_name=self.provider_name,
                models=models,
                status=status,
                error_message=None if status == FetchStatus.SUCCESS else "test error",
            )

        def post_process(self, models_list: list[str]) -> list[str]:
            return sorted(set(models_list))

    return FakeFetcher


class TestContractOrchestrator:
    """Test that update_models.main() runs all providers through the contract path."""

    @patch("update_models.setup_logging")
    @patch("update_models.discover_providers")
    @patch("update_models.load_yaml_file", return_value=None)
    @patch("update_models.cleanup_temp_files")
    def test_all_providers_run_via_contract(
        self, mock_cleanup, mock_load_yaml, mock_discover, mock_setup_log, caplog
    ):
        """All providers should be discovered and run via the contract path."""
        mock_discover.return_value = {
            "Nvidia": _make_fake_fetcher("Nvidia", ["model-a", "model-b"]),
            "groq": _make_fake_fetcher("groq", ["llama-3"]),
        }

        with caplog.at_level(logging.INFO, logger="update_models"):
            from update_models import main
            main()

        # Both providers should have run
        run_messages = [r.message for r in caplog.records if "Running" in r.message]
        provider_names = " ".join(run_messages)
        assert "Nvidia" in provider_names
        assert "groq" in provider_names

    @patch("update_models.setup_logging")
    @patch("update_models.discover_providers")
    @patch("update_models.save_yaml_file")
    @patch("update_models.create_backup", return_value=MagicMock())
    @patch("update_models.cleanup_temp_files")
    def test_registry_results_in_provider_models(
        self, mock_cleanup, mock_backup, mock_save, mock_discover, mock_setup_log
    ):
        """Registry provider results should flow into the YAML update logic."""
        mock_discover.return_value = {
            "Nvidia": _make_fake_fetcher("Nvidia", ["model-a", "model-b"]),
        }

        # Create a mock YAML structure that has the Nvidia endpoint
        mock_yaml_data = {
            "endpoints": {
                "custom": [
                    {
                        "name": "Nvidia",
                        "models": {"default": [], "fetch": True},
                    }
                ]
            }
        }

        with patch("update_models.load_yaml_file", return_value=mock_yaml_data), \
             patch("update_models.os.path.dirname", return_value="/fake"), \
             patch("update_models.Path") as MockPath:
            # Make yaml_path.exists() return True
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True
            MockPath.return_value = mock_path_instance

            from update_models import main
            main()

        # Verify the YAML data was updated with the fetched models
        assert mock_yaml_data["endpoints"]["custom"][0]["models"]["default"] == ["model-a", "model-b"]
        assert mock_yaml_data["endpoints"]["custom"][0]["models"]["fetch"] is False

    @patch("update_models.setup_logging")
    @patch("update_models.discover_providers")
    @patch("update_models.load_yaml_file", return_value=None)
    @patch("update_models.cleanup_temp_files")
    def test_failed_provider_tracked(
        self, mock_cleanup, mock_load_yaml, mock_discover, mock_setup_log, caplog
    ):
        """Providers that fail should be tracked in stats."""
        mock_discover.return_value = {
            "Nvidia": _make_fake_fetcher("Nvidia", [], FetchStatus.NETWORK_ERROR),
        }

        with caplog.at_level(logging.WARNING, logger="update_models"):
            from update_models import main
            main()

        warning_messages = [r.message for r in caplog.records if r.levelno >= logging.WARNING]
        assert any("Nvidia" in m for m in warning_messages)
