from __future__ import annotations

from typing import Optional

import requests

from .base import BaseFetcher, FetchResult, FetchStatus


class NvidiaFetcher(BaseFetcher):
    """Fetch models from NVIDIA's public API (no key required)."""

    provider_name = "Nvidia"

    def get_api_key(self) -> Optional[str]:
        return None  # Public API

    def fetch_models(self) -> FetchResult:
        try:
            response = requests.get("https://integrate.api.nvidia.com/v1/models")
            response.raise_for_status()
            data = response.json()
            if "data" not in data or not isinstance(data["data"], list):
                return FetchResult(
                    provider_name=self.provider_name,
                    models=[],
                    status=FetchStatus.PARSE_ERROR,
                    error_message="Response missing 'data' key or 'data' is not a list",
                )
            models = [m["id"] for m in data["data"] if "id" in m]
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
        except requests.exceptions.HTTPError as e:
            status = (
                FetchStatus.AUTH_ERROR
                if e.response is not None and e.response.status_code in (401, 403)
                else FetchStatus.NETWORK_ERROR
            )
            return FetchResult(
                provider_name=self.provider_name,
                models=[],
                status=status,
                error_message=str(e),
            )
        except requests.exceptions.RequestException as e:
            return FetchResult(
                provider_name=self.provider_name,
                models=[],
                status=FetchStatus.NETWORK_ERROR,
                error_message=str(e),
            )

    def post_process(self, models: list[str]) -> list[str]:
        return sorted(set(models))
