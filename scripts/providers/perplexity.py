from __future__ import annotations

import re
from typing import Optional

from .base import BaseFetcher, FetchResult, FetchStatus

_MODEL_PATTERN = re.compile(r"^sonar(-[a-z0-9]+)*$")


class PerplexityFetcher(BaseFetcher):
    """Perplexity provider with hardcoded model list and regex validation.

    No public model-listing API exists. Models sourced from:
    https://docs.perplexity.ai/guides/model-cards
    """

    provider_name = "Perplexity"

    MODELS = [
        "sonar",
        "sonar-pro",
        "sonar-reasoning-pro",
        "sonar-deep-research",
    ]

    def get_api_key(self) -> Optional[str]:
        return None  # Hardcoded list, no API call

    def fetch_models(self) -> FetchResult:
        invalid = [m for m in self.MODELS if not _MODEL_PATTERN.match(m)]
        if invalid:
            return FetchResult(
                provider_name=self.provider_name,
                models=[],
                status=FetchStatus.PARSE_ERROR,
                error_message=f"Invalid model names: {invalid}",
            )
        return FetchResult(
            provider_name=self.provider_name,
            models=list(self.MODELS),
            status=FetchStatus.SUCCESS,
        )

    def post_process(self, models: list[str]) -> list[str]:
        return sorted(set(models))
