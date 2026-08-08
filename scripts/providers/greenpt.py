from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv
from pydantic import ValidationError

from .base import BaseFetcher, FetchResult, FetchStatus
from .response_models import OpenAIModelListResponse


NON_CHAT_MODELS = {
    "bge-multilingual-gemma2",
    "green-embedding",
    "green-l",
    "green-l-raw",
    "green-r",
    "green-r-raw",
    "green-rerank",
    "green-s",
    "green-s-pro",
}
FEATURED_MODELS = ("glm-5.2", "kimi-k2.7-code")


class GreenPTFetcher(BaseFetcher):
    """Fetch chat models from GreenPT's OpenAI-compatible API."""

    provider_name = "GreenPT"

    def get_api_key(self) -> Optional[str]:
        load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
        return os.getenv("GREENPT_API_KEY")

    def fetch_models(self) -> FetchResult:
        api_key = self.get_api_key()
        if not api_key:
            return FetchResult(
                provider_name=self.provider_name,
                models=[],
                status=FetchStatus.AUTH_ERROR,
                error_message="GREENPT_API_KEY not set",
            )

        try:
            response = self._http_get(
                "https://api.greenpt.ai/v1/models",
                headers={
                    "accept": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
            )
            try:
                validated = OpenAIModelListResponse.model_validate(response.json())
            except ValidationError as error:
                return FetchResult(
                    provider_name=self.provider_name,
                    models=[],
                    status=FetchStatus.PARSE_ERROR,
                    error_message=str(error),
                )

            models = [
                entry.id
                for entry in validated.data
                if entry.id not in NON_CHAT_MODELS
                and "embedding" not in entry.id.lower()
                and "rerank" not in entry.id.lower()
            ]
            if not models:
                return FetchResult(
                    provider_name=self.provider_name,
                    models=[],
                    status=FetchStatus.EMPTY,
                    error_message="No chat models returned after filtering",
                )
            return FetchResult(
                provider_name=self.provider_name,
                models=models,
                status=FetchStatus.SUCCESS,
            )
        except httpx.HTTPStatusError as error:
            status = (
                FetchStatus.AUTH_ERROR
                if error.response.status_code in (401, 403)
                else FetchStatus.NETWORK_ERROR
            )
            return FetchResult(
                provider_name=self.provider_name,
                models=[],
                status=status,
                error_message=str(error),
            )
        except httpx.HTTPError as error:
            return FetchResult(
                provider_name=self.provider_name,
                models=[],
                status=FetchStatus.NETWORK_ERROR,
                error_message=str(error),
            )

    def post_process(self, models: list[str]) -> list[str]:
        unique_models = set(models)
        featured = [model for model in FEATURED_MODELS if model in unique_models]
        return featured + sorted(unique_models - set(featured))
