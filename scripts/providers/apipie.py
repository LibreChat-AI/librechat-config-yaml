from __future__ import annotations

from typing import Optional

import httpx
from pydantic import ValidationError

from .base import BaseFetcher, FetchResult, FetchStatus
from .response_models import ModelEntryById, OpenAIModelListResponse


class APIpieFetcher(BaseFetcher):
    """Fetch models from APIpie's /v1/models endpoint."""

    provider_name = "APIpie"

    def get_api_key(self) -> Optional[str]:
        return None  # No API key required

    def fetch_models(self) -> FetchResult:
        models = self._try_single_request()
        if models is not None:
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

        # Fallback: 3 filtered requests (legacy approach on /v1/models)
        models = self._try_filtered_requests()
        if not models:
            return FetchResult(
                provider_name=self.provider_name,
                models=[],
                status=FetchStatus.EMPTY,
                error_message="No models returned from any request",
            )
        return FetchResult(
            provider_name=self.provider_name,
            models=models,
            status=FetchStatus.SUCCESS,
        )

    def _try_single_request(self) -> list[str] | None:
        """Try the single /v1/models endpoint. Return model list or None on failure."""
        try:
            response = self._http_get(
                "https://apipie.ai/v1/models",
                headers={"Accept": "application/json"},
            )
            data = response.json()

            # OpenAI format: {"data": [{"id": ...}]}
            if isinstance(data, dict) and "data" in data:
                try:
                    validated = OpenAIModelListResponse.model_validate(data)
                    return [entry.id for entry in validated.data]
                except ValidationError:
                    return None

            # Flat list: [{"id": ...}]
            if isinstance(data, list):
                try:
                    entries = [ModelEntryById.model_validate(e) for e in data]
                    return [e.id for e in entries]
                except ValidationError:
                    return None

        except httpx.HTTPError:
            return None

        return None

    def _try_filtered_requests(self) -> list[str]:
        """Fallback: 3 filtered requests to /v1/models with type params."""
        all_models: set[str] = set()
        for type_param in ["free", "vision", "llm"]:
            try:
                resp = self._http_get(
                    "https://apipie.ai/v1/models",
                    headers={"Accept": "application/json"},
                    params={"type": type_param},
                )
                page_data = resp.json()
                if isinstance(page_data, dict) and "data" in page_data:
                    for entry in page_data["data"]:
                        if isinstance(entry, dict) and "id" in entry:
                            all_models.add(entry["id"])
                elif isinstance(page_data, list):
                    for entry in page_data:
                        if isinstance(entry, dict) and "id" in entry:
                            all_models.add(str(entry["id"]))
            except httpx.HTTPError:
                continue
        return list(all_models)

    def post_process(self, models: list[str]) -> list[str]:
        free = sorted(m for m in set(models) if m.startswith("free/"))
        other = sorted(m for m in set(models) if not m.startswith("free/"))
        result: list[str] = []
        if free:
            result.append("---FREE---")
            result.extend(free)
        result.extend(other)
        return result
