"""Tests for BaseFetcher._http_get() retry behavior (REQ-P4, REQ-P5)."""
from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest


def _make_response(status_code: int = 200, json_data: dict | None = None) -> httpx.Response:
    """Create a real httpx.Response with the given status code."""
    response = httpx.Response(
        status_code=status_code,
        request=httpx.Request("GET", "https://example.com/api"),
        json=json_data or {},
    )
    return response


def _make_status_error(status_code: int) -> httpx.HTTPStatusError:
    """Create an HTTPStatusError with the given status code."""
    response = _make_response(status_code)
    return httpx.HTTPStatusError(
        message=f"HTTP {status_code}",
        request=httpx.Request("GET", "https://example.com/api"),
        response=response,
    )


class TestHttpGetRetry:
    """Test retry behavior of BaseFetcher._http_get()."""

    def test_retry_on_429(self, concrete_fetcher_class):
        """_http_get retries on 429 Too Many Requests and succeeds on 2nd attempt."""
        fetcher = concrete_fetcher_class()
        ok_response = _make_response(200)

        with patch("providers.base.httpx.get") as mock_get, \
             patch("tenacity.nap.time.sleep"):
            mock_get.side_effect = [_make_status_error(429), ok_response]
            result = fetcher._http_get("https://example.com/api")
            assert result.status_code == 200
            assert mock_get.call_count == 2

    def test_retry_on_5xx(self, concrete_fetcher_class):
        """_http_get retries on 500/502/503/504 and succeeds on 2nd attempt."""
        fetcher = concrete_fetcher_class()

        for code in (500, 502, 503, 504):
            ok_response = _make_response(200)
            with patch("providers.base.httpx.get") as mock_get, \
                 patch("tenacity.nap.time.sleep"):
                mock_get.side_effect = [_make_status_error(code), ok_response]
                result = fetcher._http_get("https://example.com/api")
                assert result.status_code == 200
                assert mock_get.call_count == 2, f"Expected 2 calls for {code}, got {mock_get.call_count}"

    def test_retry_on_timeout(self, concrete_fetcher_class):
        """_http_get retries on TimeoutException and succeeds on 2nd attempt."""
        fetcher = concrete_fetcher_class()
        ok_response = _make_response(200)

        with patch("providers.base.httpx.get") as mock_get, \
             patch("tenacity.nap.time.sleep"):
            mock_get.side_effect = [httpx.TimeoutException("timed out"), ok_response]
            result = fetcher._http_get("https://example.com/api")
            assert result.status_code == 200
            assert mock_get.call_count == 2

    def test_retry_on_connect_error(self, concrete_fetcher_class):
        """_http_get retries on ConnectError and succeeds on 2nd attempt."""
        fetcher = concrete_fetcher_class()
        ok_response = _make_response(200)

        with patch("providers.base.httpx.get") as mock_get, \
             patch("tenacity.nap.time.sleep"):
            mock_get.side_effect = [httpx.ConnectError("connection refused"), ok_response]
            result = fetcher._http_get("https://example.com/api")
            assert result.status_code == 200
            assert mock_get.call_count == 2

    def test_stops_after_3_attempts(self, concrete_fetcher_class):
        """_http_get raises the original exception after 3 failed attempts."""
        fetcher = concrete_fetcher_class()

        with patch("providers.base.httpx.get") as mock_get, \
             patch("tenacity.nap.time.sleep"):
            mock_get.side_effect = [
                _make_status_error(500),
                _make_status_error(500),
                _make_status_error(500),
            ]
            with pytest.raises(httpx.HTTPStatusError):
                fetcher._http_get("https://example.com/api")
            assert mock_get.call_count == 3

    def test_no_retry_on_auth_error(self, concrete_fetcher_class):
        """_http_get does NOT retry on 401 or 403 -- raises immediately."""
        fetcher = concrete_fetcher_class()

        for code in (401, 403):
            with patch("providers.base.httpx.get") as mock_get, \
                 patch("tenacity.nap.time.sleep"):
                mock_get.side_effect = _make_status_error(code)
                with pytest.raises(httpx.HTTPStatusError):
                    fetcher._http_get("https://example.com/api")
                assert mock_get.call_count == 1, f"Expected 1 call for {code}, got {mock_get.call_count}"

    def test_no_retry_on_404(self, concrete_fetcher_class):
        """_http_get does NOT retry on 404 -- raises immediately."""
        fetcher = concrete_fetcher_class()

        with patch("providers.base.httpx.get") as mock_get, \
             patch("tenacity.nap.time.sleep"):
            mock_get.side_effect = _make_status_error(404)
            with pytest.raises(httpx.HTTPStatusError):
                fetcher._http_get("https://example.com/api")
            assert mock_get.call_count == 1

    def test_follow_redirects(self, concrete_fetcher_class):
        """_http_get passes follow_redirects=True to httpx.get by default."""
        fetcher = concrete_fetcher_class()
        ok_response = _make_response(200)

        with patch("providers.base.httpx.get", return_value=ok_response) as mock_get:
            fetcher._http_get("https://example.com/api")
            _, kwargs = mock_get.call_args
            assert kwargs["follow_redirects"] is True

    def test_default_timeout(self, concrete_fetcher_class):
        """_http_get passes timeout=30.0 to httpx.get by default."""
        fetcher = concrete_fetcher_class()
        ok_response = _make_response(200)

        with patch("providers.base.httpx.get", return_value=ok_response) as mock_get:
            fetcher._http_get("https://example.com/api")
            _, kwargs = mock_get.call_args
            assert kwargs["timeout"] == 30.0

    def test_custom_headers(self, concrete_fetcher_class):
        """_http_get passes headers dict to httpx.get."""
        fetcher = concrete_fetcher_class()
        ok_response = _make_response(200)
        headers = {"Authorization": "Bearer token123"}

        with patch("providers.base.httpx.get", return_value=ok_response) as mock_get:
            fetcher._http_get("https://example.com/api", headers=headers)
            _, kwargs = mock_get.call_args
            assert kwargs["headers"] == headers

    def test_successful_request(self, concrete_fetcher_class):
        """_http_get returns httpx.Response on success."""
        fetcher = concrete_fetcher_class()
        ok_response = _make_response(200)

        with patch("providers.base.httpx.get", return_value=ok_response) as mock_get:
            result = fetcher._http_get("https://example.com/api")
            assert isinstance(result, httpx.Response)
            assert result.status_code == 200
            mock_get.assert_called_once()
