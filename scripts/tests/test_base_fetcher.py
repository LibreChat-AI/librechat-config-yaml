"""Tests for BaseFetcher ABC enforcement and concrete instantiation (REQ-F1)."""
from __future__ import annotations

from typing import Optional

import pytest

from providers.base import BaseFetcher, FetchResult, FetchStatus


class TestABCEnforcement:
    def test_abc_enforcement(self):
        """BaseFetcher cannot be instantiated directly -- it is abstract."""
        with pytest.raises(TypeError):
            BaseFetcher()

    def test_missing_one_method(self):
        """A subclass implementing only 2 of 3 methods raises TypeError on instantiation."""

        class Partial(BaseFetcher):
            provider_name = "partial"

            def get_api_key(self) -> Optional[str]:
                return None

            def fetch_models(self) -> FetchResult:
                return FetchResult(
                    provider_name=self.provider_name,
                    models=[],
                    status=FetchStatus.EMPTY,
                )

            # post_process deliberately not implemented

        with pytest.raises(TypeError):
            Partial()

    def test_concrete_instantiation(self, concrete_fetcher_class):
        """A subclass implementing all 3 methods can be instantiated."""
        fetcher = concrete_fetcher_class()
        assert fetcher.provider_name == "test_provider"

    def test_run_template_method(self, concrete_fetcher_class):
        """run() calls fetch_models(), then post_process() on success, returns FetchResult."""
        fetcher = concrete_fetcher_class()
        result = fetcher.run()

        assert isinstance(result, FetchResult)
        assert result.status == FetchStatus.SUCCESS
        assert result.models == ["model-a", "model-b"]
        assert result.model_count == 2

    def test_run_catches_exceptions(self):
        """run() returns FetchResult with NETWORK_ERROR status when fetch_models() raises."""

        class FailingFetcher(BaseFetcher):
            provider_name = "failing"

            def get_api_key(self) -> Optional[str]:
                return None

            def fetch_models(self) -> FetchResult:
                raise ConnectionError("Network down")

            def post_process(self, models: list[str]) -> list[str]:
                return models

        fetcher = FailingFetcher()
        result = fetcher.run()

        assert result.status == FetchStatus.NETWORK_ERROR
        assert result.error_message == "Network down"
        assert result.models == []
        assert result.model_count == 0
