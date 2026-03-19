from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from .base import BaseFetcher, FetchResult, FetchStatus, get_registry


def discover_providers() -> dict[str, type[BaseFetcher]]:
    """Import all provider modules in this package, triggering registration."""
    package_dir = Path(__file__).parent
    for finder, name, ispkg in pkgutil.iter_modules([str(package_dir)]):
        if name != "base":
            importlib.import_module(f".{name}", package=__package__)
    return get_registry()


__all__ = [
    "BaseFetcher",
    "FetchResult",
    "FetchStatus",
    "discover_providers",
    "get_registry",
]
