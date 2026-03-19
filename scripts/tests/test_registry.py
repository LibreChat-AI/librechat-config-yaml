"""Tests for __init_subclass__ registration and discover_providers() (REQ-F3)."""
from __future__ import annotations

from typing import Optional

from providers.base import BaseFetcher, FetchResult, FetchStatus, get_registry


class TestAutoRegistration:
    def test_auto_registration(self):
        """Defining a concrete class with provider_name causes it to appear in registry."""

        class FooFetcher(BaseFetcher):
            provider_name = "foo"

            def get_api_key(self) -> Optional[str]:
                return None

            def fetch_models(self) -> FetchResult:
                return FetchResult(
                    provider_name=self.provider_name,
                    models=[],
                    status=FetchStatus.EMPTY,
                )

            def post_process(self, models: list[str]) -> list[str]:
                return models

        registry = get_registry()
        assert "foo" in registry
        assert registry["foo"] is FooFetcher

    def test_abstract_not_registered(self):
        """A subclass without provider_name (empty string) is NOT in the registry."""

        class AbstractIntermediate(BaseFetcher):
            # No provider_name set (inherits empty string default)
            pass

        registry = get_registry()
        assert AbstractIntermediate not in registry.values()

    def test_duplicate_registration(self):
        """Defining two classes with same provider_name -- last one wins."""

        class First(BaseFetcher):  # noqa: F841 -- registered via __init_subclass__ side effect
            provider_name = "dup"

            def get_api_key(self) -> Optional[str]:
                return None

            def fetch_models(self) -> FetchResult:
                return FetchResult(
                    provider_name=self.provider_name,
                    models=[],
                    status=FetchStatus.EMPTY,
                )

            def post_process(self, models: list[str]) -> list[str]:
                return models

        class Second(BaseFetcher):
            provider_name = "dup"

            def get_api_key(self) -> Optional[str]:
                return None

            def fetch_models(self) -> FetchResult:
                return FetchResult(
                    provider_name=self.provider_name,
                    models=[],
                    status=FetchStatus.EMPTY,
                )

            def post_process(self, models: list[str]) -> list[str]:
                return models

        registry = get_registry()
        assert registry["dup"] is Second

    def test_get_registry_returns_copy(self):
        """get_registry() returns a copy -- modifying it doesn't affect internal registry."""
        registry = get_registry()
        registry["injected"] = "should_not_persist"
        assert "injected" not in get_registry()


class TestDiscoverProviders:
    def test_discover_all(self):
        """discover_providers() returns a dict (may be empty with no concrete providers yet)."""
        from providers import discover_providers

        result = discover_providers()
        assert isinstance(result, dict)
