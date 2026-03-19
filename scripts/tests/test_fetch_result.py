"""Tests for FetchResult dataclass and FetchStatus enum (REQ-F2)."""
from __future__ import annotations

from datetime import datetime, timezone

from providers.base import FetchResult, FetchStatus


class TestFetchStatusEnum:
    def test_status_enum_values(self):
        """FetchStatus has exactly 5 members with correct string values."""
        assert len(FetchStatus) == 5
        assert FetchStatus.SUCCESS.value == "success"
        assert FetchStatus.AUTH_ERROR.value == "auth_error"
        assert FetchStatus.NETWORK_ERROR.value == "network_error"
        assert FetchStatus.PARSE_ERROR.value == "parse_error"
        assert FetchStatus.EMPTY.value == "empty"


class TestFetchResult:
    def test_fields(self):
        """FetchResult has all required fields with correct types."""
        result = FetchResult(
            provider_name="test",
            models=["a", "b"],
            status=FetchStatus.SUCCESS,
        )
        assert isinstance(result.provider_name, str)
        assert isinstance(result.models, list)
        assert isinstance(result.status, FetchStatus)
        assert isinstance(result.error_message, type(None))
        assert isinstance(result.model_count, int)
        assert isinstance(result.timestamp, datetime)

    def test_model_count_auto(self):
        """model_count is auto-populated from len(models) via __post_init__."""
        result = FetchResult(
            provider_name="x",
            models=["a", "b", "c"],
            status=FetchStatus.SUCCESS,
        )
        assert result.model_count == 3

    def test_model_count_empty(self):
        """model_count is 0 when models list is empty."""
        result = FetchResult(
            provider_name="x",
            models=[],
            status=FetchStatus.EMPTY,
        )
        assert result.model_count == 0

    def test_timestamp_auto(self):
        """FetchResult timestamp is auto-populated with UTC timezone."""
        result = FetchResult(
            provider_name="x",
            models=[],
            status=FetchStatus.EMPTY,
        )
        assert result.timestamp.tzinfo is not None
        assert result.timestamp.tzinfo == timezone.utc

    def test_error_message_default_none(self):
        """FetchResult without error_message has error_message=None."""
        result = FetchResult(
            provider_name="x",
            models=[],
            status=FetchStatus.EMPTY,
        )
        assert result.error_message is None
