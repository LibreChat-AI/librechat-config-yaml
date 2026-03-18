"""Tests for staleness detection in update_models.py."""
from __future__ import annotations

import logging
import os
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from providers.base import BaseFetcher, FetchResult, FetchStatus


@pytest.fixture
def yaml_data_with_models():
    """YAML data with 10 models for Nvidia."""
    return {
        "version": "1.0",
        "endpoints": {
            "custom": [
                {
                    "name": "Nvidia",
                    "models": {
                        "default": ["m%d" % i for i in range(10)],
                        "fetch": False,
                    },
                }
            ]
        },
    }


@pytest.fixture
def yaml_data_empty_provider():
    """YAML data with 0 models for Nvidia (first-time population)."""
    return {
        "version": "1.0",
        "endpoints": {
            "custom": [
                {
                    "name": "Nvidia",
                    "models": {"default": [], "fetch": True},
                }
            ]
        },
    }


@pytest.fixture
def yaml_data_no_unknown():
    """YAML data without an Unknown provider."""
    return {
        "version": "1.0",
        "endpoints": {
            "custom": [
                {
                    "name": "Nvidia",
                    "models": {
                        "default": ["m%d" % i for i in range(10)],
                        "fetch": False,
                    },
                }
            ]
        },
    }


class TestCheckStaleness:
    """Unit tests for the check_staleness function."""

    def test_stale_provider_skipped(self, yaml_data_with_models):
        """Provider with 90% drop is flagged as stale."""
        from update_models import check_staleness

        is_stale, old_count, new_count = check_staleness(
            "Nvidia", ["m1"], yaml_data_with_models
        )
        assert is_stale is True
        assert old_count == 10
        assert new_count == 1

    def test_not_stale_provider_passes(self, yaml_data_with_models):
        """Provider with 20% drop is NOT flagged as stale."""
        from update_models import check_staleness

        models = ["m%d" % i for i in range(8)]
        is_stale, old_count, new_count = check_staleness(
            "Nvidia", models, yaml_data_with_models
        )
        assert is_stale is False
        assert old_count == 10
        assert new_count == 8

    def test_threshold_configurable(self, yaml_data_with_models):
        """STALENESS_THRESHOLD env var changes the detection threshold."""
        from update_models import check_staleness

        # 3 models out of 10 = 30% ratio
        models = ["m0", "m1", "m2"]

        # With threshold 0.5 (default), 30% < 50% => stale
        with patch.dict(os.environ, {"STALENESS_THRESHOLD": "0.5"}):
            import importlib
            import update_models

            importlib.reload(update_models)
            is_stale, _, _ = update_models.check_staleness(
                "Nvidia", models, yaml_data_with_models
            )
            assert is_stale is True

        # With threshold 0.2, 30% >= 20% => not stale
        with patch.dict(os.environ, {"STALENESS_THRESHOLD": "0.2"}):
            importlib.reload(update_models)
            is_stale, _, _ = update_models.check_staleness(
                "Nvidia", models, yaml_data_with_models
            )
            assert is_stale is False

        # Reload with default to not pollute other tests
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("STALENESS_THRESHOLD", None)
            importlib.reload(update_models)

    def test_first_population(self, yaml_data_empty_provider):
        """First-time population (old count 0) is never flagged as stale."""
        from update_models import check_staleness

        is_stale, old_count, new_count = check_staleness(
            "Nvidia", ["m1"], yaml_data_empty_provider
        )
        assert is_stale is False
        assert old_count == 0
        assert new_count == 1

    def test_provider_not_in_yaml(self, yaml_data_no_unknown):
        """Unknown provider not in YAML is treated as first-time (not stale)."""
        from update_models import check_staleness

        is_stale, old_count, new_count = check_staleness(
            "Unknown", ["m1"], yaml_data_no_unknown
        )
        assert is_stale is False
        assert old_count == 0
        assert new_count == 1


def _make_fake_fetcher(name, models, status=FetchStatus.SUCCESS):
    """Create a fake fetcher class for integration tests."""

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


class TestStalenessIntegration:
    """Integration test: stale provider is skipped in main()."""

    @patch("update_models.setup_logging")
    @patch("update_models.discover_providers")
    @patch("update_models.save_yaml_file")
    @patch("update_models.create_backup", return_value=MagicMock())
    @patch("update_models.cleanup_temp_files")
    def test_staleness_integration_main(
        self, mock_cleanup, mock_backup, mock_save, mock_discover, mock_setup_log, caplog
    ):
        """When a provider returns stale results, main() skips that provider."""
        mock_discover.return_value = {
            "Nvidia": _make_fake_fetcher("Nvidia", ["only-one-model"]),
        }

        # YAML data with 10 existing models for Nvidia
        mock_yaml_data = {
            "version": "1.0",
            "endpoints": {
                "custom": [
                    {
                        "name": "Nvidia",
                        "models": {
                            "default": ["m%d" % i for i in range(10)],
                            "fetch": False,
                        },
                    }
                ]
            },
        }

        with patch("update_models.load_yaml_file", return_value=mock_yaml_data), \
             patch("update_models.os.path.dirname", return_value="/fake"), \
             patch("update_models.Path") as MockPath:
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = True
            MockPath.return_value = mock_path_instance

            with caplog.at_level(logging.WARNING, logger="update_models"):
                from update_models import main
                main()

        # Nvidia models should NOT have been updated (still 10 old models)
        assert mock_yaml_data["endpoints"]["custom"][0]["models"]["default"] == [
            "m%d" % i for i in range(10)
        ]

        # A staleness warning should have been logged
        warning_messages = [r.message for r in caplog.records if r.levelno >= logging.WARNING]
        assert any("Staleness" in m or "staleness" in m.lower() for m in warning_messages)
