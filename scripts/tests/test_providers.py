"""Tests for converted provider fetchers."""
from __future__ import annotations

import importlib
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
# 302AI
# ---------------------------------------------------------------------------

class TestAI302Fetcher:
    def _make(self):
        from providers.ai302 import AI302Fetcher
        return AI302Fetcher()

    def test_ai302_provider_name(self):
        from providers.ai302 import AI302Fetcher
        assert AI302Fetcher.provider_name == "302AI"

    def test_ai302_no_api_key(self, monkeypatch):
        monkeypatch.delenv("AI302_API_KEY", raising=False)
        with patch("providers.ai302.load_dotenv"):
            fetcher = self._make()
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.AUTH_ERROR
        assert "AI302_API_KEY" in result.error_message

    def test_ai302_fetch_success(self, monkeypatch):
        from providers.ai302 import AI302Fetcher
        monkeypatch.setenv("AI302_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [{"id": "model-a"}, {"id": "model-b"}]
        }

        with patch("providers.ai302.load_dotenv"), \
             patch.object(AI302Fetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert "model-a" in result.models
        assert "model-b" in result.models

    def test_ai302_post_process_dedup_and_sort(self):
        fetcher = self._make()
        assert fetcher.post_process(["z", "a", "a"]) == ["a", "z"]

    def test_ai302_malformed_response(self, monkeypatch):
        from providers.ai302 import AI302Fetcher
        monkeypatch.setenv("AI302_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"wrong": "format"}

        with patch("providers.ai302.load_dotenv"), \
             patch.object(AI302Fetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.PARSE_ERROR


# ---------------------------------------------------------------------------
# DeepSeek
# ---------------------------------------------------------------------------

class TestDeepSeekFetcher:
    def _make(self):
        from providers.deepseek import DeepSeekFetcher
        return DeepSeekFetcher()

    def test_deepseek_provider_name(self):
        from providers.deepseek import DeepSeekFetcher
        assert DeepSeekFetcher.provider_name == "deepseek"

    def test_deepseek_no_api_key(self, monkeypatch):
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        with patch("providers.deepseek.load_dotenv"):
            fetcher = self._make()
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.AUTH_ERROR
        assert "DEEPSEEK_API_KEY" in result.error_message

    def test_deepseek_fetch_success(self, monkeypatch):
        from providers.deepseek import DeepSeekFetcher
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [{"id": "deepseek-chat"}, {"id": "deepseek-coder"}]
        }

        with patch("providers.deepseek.load_dotenv"), \
             patch.object(DeepSeekFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert "deepseek-chat" in result.models
        assert "deepseek-coder" in result.models

    def test_deepseek_fetch_success_flat_array(self, monkeypatch):
        from providers.deepseek import DeepSeekFetcher
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"id": "model-a"}, {"id": "model-b"}]

        with patch("providers.deepseek.load_dotenv"), \
             patch.object(DeepSeekFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert "model-a" in result.models
        assert "model-b" in result.models

    def test_deepseek_post_process_dedup_and_sort(self):
        fetcher = self._make()
        assert fetcher.post_process(["z", "a", "a"]) == ["a", "z"]

    def test_deepseek_malformed_response(self, monkeypatch):
        from providers.deepseek import DeepSeekFetcher
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"wrong": "format"}

        with patch("providers.deepseek.load_dotenv"), \
             patch.object(DeepSeekFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.PARSE_ERROR


# ---------------------------------------------------------------------------
# Fireworks
# ---------------------------------------------------------------------------

class TestFireworksFetcher:
    def _make(self):
        from providers.fireworks import FireworksFetcher
        return FireworksFetcher()

    def test_fireworks_provider_name(self):
        from providers.fireworks import FireworksFetcher
        assert FireworksFetcher.provider_name == "Fireworks"

    def test_fireworks_no_api_key(self, monkeypatch):
        monkeypatch.delenv("FIREWORKS_API_KEY", raising=False)
        with patch("providers.fireworks.load_dotenv"):
            fetcher = self._make()
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.AUTH_ERROR
        assert "FIREWORKS_API_KEY" in result.error_message

    def test_fireworks_fetch_success(self, monkeypatch):
        from providers.fireworks import FireworksFetcher
        monkeypatch.setenv("FIREWORKS_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {"id": "llama-v3", "supports_chat": True},
                {"id": "whisper-v3", "supports_chat": False},
            ]
        }

        with patch("providers.fireworks.load_dotenv"), \
             patch.object(FireworksFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert "llama-v3" in result.models
        assert "whisper-v3" not in result.models

    def test_fireworks_post_process_dedup_and_sort(self):
        fetcher = self._make()
        assert fetcher.post_process(["z", "a", "a"]) == ["a", "z"]

    def test_fireworks_malformed_response(self, monkeypatch):
        from providers.fireworks import FireworksFetcher
        monkeypatch.setenv("FIREWORKS_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"wrong": "format"}

        with patch("providers.fireworks.load_dotenv"), \
             patch.object(FireworksFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.PARSE_ERROR


# ---------------------------------------------------------------------------
# GLHF
# ---------------------------------------------------------------------------

class TestGLHFFetcher:
    def _make(self):
        from providers.glhf import GLHFFetcher
        return GLHFFetcher()

    def test_glhf_provider_name(self):
        from providers.glhf import GLHFFetcher
        assert GLHFFetcher.provider_name == "glhf.chat"

    def test_glhf_no_api_key(self, monkeypatch):
        monkeypatch.delenv("GLHF_API_KEY", raising=False)
        with patch("providers.glhf.load_dotenv"):
            fetcher = self._make()
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.AUTH_ERROR
        assert "GLHF_API_KEY" in result.error_message

    def test_glhf_fetch_success(self, monkeypatch):
        from providers.glhf import GLHFFetcher
        monkeypatch.setenv("GLHF_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [{"id": "hf:model-a"}, {"id": "hf:model-b"}]
        }

        with patch("providers.glhf.load_dotenv"), \
             patch.object(GLHFFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert "hf:model-a" in result.models
        assert "hf:model-b" in result.models

    def test_glhf_post_process_dedup_and_sort(self):
        fetcher = self._make()
        assert fetcher.post_process(["z", "a", "a"]) == ["a", "z"]

    def test_glhf_malformed_response(self, monkeypatch):
        from providers.glhf import GLHFFetcher
        monkeypatch.setenv("GLHF_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"wrong": "format"}

        with patch("providers.glhf.load_dotenv"), \
             patch.object(GLHFFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.PARSE_ERROR


# ---------------------------------------------------------------------------
# Kluster
# ---------------------------------------------------------------------------

class TestKlusterFetcher:
    def _make(self):
        from providers.kluster import KlusterFetcher
        return KlusterFetcher()

    def test_kluster_provider_name(self):
        from providers.kluster import KlusterFetcher
        assert KlusterFetcher.provider_name == "Kluster"

    def test_kluster_no_api_key(self, monkeypatch):
        monkeypatch.delenv("KLUSTER_API_KEY", raising=False)
        with patch("providers.kluster.load_dotenv"):
            fetcher = self._make()
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.AUTH_ERROR
        assert "KLUSTER_API_KEY" in result.error_message

    def test_kluster_fetch_success(self, monkeypatch):
        from providers.kluster import KlusterFetcher
        monkeypatch.setenv("KLUSTER_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [{"id": "model-a"}, {"id": "model-b"}]
        }

        with patch("providers.kluster.load_dotenv"), \
             patch.object(KlusterFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert "model-a" in result.models
        assert "model-b" in result.models

    def test_kluster_post_process_dedup_and_sort(self):
        fetcher = self._make()
        assert fetcher.post_process(["z", "a", "a"]) == ["a", "z"]

    def test_kluster_malformed_response(self, monkeypatch):
        from providers.kluster import KlusterFetcher
        monkeypatch.setenv("KLUSTER_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"wrong": "format"}

        with patch("providers.kluster.load_dotenv"), \
             patch.object(KlusterFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.PARSE_ERROR


# ---------------------------------------------------------------------------
# Mistral
# ---------------------------------------------------------------------------

class TestMistralFetcher:
    def _make(self):
        from providers.mistral import MistralFetcher
        return MistralFetcher()

    def test_mistral_provider_name(self):
        from providers.mistral import MistralFetcher
        assert MistralFetcher.provider_name == "Mistral"

    def test_mistral_no_api_key(self, monkeypatch):
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
        with patch("providers.mistral.load_dotenv"):
            fetcher = self._make()
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.AUTH_ERROR
        assert "MISTRAL_API_KEY" in result.error_message

    def test_mistral_fetch_success(self, monkeypatch):
        from providers.mistral import MistralFetcher
        monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [{"id": "mistral-large"}, {"id": "mistral-small"}]
        }

        with patch("providers.mistral.load_dotenv"), \
             patch.object(MistralFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert "mistral-large" in result.models
        assert "mistral-small" in result.models

    def test_mistral_fetch_success_flat_array(self, monkeypatch):
        from providers.mistral import MistralFetcher
        monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"id": "model-a"}, {"id": "model-b"}]

        with patch("providers.mistral.load_dotenv"), \
             patch.object(MistralFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert "model-a" in result.models
        assert "model-b" in result.models

    def test_mistral_post_process_dedup_and_sort(self):
        fetcher = self._make()
        assert fetcher.post_process(["z", "a", "a"]) == ["a", "z"]

    def test_mistral_malformed_response(self, monkeypatch):
        from providers.mistral import MistralFetcher
        monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"wrong": "format"}

        with patch("providers.mistral.load_dotenv"), \
             patch.object(MistralFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.PARSE_ERROR


# ---------------------------------------------------------------------------
# Hyperbolic
# ---------------------------------------------------------------------------

class TestHyperbolicFetcher:
    def _make(self):
        from providers.hyperbolic import HyperbolicFetcher
        return HyperbolicFetcher()

    def test_hyperbolic_provider_name(self):
        from providers.hyperbolic import HyperbolicFetcher
        assert HyperbolicFetcher.provider_name == "Hyperbolic"

    def test_hyperbolic_no_api_key(self, monkeypatch):
        monkeypatch.delenv("HYPERBOLIC_API_KEY", raising=False)
        with patch("providers.hyperbolic.load_dotenv"):
            fetcher = self._make()
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.AUTH_ERROR
        assert "HYPERBOLIC_API_KEY" in result.error_message

    def test_hyperbolic_fetch_success(self, monkeypatch):
        from providers.hyperbolic import HyperbolicFetcher
        monkeypatch.setenv("HYPERBOLIC_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {"id": "llama-3", "supports_image_input": False},
                {"id": "sdxl", "supports_image_input": True},
                {"id": "TTS"},
            ]
        }

        with patch("providers.hyperbolic.load_dotenv"), \
             patch.object(HyperbolicFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert "llama-3" in result.models
        assert "sdxl" not in result.models
        assert "TTS" not in result.models

    def test_hyperbolic_post_process_dedup_and_sort(self):
        fetcher = self._make()
        assert fetcher.post_process(["z", "a", "a"]) == ["a", "z"]

    def test_hyperbolic_malformed_response(self, monkeypatch):
        from providers.hyperbolic import HyperbolicFetcher
        monkeypatch.setenv("HYPERBOLIC_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"wrong": "format"}

        with patch("providers.hyperbolic.load_dotenv"), \
             patch.object(HyperbolicFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.PARSE_ERROR


# ---------------------------------------------------------------------------
# xAI
# ---------------------------------------------------------------------------

class TestXAIFetcher:
    def _make(self):
        from providers.xai import XAIFetcher
        return XAIFetcher()

    def test_xai_provider_name(self):
        from providers.xai import XAIFetcher
        assert XAIFetcher.provider_name == "xai"

    def test_xai_no_api_key(self, monkeypatch):
        monkeypatch.delenv("XAI_API_KEY", raising=False)
        with patch("providers.xai.load_dotenv"):
            fetcher = self._make()
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.AUTH_ERROR
        assert "XAI_API_KEY" in result.error_message

    def test_xai_fetch_success(self, monkeypatch):
        from providers.xai import XAIFetcher
        monkeypatch.setenv("XAI_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [{"id": "grok-2"}, {"id": "grok-3"}]
        }

        with patch("providers.xai.load_dotenv"), \
             patch.object(XAIFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert "grok-2" in result.models
        assert "grok-3" in result.models

    def test_xai_post_process_dedup_and_sort(self):
        fetcher = self._make()
        assert fetcher.post_process(["z", "a", "a"]) == ["a", "z"]

    def test_xai_malformed_response(self, monkeypatch):
        from providers.xai import XAIFetcher
        monkeypatch.setenv("XAI_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"wrong": "format"}

        with patch("providers.xai.load_dotenv"), \
             patch.object(XAIFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.PARSE_ERROR


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
# NanoGPT
# ---------------------------------------------------------------------------

class TestNanoGPTFetcher:
    def _make(self):
        from providers.nanogpt import NanoGPTFetcher
        return NanoGPTFetcher()

    def test_nanogpt_provider_name(self):
        from providers.nanogpt import NanoGPTFetcher
        assert NanoGPTFetcher.provider_name == "NanoGPT"

    def test_nanogpt_get_api_key_returns_none(self):
        fetcher = self._make()
        assert fetcher.get_api_key() is None

    def test_nanogpt_fetch_success(self):
        from providers.nanogpt import NanoGPTFetcher
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [{"id": "gpt-4o"}, {"id": "claude-3"}]}

        with patch.object(NanoGPTFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert "gpt-4o" in result.models
        assert "claude-3" in result.models

    def test_nanogpt_uses_v1_endpoint(self):
        from providers.nanogpt import NanoGPTFetcher
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [{"id": "test-model"}]}

        with patch.object(NanoGPTFetcher, "_http_get", return_value=mock_resp) as mock_http_get:
            fetcher.fetch_models()

        url_arg = mock_http_get.call_args[0][0]
        assert "/api/v1/models" in url_arg

    def test_nanogpt_post_process(self):
        fetcher = self._make()
        assert fetcher.post_process(["b", "a", "a"]) == ["a", "b"]

    def test_nanogpt_malformed_response(self):
        from providers.nanogpt import NanoGPTFetcher
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"wrong": "format"}

        with patch.object(NanoGPTFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.PARSE_ERROR


# ---------------------------------------------------------------------------
# APIpie
# ---------------------------------------------------------------------------

class TestAPIpieFetcher:
    def _make(self):
        from providers.apipie import APIpieFetcher
        return APIpieFetcher()

    def test_apipie_provider_name(self):
        from providers.apipie import APIpieFetcher
        assert APIpieFetcher.provider_name == "APIpie"

    def test_apipie_get_api_key_returns_none(self):
        fetcher = self._make()
        assert fetcher.get_api_key() is None

    def test_apipie_fetch_success_openai_format(self):
        from providers.apipie import APIpieFetcher
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [{"id": "gpt-4"}, {"id": "claude-3"}]}

        with patch.object(APIpieFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert "gpt-4" in result.models
        assert "claude-3" in result.models

    def test_apipie_uses_v1_endpoint(self):
        from providers.apipie import APIpieFetcher
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [{"id": "test-model"}]}

        with patch.object(APIpieFetcher, "_http_get", return_value=mock_resp) as mock_http_get:
            fetcher.fetch_models()

        url_arg = mock_http_get.call_args[0][0]
        assert "/v1/models" in url_arg

    def test_apipie_post_process_free_models_first(self):
        fetcher = self._make()
        result = fetcher.post_process(["gpt-4", "free/llama-3", "claude"])
        assert result == ["---FREE---", "free/llama-3", "claude", "gpt-4"]

    def test_apipie_post_process_no_free(self):
        fetcher = self._make()
        result = fetcher.post_process(["gpt-4", "claude"])
        assert result == ["claude", "gpt-4"]
        assert "---FREE---" not in result


# ---------------------------------------------------------------------------
# SambaNova
# ---------------------------------------------------------------------------

class TestSambaNova:
    def _make(self):
        from providers.sambanova import SambaNova
        return SambaNova()

    def test_sambanova_provider_name(self):
        from providers.sambanova import SambaNova
        assert SambaNova.provider_name == "SambaNova"

    def test_sambanova_get_api_key_returns_none(self):
        fetcher = self._make()
        assert fetcher.get_api_key() is None

    def test_sambanova_returns_hardcoded_models(self):
        fetcher = self._make()
        result = fetcher.fetch_models()
        assert result.status == FetchStatus.SUCCESS
        assert len(result.models) > 0

    def test_sambanova_models_are_strings(self):
        fetcher = self._make()
        result = fetcher.fetch_models()
        for model in result.models:
            assert isinstance(model, str)
            assert model.strip() != ""

    def test_sambanova_post_process(self):
        fetcher = self._make()
        assert fetcher.post_process(["b", "a", "a"]) == ["a", "b"]

    def test_sambanova_no_scraping_imports(self):
        import importlib
        mod = importlib.import_module("providers.sambanova")
        source = inspect.getsource(mod)
        assert "BeautifulSoup" not in source
        assert "bs4" not in source


# ---------------------------------------------------------------------------
# Perplexity
# ---------------------------------------------------------------------------

class TestPerplexityFetcher:
    def _make(self):
        from providers.perplexity import PerplexityFetcher
        return PerplexityFetcher()

    def test_perplexity_provider_name(self):
        from providers.perplexity import PerplexityFetcher
        assert PerplexityFetcher.provider_name == "Perplexity"

    def test_perplexity_get_api_key_returns_none(self):
        fetcher = self._make()
        assert fetcher.get_api_key() is None

    def test_perplexity_returns_hardcoded_models(self):
        fetcher = self._make()
        result = fetcher.fetch_models()
        assert result.status == FetchStatus.SUCCESS
        assert "sonar" in result.models
        assert "sonar-pro" in result.models

    def test_perplexity_all_models_match_pattern(self):
        from providers.perplexity import PerplexityFetcher
        pattern = re.compile(r"^sonar(-[a-z0-9]+)*$")
        for model in PerplexityFetcher.MODELS:
            assert pattern.match(model), f"Model '{model}' does not match pattern"

    def test_perplexity_post_process(self):
        fetcher = self._make()
        assert fetcher.post_process(["b", "a", "a"]) == ["a", "b"]

    def test_perplexity_no_scraping_imports(self):
        import importlib
        mod = importlib.import_module("providers.perplexity")
        source = inspect.getsource(mod)
        assert "BeautifulSoup" not in source
        assert "bs4" not in source


# ---------------------------------------------------------------------------
# TogetherAI
# ---------------------------------------------------------------------------

class TestTogetherAIFetcher:
    def _make(self):
        from providers.togetherai import TogetherAIFetcher
        return TogetherAIFetcher()

    def test_togetherai_provider_name(self):
        from providers.togetherai import TogetherAIFetcher
        assert TogetherAIFetcher.provider_name == "together.ai"

    def test_togetherai_no_api_key(self, monkeypatch):
        monkeypatch.delenv("TOGETHERAI_API_KEY", raising=False)
        with patch("providers.togetherai.load_dotenv"):
            fetcher = self._make()
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.AUTH_ERROR
        assert "TOGETHERAI_API_KEY" in result.error_message

    def test_togetherai_fetch_success(self, monkeypatch):
        from providers.togetherai import TogetherAIFetcher
        monkeypatch.setenv("TOGETHERAI_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"id": "llama-3", "type": "chat"},
            {"id": "stable-diffusion", "type": "image"},
            {"id": "mixtral", "type": "chat"},
        ]

        with patch("providers.togetherai.load_dotenv"), \
             patch.object(TogetherAIFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert "llama-3" in result.models
        assert "mixtral" in result.models
        assert "stable-diffusion" not in result.models  # filtered by type!=chat

    def test_togetherai_post_process(self):
        fetcher = self._make()
        assert fetcher.post_process(["z", "a", "a"]) == ["a", "z"]

    def test_togetherai_malformed_response(self, monkeypatch):
        from providers.togetherai import TogetherAIFetcher
        monkeypatch.setenv("TOGETHERAI_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": "not-array"}

        with patch("providers.togetherai.load_dotenv"), \
             patch.object(TogetherAIFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.PARSE_ERROR


# ---------------------------------------------------------------------------
# Cohere
# ---------------------------------------------------------------------------

class TestCohereFetcher:
    def _make(self):
        from providers.cohere import CohereFetcher
        return CohereFetcher()

    def test_cohere_provider_name(self):
        from providers.cohere import CohereFetcher
        assert CohereFetcher.provider_name == "cohere"

    def test_cohere_no_api_key(self, monkeypatch):
        monkeypatch.delenv("COHERE_API_KEY", raising=False)
        with patch("providers.cohere.load_dotenv"):
            fetcher = self._make()
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.AUTH_ERROR
        assert "COHERE_API_KEY" in result.error_message

    def test_cohere_fetch_success(self, monkeypatch):
        from providers.cohere import CohereFetcher
        monkeypatch.setenv("COHERE_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "models": [
                {"name": "command-r", "endpoints": ["chat", "generate"]},
                {"name": "embed-english", "endpoints": ["embed"]},
            ]
        }

        with patch("providers.cohere.load_dotenv"), \
             patch.object(CohereFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert "command-r" in result.models
        assert "embed-english" not in result.models  # no "chat" in endpoints

    def test_cohere_post_process(self):
        fetcher = self._make()
        assert fetcher.post_process(["z", "a", "a"]) == ["a", "z"]

    def test_cohere_malformed_response(self, monkeypatch):
        from providers.cohere import CohereFetcher
        monkeypatch.setenv("COHERE_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"wrong": "format"}

        with patch("providers.cohere.load_dotenv"), \
             patch.object(CohereFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.PARSE_ERROR


# ---------------------------------------------------------------------------
# Unify
# ---------------------------------------------------------------------------

class TestUnifyFetcher:
    def _make(self):
        from providers.unify import UnifyFetcher
        return UnifyFetcher()

    def test_unify_provider_name(self):
        from providers.unify import UnifyFetcher
        assert UnifyFetcher.provider_name == "Unify"

    def test_unify_no_api_key(self, monkeypatch):
        monkeypatch.delenv("UNIFY_API_KEY", raising=False)
        with patch("providers.unify.load_dotenv"):
            fetcher = self._make()
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.AUTH_ERROR
        assert "UNIFY_API_KEY" in result.error_message

    def test_unify_fetch_success(self, monkeypatch):
        from providers.unify import UnifyFetcher
        monkeypatch.setenv("UNIFY_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            "claude-3@anthropic",
            "gpt-4@openai",
            "llama-3@together",
        ]

        with patch("providers.unify.load_dotenv"), \
             patch.object(UnifyFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert "claude-3@anthropic" in result.models
        assert "gpt-4@openai" in result.models
        assert "llama-3@together" in result.models

    def test_unify_post_process(self):
        fetcher = self._make()
        assert fetcher.post_process(["z", "a", "a"]) == ["a", "z"]

    def test_unify_malformed_response(self, monkeypatch):
        from providers.unify import UnifyFetcher
        monkeypatch.setenv("UNIFY_API_KEY", "test-key")
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"not": "a list"}

        with patch("providers.unify.load_dotenv"), \
             patch.object(UnifyFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.PARSE_ERROR


# ---------------------------------------------------------------------------
# HuggingFace
# ---------------------------------------------------------------------------

class TestHuggingFaceFetcher:
    def _make(self):
        from providers.huggingface import HuggingFaceFetcher
        return HuggingFaceFetcher()

    def test_huggingface_provider_name(self):
        from providers.huggingface import HuggingFaceFetcher
        assert HuggingFaceFetcher.provider_name == "HuggingFace"

    def test_huggingface_get_api_key_returns_none(self):
        fetcher = self._make()
        assert fetcher.get_api_key() is None

    def test_huggingface_fetch_success_single_page(self):
        from providers.huggingface import HuggingFaceFetcher
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"modelId": "meta-llama/Llama-3", "pipeline_tag": "text-generation"},
            {"modelId": "openai/whisper", "pipeline_tag": "automatic-speech-recognition"},
        ]

        with patch.object(HuggingFaceFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.SUCCESS
        assert "meta-llama/Llama-3" in result.models
        assert "openai/whisper" not in result.models  # pipeline_tag filter

    def test_huggingface_post_process(self):
        fetcher = self._make()
        assert fetcher.post_process(["z", "a", "a"]) == ["a", "z"]

    def test_huggingface_empty_result(self):
        from providers.huggingface import HuggingFaceFetcher
        fetcher = self._make()
        mock_resp = MagicMock()
        mock_resp.json.return_value = []

        with patch.object(HuggingFaceFetcher, "_http_get", return_value=mock_resp):
            result = fetcher.fetch_models()

        assert result.status == FetchStatus.EMPTY


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def _reload_all_providers():
    """Reload all provider modules to re-trigger __init_subclass__ registration.

    The autouse clean_registry fixture clears the registry between tests, but
    cached modules in sys.modules won't re-fire __init_subclass__ on plain
    import. Reloading forces re-registration.
    """
    provider_module_names = [
        "providers.nvidia", "providers.groq", "providers.github_models",
        "providers.openrouter", "providers.nanogpt", "providers.apipie",
        "providers.sambanova", "providers.perplexity", "providers.togetherai",
        "providers.cohere", "providers.unify", "providers.huggingface",
        "providers.ai302", "providers.deepseek", "providers.fireworks",
        "providers.glhf", "providers.kluster", "providers.mistral",
        "providers.hyperbolic", "providers.xai",
    ]

    modules = [importlib.import_module(name) for name in provider_module_names]
    for mod in modules:
        importlib.reload(mod)

    return get_registry()


class TestRegistration:
    def test_all_20_providers_registered(self):
        """All 20 providers must be discoverable."""
        registry = _reload_all_providers()
        expected = {
            "302AI", "APIpie", "cohere", "deepseek", "Fireworks",
            "Github Models", "glhf.chat", "groq", "HuggingFace",
            "Hyperbolic", "Kluster", "Mistral", "NanoGPT", "Nvidia",
            "OpenRouter", "Perplexity", "SambaNova", "together.ai",
            "Unify", "xai",
        }
        assert set(registry.keys()) == expected, (
            f"Missing: {expected - set(registry.keys())}, "
            f"Extra: {set(registry.keys()) - expected}"
        )

    def test_registry_count(self):
        registry = _reload_all_providers()
        assert len(registry) == 20


class TestNoDuplicates:
    """Integration test: every provider's post_process produces no duplicates."""

    def test_no_duplicates_in_post_process(self):
        registry = _reload_all_providers()
        for name, cls in registry.items():
            fetcher = cls()
            # Feed duplicates to post_process
            test_input = ["model-a", "model-b", "model-a", "model-c", "model-b"]
            result = fetcher.post_process(test_input)
            # Filter out category headers (e.g., ---FREE---)
            model_ids = [m for m in result if not m.startswith("---")]
            assert len(model_ids) == len(set(model_ids)), (
                f"{name}: post_process produced duplicates: {result}"
            )

    def test_post_process_is_deterministic(self):
        registry = _reload_all_providers()
        for name, cls in registry.items():
            fetcher = cls()
            test_input = ["z-model", "a-model", "m-model", "a-model"]
            result1 = fetcher.post_process(list(test_input))
            result2 = fetcher.post_process(list(test_input))
            assert result1 == result2, (
                f"{name}: post_process is not deterministic"
            )


class TestAllProviderNames:
    """Verify each provider's provider_name matches the expected YAML name."""

    def test_provider_names_match_yaml_names(self):
        registry = _reload_all_providers()
        # These are the exact YAML endpoint names from the config files
        expected_names = {
            "302AI", "APIpie", "cohere", "deepseek", "Fireworks",
            "Github Models", "glhf.chat", "groq", "HuggingFace",
            "Hyperbolic", "Kluster", "Mistral", "NanoGPT", "Nvidia",
            "OpenRouter", "Perplexity", "SambaNova", "together.ai",
            "Unify", "xai",
        }
        for name in expected_names:
            assert name in registry, f"Provider '{name}' not registered"
            fetcher = registry[name]()
            assert fetcher.provider_name == name
