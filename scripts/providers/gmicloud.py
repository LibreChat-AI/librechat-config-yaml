from __future__ import annotations

import os
import re
from pathlib import Path

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

from .base import BaseFetcher, FetchResult, FetchStatus
from .response_models import OpenAIModelEntry


class GMIModelEntry(OpenAIModelEntry):
    id: str = ""
    object: str = "model"


class GMIModelListResponse(BaseModel):
    data: list[GMIModelEntry]


# The inference catalog can include embedding or generation models alongside chat.
NON_CHAT_MODEL = re.compile(
    r"(?:^|[/_.-])(?:3d|asr|chatterbox|clip|embeddings?|flux|image|imagegen|kling|music|ocr|"
    r"rerank(?:er)?|seedance|seedream|sora|speech|transcribe|transcription|tts|veo|video|whisper)"
    r"(?=$|[/_.-]|\d)",
    re.IGNORECASE,
)


class GMICloudFetcher(BaseFetcher):
    """Fetch chat models from the GMI Cloud Inference Engine."""

    provider_name = "GMI Cloud"

    def get_api_key(self) -> str | None:
        load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
        return os.getenv("GMI_API_KEY")

    def fetch_models(self) -> FetchResult:
        api_key = self.get_api_key()
        if not api_key:
            return FetchResult(self.provider_name, [], FetchStatus.AUTH_ERROR, "GMI_API_KEY not set")

        try:
            response = self._http_get(
                "https://api.gmi-serving.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
            )
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            status = FetchStatus.AUTH_ERROR if code in (401, 403) else FetchStatus.NETWORK_ERROR
            return FetchResult(self.provider_name, [], status, f"HTTP {code}")
        except httpx.HTTPError as exc:
            return FetchResult(self.provider_name, [], FetchStatus.NETWORK_ERROR, type(exc).__name__)

        try:
            catalog = GMIModelListResponse.model_validate_json(response.content)
        except ValidationError:
            return FetchResult(self.provider_name, [], FetchStatus.PARSE_ERROR, "Invalid model list response")

        models = []
        for entry in catalog.data:
            model_id = entry.id.strip()
            # Older catalog rows put the model ID in "object".
            if not model_id or model_id == "model":
                model_id = entry.object.strip()
            if model_id and model_id != "model" and not NON_CHAT_MODEL.search(model_id):
                models.append(model_id)

        if not models:
            return FetchResult(self.provider_name, [], FetchStatus.EMPTY, "No chat models returned")
        return FetchResult(self.provider_name, models, FetchStatus.SUCCESS)

    def post_process(self, models: list[str]) -> list[str]:
        return sorted(set(models))
