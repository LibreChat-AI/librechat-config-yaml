"""Tests for converted provider fetchers: NVIDIA, Groq, GitHub Models."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from providers.base import FetchResult, FetchStatus, get_registry


# ---------------------------------------------------------------------------
# NVIDIA
# ---------------------------------------------------------------------------

class TestNvidiaFetcher:
    def _make(self):
        from providers.nvidia import NvidiaFetcher
        return NvidiaFetcher()

    def test_nvidia_provider_name(self):
        from providers.nvidia import NvidiaFetcher
        assert NvidiaFetcher.provider_name == "Nvidia"

    def test_nvidia_get_api_key_returns_none(self):
        fetcher = self._make()
        assert fetcher.get_api_key() is None

    def test_nvidia_fetch_success(self):
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [{"id": "a"}, {"id": "b"}]}
        mock_resp.raise_for_status = MagicMock()

        with patch("providers.nvidia.requests.get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert result.models == ["a", "b"]

    def test_nvidia_post_process(self):
        fetcher = self._make()
        assert fetcher.post_process(["b", "a", "a"]) == ["a", "b"]

    def test_nvidia_fetch_empty_data(self):
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": []}
        mock_resp.raise_for_status = MagicMock()

        with patch("providers.nvidia.requests.get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.EMPTY


# ---------------------------------------------------------------------------
# Groq
# ---------------------------------------------------------------------------

class TestGroqFetcher:
    def _make(self):
        from providers.groq import GroqFetcher
        return GroqFetcher()

    def test_groq_provider_name(self):
        from providers.groq import GroqFetcher
        assert GroqFetcher.provider_name == "groq"

    def test_groq_no_api_key(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        with patch("providers.groq.load_dotenv"):
            fetcher = self._make()
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.AUTH_ERROR
        assert "GROQ_API_KEY" in result.error_message

    def test_groq_fetch_success(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {"id": "llama-3"},
                {"id": "whisper-large-v3"},
                {"id": "mixtral-8x7b"},
            ]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("providers.groq.load_dotenv"), \
             patch("providers.groq.requests.get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        # whisper model should be filtered out
        assert "whisper-large-v3" not in result.models
        assert "llama-3" in result.models
        assert "mixtral-8x7b" in result.models

    def test_groq_post_process(self):
        fetcher = self._make()
        assert fetcher.post_process(["z", "a", "a"]) == ["a", "z"]


# ---------------------------------------------------------------------------
# GitHub Models
# ---------------------------------------------------------------------------

class TestGithubModelsFetcher:
    def _make(self):
        from providers.github_models import GithubModelsFetcher
        return GithubModelsFetcher()

    def test_github_provider_name(self):
        from providers.github_models import GithubModelsFetcher
        assert GithubModelsFetcher.provider_name == "Github Models"

    def test_github_get_api_key_returns_none(self):
        fetcher = self._make()
        assert fetcher.get_api_key() is None

    def test_github_fetch_success(self):
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"name": "x"}, {"name": "y"}]
        mock_resp.raise_for_status = MagicMock()

        with patch("providers.github_models.requests.get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert result.models == ["x", "y"]

    def test_github_post_process(self):
        fetcher = self._make()
        assert fetcher.post_process(["c", "a", "a"]) == ["a", "c"]


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegistration:
    def test_all_three_registered(self):
        # Force-import all 3 modules to trigger __init_subclass__ registration
        import providers.nvidia  # noqa: F401
        import providers.groq  # noqa: F401
        import providers.github_models  # noqa: F401

        registry = get_registry()
        assert "Nvidia" in registry
        assert "groq" in registry
        assert "Github Models" in registry
