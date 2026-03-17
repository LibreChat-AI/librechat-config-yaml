"""Tests for pydantic response model validation across all provider API formats."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from providers.response_models import (
    CohereModelListResponse,
    HuggingFaceModelEntry,
    ModelEntryById,
    ModelEntryByName,
    NanoGPTResponse,
    OpenAIModelListResponse,
)


class TestOpenAIModelListResponse:
    def test_valid_response(self):
        data = {"data": [{"id": "model-a"}, {"id": "model-b"}], "object": "list"}
        result = OpenAIModelListResponse.model_validate(data)
        assert len(result.data) == 2
        assert result.data[0].id == "model-a"

    def test_extra_fields_allowed(self):
        data = {"data": [{"id": "m", "owned_by": "org", "created": 123}], "object": "list"}
        result = OpenAIModelListResponse.model_validate(data)
        assert result.data[0].id == "m"

    def test_missing_data_key(self):
        with pytest.raises(ValidationError) as exc_info:
            OpenAIModelListResponse.model_validate({"models": []})
        assert "data" in str(exc_info.value)

    def test_data_not_a_list(self):
        with pytest.raises(ValidationError):
            OpenAIModelListResponse.model_validate({"data": "not-a-list"})

    def test_entry_missing_id(self):
        with pytest.raises(ValidationError) as exc_info:
            OpenAIModelListResponse.model_validate({"data": [{"name": "no-id"}]})
        assert "id" in str(exc_info.value)

    def test_empty_data_list_valid(self):
        """Empty data list is structurally valid -- emptiness check is the fetcher's job."""
        result = OpenAIModelListResponse.model_validate({"data": []})
        assert result.data == []


class TestModelEntryById:
    def test_valid(self):
        result = ModelEntryById.model_validate({"id": "x", "extra": True})
        assert result.id == "x"

    def test_missing_id(self):
        with pytest.raises(ValidationError):
            ModelEntryById.model_validate({"name": "x"})


class TestModelEntryByName:
    def test_valid(self):
        result = ModelEntryByName.model_validate({"name": "x", "extra": True})
        assert result.name == "x"

    def test_missing_name(self):
        with pytest.raises(ValidationError) as exc_info:
            ModelEntryByName.model_validate({"id": "x"})
        assert "name" in str(exc_info.value)


class TestCohereModelListResponse:
    def test_valid(self):
        data = {"models": [{"name": "cmd-r", "endpoints": ["chat"]}]}
        result = CohereModelListResponse.model_validate(data)
        assert result.models[0].name == "cmd-r"
        assert result.models[0].endpoints == ["chat"]

    def test_missing_models_key(self):
        with pytest.raises(ValidationError):
            CohereModelListResponse.model_validate({"data": []})

    def test_entry_missing_name(self):
        with pytest.raises(ValidationError):
            CohereModelListResponse.model_validate({"models": [{"id": "no-name"}]})

    def test_default_endpoints(self):
        data = {"models": [{"name": "m"}]}
        result = CohereModelListResponse.model_validate(data)
        assert result.models[0].endpoints == []


class TestNanoGPTResponse:
    def test_valid(self):
        data = {"models": {"text": {"gpt-4": {"model": "gpt-4-actual"}}}}
        result = NanoGPTResponse.model_validate(data)
        assert result.models.text["gpt-4"].model == "gpt-4-actual"

    def test_missing_models(self):
        with pytest.raises(ValidationError):
            NanoGPTResponse.model_validate({"data": {}})

    def test_missing_text(self):
        with pytest.raises(ValidationError):
            NanoGPTResponse.model_validate({"models": {"image": {}}})


class TestHuggingFaceModelEntry:
    def test_valid(self):
        data = {"modelId": "org/model", "pipeline_tag": "text-generation"}
        result = HuggingFaceModelEntry.model_validate(data)
        assert result.modelId == "org/model"
        assert result.pipeline_tag == "text-generation"

    def test_optional_pipeline_tag(self):
        result = HuggingFaceModelEntry.model_validate({"modelId": "org/model"})
        assert result.pipeline_tag is None

    def test_missing_model_id(self):
        with pytest.raises(ValidationError):
            HuggingFaceModelEntry.model_validate({"name": "x"})


class TestErrorMessages:
    def test_error_names_missing_field(self):
        with pytest.raises(ValidationError) as exc_info:
            OpenAIModelListResponse.model_validate({"wrong": 1})
        assert "data" in str(exc_info.value)

    def test_error_names_type_mismatch(self):
        with pytest.raises(ValidationError) as exc_info:
            OpenAIModelListResponse.model_validate({"data": "string"})
        assert "list" in str(exc_info.value)
