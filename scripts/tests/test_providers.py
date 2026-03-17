"""Tests for converted provider fetchers."""
from __future__ import annotations

import inspect
import re
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
        from providers.nvidia import NvidiaFetcher
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [{"id": "a"}, {"id": "b"}]}

        with patch.object(NvidiaFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert result.models == ["a", "b"]

    def test_nvidia_post_process(self):
        fetcher = self._make()
        assert fetcher.post_process(["b", "a", "a"]) == ["a", "b"]

    def test_nvidia_fetch_empty_data(self):
        from providers.nvidia import NvidiaFetcher
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": []}

        with patch.object(NvidiaFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.EMPTY

    def test_nvidia_fetch_malformed_response(self):
        """Malformed response (wrong structure) returns parse_error with pydantic details."""
        from providers.nvidia import NvidiaFetcher
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"models": [{"name": "x"}]}  # wrong shape

        with patch.object(NvidiaFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.PARSE_ERROR
        assert "data" in result.error_message  # pydantic names the missing field


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
        from providers.groq import GroqFetcher
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

        with patch("providers.groq.load_dotenv"), \
             patch.object(GroqFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        # whisper model should be filtered out
        assert "whisper-large-v3" not in result.models
        assert "llama-3" in result.models
        assert "mixtral-8x7b" in result.models

    def test_groq_post_process(self):
        fetcher = self._make()
        assert fetcher.post_process(["z", "a", "a"]) == ["a", "z"]

    def test_groq_fetch_malformed_response(self, monkeypatch):
        """Malformed response returns parse_error with pydantic details."""
        from providers.groq import GroqFetcher
        monkeypatch.setenv("GROQ_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": "not-openai-format"}

        with patch("providers.groq.load_dotenv"), \
             patch.object(GroqFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.PARSE_ERROR
        assert "data" in result.error_message


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
        from providers.github_models import GithubModelsFetcher
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"name": "x"}, {"name": "y"}]

        with patch.object(GithubModelsFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert result.models == ["x", "y"]

    def test_github_post_process(self):
        fetcher = self._make()
        assert fetcher.post_process(["c", "a", "a"]) == ["a", "c"]

    def test_github_fetch_malformed_entries(self):
        """Array with entries missing 'name' returns parse_error."""
        from providers.github_models import GithubModelsFetcher
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"id": "no-name-field"}]  # has id, not name

        with patch.object(GithubModelsFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.PARSE_ERROR
        assert "name" in result.error_message


# ---------------------------------------------------------------------------
# OpenRouter
# ---------------------------------------------------------------------------

class TestOpenRouterFetcher:
    def _make(self):
        from providers.openrouter import OpenRouterFetcher
        return OpenRouterFetcher()

    def test_openrouter_provider_name(self):
        from providers.openrouter import OpenRouterFetcher
        assert OpenRouterFetcher.provider_name == "OpenRouter"

    def test_openrouter_get_api_key_returns_none(self):
        fetcher = self._make()
        assert fetcher.get_api_key() is None

    def test_openrouter_fetch_success(self):
        from providers.openrouter import OpenRouterFetcher
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [{"id": "gpt-4"}, {"id": "claude-3"}]}

        with patch.object(OpenRouterFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert "gpt-4" in result.models
        assert "claude-3" in result.models

    def test_openrouter_post_process_auto_first(self):
        fetcher = self._make()
        result = fetcher.post_process(["model/a", "openrouter/auto", "model/b"])
        assert result[0] == "openrouter/auto"

    def test_openrouter_post_process_suffix_grouping(self):
        fetcher = self._make()
        result = fetcher.post_process([
            "model/a:free", "model/b:free",
            "model/c:nitro",
            "model/d:beta",
            "model/e:extended",
        ])
        assert "---FREE---" in result
        assert "---NITRO---" in result
        assert "---BETA---" in result
        assert "---EXTENDED---" in result
        free_idx = result.index("---FREE---")
        nitro_idx = result.index("---NITRO---")
        assert free_idx < nitro_idx  # FREE before NITRO

    def test_openrouter_post_process_prefix_grouping(self):
        fetcher = self._make()
        # 3+ models from same prefix -> gets own header
        result = fetcher.post_process([
            "acme/model-a", "acme/model-b", "acme/model-c",
            "solo/model-x",
        ])
        assert "---ACME---" in result
        assert "---OTHERS---" in result
        # solo/ has <=2 models so goes to OTHERS
        assert "solo/model-x" in result[result.index("---OTHERS---"):]

    def test_openrouter_post_process_dedup(self):
        fetcher = self._make()
        result = fetcher.post_process(["model/a", "model/a", "model/b"])
        model_count = sum(1 for r in result if not r.startswith("---"))
        assert model_count == 2  # no duplicates

    def test_openrouter_post_process_deterministic(self):
        fetcher = self._make()
        input_models = ["z/a", "a/b", "m/c:free", "m/d:free", "openrouter/auto"]
        result1 = fetcher.post_process(list(input_models))
        result2 = fetcher.post_process(list(input_models))
        assert result1 == result2  # identical output

    def test_openrouter_no_stealth(self):
        fetcher = self._make()
        result = fetcher.post_process(["model/a:free", "model/b"])
        assert "---STEALTH---" not in result

    def test_openrouter_malformed_response(self):
        from providers.openrouter import OpenRouterFetcher
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"wrong": "format"}

        with patch.object(OpenRouterFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.PARSE_ERROR


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegistration:
    def test_all_four_registered(self):
        import importlib

        # Force re-import to trigger __init_subclass__ registration
        # (clean_registry fixture clears the registry, but cached modules
        # won't re-fire __init_subclass__, so we reload them)
        import providers.nvidia
        import providers.groq
        import providers.github_models
        import providers.openrouter

        importlib.reload(providers.nvidia)
        importlib.reload(providers.groq)
        importlib.reload(providers.github_models)
        importlib.reload(providers.openrouter)

        registry = get_registry()
        assert "Nvidia" in registry
        assert "groq" in registry
        assert "Github Models" in registry
        assert "OpenRouter" in registry
