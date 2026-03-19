from __future__ import annotations

from collections import defaultdict
from typing import Optional

import httpx
from pydantic import ValidationError

from .base import BaseFetcher, FetchResult, FetchStatus
from .response_models import OpenAIModelListResponse


class OpenRouterFetcher(BaseFetcher):
    """Fetch models from OpenRouter API with category grouping."""

    provider_name = "OpenRouter"

    def get_api_key(self) -> Optional[str]:
        return None  # Public API

    def fetch_models(self) -> FetchResult:
        try:
            response = self._http_get("https://openrouter.ai/api/v1/models")
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
        """Sort and group model IDs with category headers.

        Reproduces the legacy sort_and_group_ids() logic:
        1. openrouter/auto first
        2. Suffix groups: :free, :nitro, :beta, :extended (with headers)
        3. Prefix groups for no-suffix models (with headers)
        4. Small prefix groups (<=2) merged into ---OTHERS---

        Stealth models are intentionally not supported in the
        contract-based fetcher. They should be managed separately
        if needed.
        """
        ids = list(set(models))  # deduplicate

        first_model = "openrouter/auto"
        result = []

        if first_model in ids:
            ids.remove(first_model)
            result.append(first_model)

        # Group by suffix
        sorted_suffixes = [":free", ":nitro", ":beta", ":extended"]
        grouped = defaultdict(list)

        for model_id in ids:
            for suffix in sorted_suffixes:
                if model_id.endswith(suffix):
                    grouped[suffix].append(model_id)
                    break
            else:
                grouped["no_suffix"].append(model_id)

        # Sort each group
        for key in grouped:
            grouped[key].sort()

        # Group no_suffix models by prefix
        prefix_grouped = defaultdict(list)
        others = []

        for model_id in grouped["no_suffix"]:
            prefix = model_id.split("/")[0]
            prefix_grouped[prefix].append(model_id)

        # Move small groups to others
        for prefix in list(prefix_grouped.keys()):
            if len(prefix_grouped[prefix]) <= 2:
                others.extend(prefix_grouped.pop(prefix))

        prefix_grouped["others"] = sorted(others)

        # Add suffix groups with headers
        for suffix in sorted_suffixes:
            if grouped[suffix]:
                result.append(f"---{suffix[1:].upper()}---")
                result.extend(grouped[suffix])

        # Add prefix groups with headers
        for prefix in sorted(prefix_grouped.keys()):
            if prefix != "others":
                result.append(f"---{prefix.upper()}---")
                result.extend(sorted(prefix_grouped[prefix]))

        # Add others group last
        if prefix_grouped["others"]:
            result.append("---OTHERS---")
            result.extend(prefix_grouped["others"])

        return result
