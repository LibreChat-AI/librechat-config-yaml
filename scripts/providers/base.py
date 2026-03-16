from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


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


# Module-level registry: provider_name -> fetcher class
_registry: dict[str, type[BaseFetcher]] = {}


class BaseFetcher(ABC):
    """Abstract base class for all provider fetchers."""

    # Subclasses MUST set this as a class attribute
    provider_name: str = ""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Only register concrete classes (those with a provider_name set)
        if cls.provider_name:
            _registry[cls.provider_name] = cls

    @abstractmethod
    def get_api_key(self) -> Optional[str]:
        """Return the API key for this provider, or None if not required."""
        ...

    @abstractmethod
    def fetch_models(self) -> FetchResult:
        """Fetch models from the provider and return a typed FetchResult."""
        ...

    @abstractmethod
    def post_process(self, models: list[str]) -> list[str]:
        """Post-process the model list (sort, filter, deduplicate)."""
        ...

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


def get_registry() -> dict[str, type[BaseFetcher]]:
    """Return a copy of the provider registry."""
    return dict(_registry)
