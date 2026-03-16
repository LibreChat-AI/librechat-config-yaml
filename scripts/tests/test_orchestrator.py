"""Tests for dual-path orchestrator logic in update_models.py."""
from __future__ import annotations

import logging
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

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


class TestDualPathOrchestrator:
    """Test that update_models.main() runs registry providers first,
    then legacy providers, skipping duplicates."""

    @patch("update_models.discover_providers")
    @patch("update_models.run_fetcher_script")
    @patch("update_models.load_yaml_file", return_value=None)
    @patch("update_models.cleanup_temp_files")
    def test_migrated_providers_skipped(
        self, mock_cleanup, mock_load_yaml, mock_run_fetcher, mock_discover, caplog
    ):
        """Providers in the registry should be skipped in the legacy loop."""
        # Set up registry with Nvidia and groq
        mock_discover.return_value = {
            "Nvidia": _make_fake_fetcher("Nvidia", ["model-a", "model-b"]),
            "groq": _make_fake_fetcher("groq", ["llama-3"]),
        }

        with caplog.at_level(logging.INFO, logger="model_updater"):
            from update_models import main
            main()

        # Legacy nvidia and groq should be skipped
        skip_messages = [r.message for r in caplog.records if "Skipping legacy" in r.message]
        skipped_scripts = " ".join(skip_messages)
        assert "nvidia" in skipped_scripts
        assert "groq" in skipped_scripts

        # run_fetcher_script should NOT be called for nvidia or groq
        called_scripts = [call.args[0] for call in mock_run_fetcher.call_args_list]
        assert "nvidia" not in called_scripts
        assert "groq" not in called_scripts

    @patch("update_models.discover_providers")
    @patch("update_models.run_fetcher_script", return_value=None)
    @patch("update_models.load_yaml_file", return_value=None)
    @patch("update_models.cleanup_temp_files")
    def test_legacy_providers_still_run(
        self, mock_cleanup, mock_load_yaml, mock_run_fetcher, mock_discover, caplog
    ):
        """Non-migrated providers should still run via legacy path."""
        # Only Nvidia is migrated
        mock_discover.return_value = {
            "Nvidia": _make_fake_fetcher("Nvidia", ["model-a"]),
        }

        with caplog.at_level(logging.INFO, logger="model_updater"):
            from update_models import main
            main()

        # run_fetcher_script should be called for non-migrated providers
        called_scripts = [call.args[0] for call in mock_run_fetcher.call_args_list]
        # cohere, deepseek etc. should be in the called list
        assert "cohere" in called_scripts
        assert "deepseek" in called_scripts
        # nvidia should NOT be in the called list
        assert "nvidia" not in called_scripts

    @patch("update_models.discover_providers")
    @patch("update_models.run_fetcher_script", return_value=None)
    @patch("update_models.save_yaml_file")
    @patch("update_models.create_backup", return_value=MagicMock())
    @patch("update_models.cleanup_temp_files")
    def test_registry_results_in_provider_models(
        self, mock_cleanup, mock_backup, mock_save, mock_run_fetcher, mock_discover
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
