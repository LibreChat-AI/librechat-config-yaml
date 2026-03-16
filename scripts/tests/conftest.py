from __future__ import annotations

import pytest

from providers.base import BaseFetcher, FetchResult, FetchStatus, _registry


@pytest.fixture(autouse=True)
def clean_registry():
    """Save and restore registry state around each test to prevent leaking."""
    saved = dict(_registry)
    yield
    _registry.clear()
    _registry.update(saved)


@pytest.fixture
def concrete_fetcher_class():
    """Return a dynamically-created concrete BaseFetcher subclass."""
    from typing import Optional

    class TestFetcher(BaseFetcher):
        provider_name = "test_provider"

        def get_api_key(self) -> Optional[str]:
            return None

        def fetch_models(self) -> FetchResult:
            return FetchResult(
                provider_name=self.provider_name,
                models=["model-a", "model-b"],
                status=FetchStatus.SUCCESS,
            )

        def post_process(self, models: list[str]) -> list[str]:
            return sorted(models)

    return TestFetcher


@pytest.fixture
def fetch_result_factory():
    """Return a factory function for creating FetchResult instances with defaults."""

    def _create(**kwargs):
        defaults = {
            "provider_name": "test",
            "models": ["m1", "m2"],
            "status": FetchStatus.SUCCESS,
        }
        defaults.update(kwargs)
        return FetchResult(**defaults)

    return _create
