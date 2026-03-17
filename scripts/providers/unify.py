from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv

from .base import BaseFetcher, FetchResult, FetchStatus


class UnifyFetcher(BaseFetcher):
    """Fetch models from Unify API (API key required, plain string list format)."""

    provider_name = "Unify"

    def get_api_key(self) -> Optional[str]:
        load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
        return os.getenv("UNIFY_API_KEY")

    def fetch_models(self) -> FetchResult:
        api_key = self.get_api_key()
        if not api_key:
            return FetchResult(
                provider_name=self.provider_name,
                models=[],
                status=FetchStatus.AUTH_ERROR,
                error_message="UNIFY_API_KEY not set",
            )
        try:
            response = self._http_get(
                "https://api.unify.ai/v0/endpoints",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "accept": "application/json",
                },
            )
            data = response.json()
            if not isinstance(data, list) or not all(isinstance(s, str) for s in data):
                return FetchResult(
                    provider_name=self.provider_name,
                    models=[],
                    status=FetchStatus.PARSE_ERROR,
                    error_message="Expected list of strings, got %s" % type(data).__name__,
                )
            if not data:
                return FetchResult(
                    provider_name=self.provider_name,
                    models=[],
                    status=FetchStatus.EMPTY,
                    error_message="No models returned",
                )
            return FetchResult(
                provider_name=self.provider_name,
                models=data,
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
