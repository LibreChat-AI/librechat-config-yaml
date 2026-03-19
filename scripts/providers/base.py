from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
    before_sleep_log,
)


class FetchStatus(Enum):
    SUCCESS = "success"
    AUTH_ERROR = "auth_error"
    NETWORK_ERROR = "network_error"
    PARSE_ERROR = "parse_error"
    EMPTY = "empty"


@dataclass
class FetchResult:
    provider_name: str
    models: list[str]
    status: FetchStatus
    error_message: Optional[str] = None
    model_count: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        self.model_count = len(self.models)


def _is_transient_error(exc: BaseException) -> bool:
    """Return True for transient HTTP errors worth retrying."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (429, 500, 502, 503, 504)
    return isinstance(exc, (httpx.ConnectError, httpx.TimeoutException))


# Module-level registry: provider_name -> fetcher class
_registry: dict[str, type[BaseFetcher]] = {}


class BaseFetcher(ABC):
    """Abstract base class for all provider fetchers."""

    # Subclasses MUST set this as a class attribute
    provider_name: str = ""

    @property
    def logger(self) -> logging.LoggerAdapter:
        """Logger that auto-includes provider name in log records."""
        base_logger = logging.getLogger(f"fetcher.{self.provider_name}")
        return logging.LoggerAdapter(base_logger, {"provider": self.provider_name})

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Only register concrete classes (those with a provider_name set)
        if cls.provider_name:
            _registry[cls.provider_name] = cls

    @abstractmethod
    def get_api_key(self) -> Optional[str]:
        """Return the API key for this provider, or None if not required."""
        pass

    @abstractmethod
    def fetch_models(self) -> FetchResult:
        """Fetch models from the provider and return a typed FetchResult."""
        pass

    @abstractmethod
    def post_process(self, models: list[str]) -> list[str]:
        """Post-process the model list (sort, filter, deduplicate)."""
        pass

    def run(self) -> FetchResult:
        """Template method: orchestrates fetch + post_process with error handling."""
        try:
            result = self.fetch_models()
            if result.status == FetchStatus.SUCCESS and result.models:
                result.models = self.post_process(result.models)
                result.model_count = len(result.models)
            return result
        except Exception as e:
            return FetchResult(
                provider_name=self.provider_name,
                models=[],
                status=FetchStatus.NETWORK_ERROR,
                error_message=str(e),
            )

    def _http_get(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float = 30.0,
        follow_redirects: bool = True,
    ) -> httpx.Response:
        """GET request with automatic retry on transient errors."""

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential_jitter(initial=2, max=30),
            retry=retry_if_exception(_is_transient_error),
            before_sleep=before_sleep_log(
                logging.getLogger(f"fetcher.{self.provider_name}"),
                logging.WARNING,
            ),
            reraise=True,
        )
        def _do_get() -> httpx.Response:
            response = httpx.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout,
                follow_redirects=follow_redirects,
            )
            response.raise_for_status()
            return response

        return _do_get()


def get_registry() -> dict[str, type[BaseFetcher]]:
    """Return a copy of the provider registry."""
    return dict(_registry)
