from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv
from pydantic import ValidationError

from .base import BaseFetcher, FetchResult, FetchStatus
from .response_models import OpenAIModelListResponse


class GLHFFetcher(BaseFetcher):
    """Fetch models from GLHF API (API key required)."""

    provider_name = "glhf.chat"

    def get_api_key(self) -> Optional[str]:
        load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
        return os.getenv("GLHF_API_KEY")

    def fetch_models(self) -> FetchResult:
        api_key = self.get_api_key()
        if not api_key:
            return FetchResult(
                provider_name=self.provider_name,
                models=[],
                status=FetchStatus.AUTH_ERROR,
                error_message="GLHF_API_KEY not set",
            )
        try:
            response = self._http_get(
                "https://glhf.chat/api/openai/v1/models",
                headers={
                    "accept": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
            )
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
