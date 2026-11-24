from __future__ import annotations

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .base import BaseFetcher, FetchResult, FetchStatus


class CatalogEndpoint(BaseModel):
    protocol: str
    path: str
    base_url: str
    auth: str


class CatalogModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    modality: str
    endpoints: list[CatalogEndpoint] = Field(default_factory=list)


class CatalogResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    items: list[CatalogModel]


class AceDataCloudFetcher(BaseFetcher):
    """Read only public chat catalog metadata; never send a generation request."""

    provider_name = "Ace Data Cloud"
    protocol = "chat_completions"
    endpoint_path = "/v1/chat/completions"
    base_url = "https://api.acedata.cloud/v1"

    def get_api_key(self):
        # The catalog is public. Actual inference and /v1/models require a user key.
        return None

    def fetch_models(self) -> FetchResult:
        try:
            response = self._http_get("https://platform.acedata.cloud/api/v1/models/catalog/")
            catalog = CatalogResponse.model_validate(response.json())
            models = [
                item.id for item in catalog.items
                if item.modality == "chat" and item.id.strip() and any(
                    endpoint.protocol == self.protocol and endpoint.path == self.endpoint_path
                    and endpoint.base_url == self.base_url and endpoint.auth == "bearer"
                    for endpoint in item.endpoints
                )
            ]
            return FetchResult(
                provider_name=self.provider_name,
                models=models,
                status=FetchStatus.SUCCESS if models else FetchStatus.EMPTY,
                error_message=None if models else "No chat models returned",
            )
        except (ValidationError, ValueError):
            return FetchResult(self.provider_name, [], FetchStatus.PARSE_ERROR, "Invalid public model catalog")
        except httpx.HTTPStatusError as error:
            status = FetchStatus.AUTH_ERROR if error.response.status_code in (401, 403) else FetchStatus.NETWORK_ERROR
            return FetchResult(self.provider_name, [], status, "Public model catalog request failed")
        except httpx.HTTPError:
            return FetchResult(self.provider_name, [], FetchStatus.NETWORK_ERROR, "Public model catalog unavailable")

    def post_process(self, models: list[str]) -> list[str]:
        return sorted(set(models))
