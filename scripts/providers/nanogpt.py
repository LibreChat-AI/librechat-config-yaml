from __future__ import annotations

from typing import Optional

import httpx
from pydantic import ValidationError

from .base import BaseFetcher, FetchResult, FetchStatus
from .response_models import OpenAIModelListResponse


class NanoGPTFetcher(BaseFetcher):
    """Fetch models from NanoGPT's OpenAI-compatible /api/v1/models endpoint."""

    provider_name = "NanoGPT"

    def get_api_key(self) -> Optional[str]:
        return None  # Public API

    def fetch_models(self) -> FetchResult:
        try:
            response = self._http_get("https://nano-gpt.com/api/v1/models")
            data = response.json()
            try:
                validated = OpenAIModelListResponse.model_validate(data)
            except ValidationError as e:
                return FetchResult(
                    provider_name=self.provider_name,
                    models=[],
                    status=FetchStatus.PARSE_ERROR,
                    error_message=str(e),
                )
            models = [entry.id for entry in validated.data]
            if not models:
                return FetchResult(
                    provider_name=self.provider_name,
                    models=[],
                    status=FetchStatus.EMPTY,
                    error_message="No models returned",
                )
            return FetchResult(
                provider_name=self.provider_name,
                models=models,
                status=FetchStatus.SUCCESS,
            )
        except httpx.HTTPStatusError as e:
            status = (
                FetchStatus.AUTH_ERROR
                if e.response.status_code in (401, 403)
                else FetchStatus.NETWORK_ERROR
            )
            return FetchResult(
                provider_name=self.provider_name,
                models=[],
                status=status,
                error_message=str(e),
            )
        except httpx.HTTPError as e:
            return FetchResult(
                provider_name=self.provider_name,
                models=[],
                status=FetchStatus.NETWORK_ERROR,
                error_message=str(e),
            )

    def post_process(self, models: list[str]) -> list[str]:
        return sorted(set(models))
