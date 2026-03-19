from __future__ import annotations

from typing import Optional

from .base import BaseFetcher, FetchResult, FetchStatus


class SambaNova(BaseFetcher):
    """SambaNova provider with hardcoded model list from official docs.

    No public model-listing API exists. Models sourced from:
    https://docs.sambanova.ai/docs/en/models/sambacloud-models
    """

    # TODO: Switch to https://api.sambanova.ai/v1/models when endpoint becomes available

    provider_name = "SambaNova"

    MODELS = [
        "DeepSeek-R1",
        "DeepSeek-R1-Distill-Llama-70B",
        "DeepSeek-V3-0324",
        "Llama-3.2-11B-Vision-Instruct",
        "Llama-3.2-90B-Vision-Instruct",
        "Llama-4-Maverick-17B-128E-Instruct",
        "Llama-4-Scout-17B-16E-Instruct",
        "Meta-Llama-3.1-405B-Instruct",
        "Meta-Llama-3.1-8B-Instruct",
        "Meta-Llama-3.3-70B-Instruct",
        "QwQ-32B",
        "Qwen2.5-72B-Instruct",
        "Qwen2.5-Coder-32B-Instruct",
    ]

    def get_api_key(self) -> Optional[str]:
        return None  # Hardcoded list, no API call

    def fetch_models(self) -> FetchResult:
        invalid = [m for m in self.MODELS if not isinstance(m, str) or not m.strip()]
        if invalid:
            return FetchResult(
                provider_name=self.provider_name,
                models=[],
                status=FetchStatus.PARSE_ERROR,
                error_message=f"Invalid model entries: {invalid}",
            )
        return FetchResult(
            provider_name=self.provider_name,
            models=list(self.MODELS),
            status=FetchStatus.SUCCESS,
        )

    def post_process(self, models: list[str]) -> list[str]:
        return sorted(set(models))
