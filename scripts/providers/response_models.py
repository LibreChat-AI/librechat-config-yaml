"""Pydantic v2 response models for all distinct provider API response formats.

These models validate raw JSON responses from provider APIs before model ID
extraction.  Every model uses ``extra="allow"`` so unknown fields pass through
without error -- only the fields we actually extract are declared as required.

Format coverage:
  A -- OpenAI-style  {"data": [{"id": ...}]}         (~14 providers)
  B -- Flat array    [{"id": ...}] or [{"name": ...}]  (2 providers)
  C -- Cohere        {"models": [{"name": ..., "endpoints": [...]}]}
  D -- NanoGPT       {"models": {"text": {"display": {"model": "id"}}}}
  G -- HuggingFace   [{"modelId": ..., "pipeline_tag": ...}]

Formats E (APIpie) and F (Unify) are handled by ModelEntryById and plain
list[str] respectively -- no dedicated model needed.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


# --- Format A: OpenAI-style {"data": [...]} ---


class OpenAIModelEntry(BaseModel):
    """Single model entry in an OpenAI-compatible /v1/models response."""

    model_config = ConfigDict(extra="allow")

    id: str


class OpenAIModelListResponse(BaseModel):
    """OpenAI-compatible /v1/models list response."""

    model_config = ConfigDict(extra="allow")

    data: list[OpenAIModelEntry]


# --- Format B: Flat array of objects ---


class ModelEntryById(BaseModel):
    """Model entry keyed by 'id' field (e.g. TogetherAI, APIpie)."""

    model_config = ConfigDict(extra="allow")

    id: str


class ModelEntryByName(BaseModel):
    """Model entry keyed by 'name' field (e.g. GitHub Models)."""

    model_config = ConfigDict(extra="allow")

    name: str


# --- Format C: Cohere {"models": [...]} ---


class CohereModelEntry(BaseModel):
    """Single model in Cohere's response."""

    model_config = ConfigDict(extra="allow")

    name: str
    endpoints: list[str] = []


class CohereModelListResponse(BaseModel):
    """Cohere /v1/models response."""

    model_config = ConfigDict(extra="allow")

    models: list[CohereModelEntry]


# --- Format D: NanoGPT nested ---


class NanoGPTModelInfo(BaseModel):
    """Single model info in NanoGPT's nested structure."""

    model_config = ConfigDict(extra="allow")

    model: str


class NanoGPTModelsSection(BaseModel):
    """The 'models' top-level object in NanoGPT response."""

    model_config = ConfigDict(extra="allow")

    text: dict[str, NanoGPTModelInfo]


class NanoGPTResponse(BaseModel):
    """NanoGPT /api/models response."""

    model_config = ConfigDict(extra="allow")

    models: NanoGPTModelsSection


# --- Format G: HuggingFace ---


class HuggingFaceModelEntry(BaseModel):
    """Single model in HuggingFace paginated response."""

    model_config = ConfigDict(extra="allow")

    modelId: str
    pipeline_tag: str | None = None
