from unittest.mock import Mock, patch

import httpx
import pytest

from providers.acedata import AceDataCloudFetcher
from providers.base import FetchStatus


def test_public_catalog_filters_media_and_deduplicates():
    fetcher = AceDataCloudFetcher()
    response = Mock()
    response.json.return_value = {"items": [
        {"id": "chat-a", "modality": "chat"},
        {"id": "image-a", "modality": "image"},
        {"id": "chat-a", "modality": "chat"},
    ]}
    with patch.object(fetcher, "_http_get", return_value=response) as get:
        result = fetcher.run()
    assert result.status == FetchStatus.SUCCESS
    assert result.models == ["chat-a"]
    get.assert_called_once_with("https://platform.acedata.cloud/api/v1/models/catalog/")
    assert fetcher.get_api_key() is None


@pytest.mark.parametrize("data,status", [
    ({"items": []}, FetchStatus.EMPTY),
    ({"items": [{"id": "image", "modality": "image"}]}, FetchStatus.EMPTY),
    ({"items": [{"id": "invalid"}]}, FetchStatus.PARSE_ERROR),
    ({"data": []}, FetchStatus.PARSE_ERROR),
])
def test_no_invalid_or_media_only_models(data, status):
    response = Mock()
    response.json.return_value = data
    with patch.object(AceDataCloudFetcher, "_http_get", return_value=response):
        assert AceDataCloudFetcher().run().status == status


@pytest.mark.parametrize("code,expected", [(401, FetchStatus.AUTH_ERROR), (500, FetchStatus.NETWORK_ERROR)])
def test_request_failure_status(code, expected):
    request = httpx.Request("GET", "https://platform.acedata.cloud/api/v1/models/catalog/")
    response = httpx.Response(code, request=request)
    with patch.object(AceDataCloudFetcher, "_http_get", side_effect=httpx.HTTPStatusError("failed", request=request, response=response)):
        result = AceDataCloudFetcher().run()
    assert result.status == expected
    assert result.models == []
