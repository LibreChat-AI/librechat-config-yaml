from __future__ import annotations

import time
from typing import Optional

import httpx
from pydantic import ValidationError

from .base import BaseFetcher, FetchResult, FetchStatus
from .response_models import HuggingFaceModelEntry


class HuggingFaceFetcher(BaseFetcher):
    """Fetch models from HuggingFace API (public, paginated, text-generation filter)."""

    provider_name = "HuggingFace"

    def get_api_key(self) -> Optional[str]:
        return None

    def fetch_models(self) -> FetchResult:
        all_models: list[str] = []
        for page in range(1, 6):
            try:
                response = self._http_get(
                    "https://huggingface.co/api/models",
                    params={
                        "filter": "conversational",
                        "sort": "likes",
                        "direction": "-1",
                        "limit": 100,
                        "full": "true",
                        "page": page,
                    },
                )
                data = response.json()
                if not isinstance(data, list):
                    break
                entries = [HuggingFaceModelEntry.model_validate(e) for e in data]
                page_models = [
                    e.modelId for e in entries
                    if e.pipeline_tag == "text-generation"
                ]
                if not page_models:
                    break
                all_models.extend(page_models)
                if len(data) < 100:
                    break
                if page < 5:
                    time.sleep(1)
            except (httpx.HTTPError, ValidationError) as exc:
                if not all_models:
                    return FetchResult(
                        provider_name=self.provider_name,
                        models=[],
                        status=FetchStatus.NETWORK_ERROR,
                        error_message=str(exc),
                    )
                break
        if not all_models:
            return FetchResult(
                provider_name=self.provider_name,
                models=[],
                status=FetchStatus.EMPTY,
                error_message="No text-generation models found",
            )
        return FetchResult(
            provider_name=self.provider_name,
            models=all_models,
            status=FetchStatus.SUCCESS,
        )

    def post_process(self, models: list[str]) -> list[str]:
        return sorted(set(models))
