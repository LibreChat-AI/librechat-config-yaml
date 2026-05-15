"""Structural validation for librechat-*.yaml files.

Run on every PR via .github/workflows/validate-yaml.yml. Catches schema drift
without requiring a Node toolchain or the published librechat-data-provider
npm package. Validates structure against the shape declared in LibreChat's
configSchema (packages/data-provider/src/config.ts on main); fields not
covered here will still parse cleanly but won't be guarded.

Exit codes:
    0 - all files valid
    1 - one or more files failed validation
    2 - invocation error (file not found, etc.)

Usage:
    python scripts/validate_yaml.py
    python scripts/validate_yaml.py librechat-env-f.yaml
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError


EXPECTED_VERSION = "1.3.11"

FILE_STRATEGY_VALUES = {"local", "s3", "firebase", "azure_blob", "cloudfront"}
IMAGE_OUTPUT_TYPES = {"png", "webp", "jpeg", "jpg"}

# Mirror of configSchema top-level keys (packages/data-provider/src/config.ts).
ALLOWED_TOP_LEVEL = {
    "version", "cache", "ocr", "webSearch", "memory", "summarization",
    "secureImageLinks", "imageOutputType", "includedTools", "filteredTools",
    "mcpServers", "mcpSettings", "interface", "turnstile", "fileStrategy",
    "fileStrategies", "cloudfront", "actions", "registration", "balance",
    "transactions", "speech", "rateLimits", "fileConfig", "modelSpecs",
    "endpoints",
}

ALLOWED_RATE_LIMIT_KEYS = {"fileUploads", "conversationsImport", "tts", "stt"}
ALLOWED_RATE_LIMIT_FIELDS = {
    "ipMax", "ipWindowInMinutes", "userMax", "userWindowInMinutes",
}

ALLOWED_INTERFACE_KEYS = {
    "modelSelect", "parameters", "multiConvo", "bookmarks", "memories",
    "presets", "fileSearch", "fileCitations", "webSearch", "runCode",
    "autoSubmitFromUrl", "temporaryChat", "temporaryChatRetention",
    "prompts", "agents", "skills", "remoteAgents", "customWelcome",
    "mcpServers", "peoplePicker", "marketplace", "termsOfService",
    "privacyPolicy",
}

ALLOWED_MEMORY_KEYS = {
    "disabled", "validKeys", "tokenLimit", "charLimit", "personalize",
    "messageWindowSize", "agent",
}

REQUIRED_CUSTOM_ENDPOINT_KEYS = {"name", "apiKey", "baseURL", "models"}


class Issue:
    def __init__(self, severity: str, path: str, msg: str) -> None:
        self.severity = severity
        self.path = path
        self.msg = msg

    def __str__(self) -> str:
        return f"  [{self.severity}] {self.path}: {self.msg}"


def _check_known_keys(obj: dict, allowed: set, where: str, issues: list[Issue]) -> None:
    for key in obj.keys():
        if key not in allowed:
            issues.append(Issue("error", f"{where}.{key}", "unknown key"))


def _validate_rate_limits(obj: Any, issues: list[Issue]) -> None:
    if not isinstance(obj, dict):
        issues.append(Issue("error", "rateLimits", "must be a mapping"))
        return
    _check_known_keys(obj, ALLOWED_RATE_LIMIT_KEYS, "rateLimits", issues)
    for category, body in obj.items():
        where = f"rateLimits.{category}"
        if not isinstance(body, dict):
            issues.append(Issue("error", where, "must be a mapping"))
            continue
        _check_known_keys(body, ALLOWED_RATE_LIMIT_FIELDS, where, issues)
        for k, v in body.items():
            if not isinstance(v, int) or v < 0:
                issues.append(Issue("error", f"{where}.{k}", "must be a non-negative integer"))


def _validate_interface(obj: Any, issues: list[Issue]) -> None:
    if not isinstance(obj, dict):
        issues.append(Issue("error", "interface", "must be a mapping"))
        return
    _check_known_keys(obj, ALLOWED_INTERFACE_KEYS, "interface", issues)


def _validate_memory(obj: Any, issues: list[Issue]) -> None:
    if not isinstance(obj, dict):
        issues.append(Issue("error", "memory", "must be a mapping"))
        return
    _check_known_keys(obj, ALLOWED_MEMORY_KEYS, "memory", issues)


def _validate_custom_endpoint(entry: Any, idx: int, issues: list[Issue]) -> None:
    where = f"endpoints.custom[{idx}]"
    if not isinstance(entry, dict):
        issues.append(Issue("error", where, "must be a mapping"))
        return
    missing = REQUIRED_CUSTOM_ENDPOINT_KEYS - set(entry.keys())
    if missing:
        issues.append(Issue("error", where, f"missing required keys: {sorted(missing)}"))

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        issues.append(Issue("error", f"{where}.name", "must be a non-empty string"))

    models = entry.get("models")
    if isinstance(models, dict):
        default = models.get("default")
        if default is not None and not isinstance(default, list):
            issues.append(Issue("error", f"{where}.models.default", "must be a list"))
        elif isinstance(default, list):
            seen = set()
            for m in default:
                if not isinstance(m, str):
                    issues.append(Issue("error", f"{where}.models.default", "non-string entry"))
                    continue
                if m in seen:
                    issues.append(Issue("error", f"{where}.models.default", f"duplicate model id {m!r}"))
                seen.add(m)


def _validate_endpoints(obj: Any, issues: list[Issue]) -> None:
    if not isinstance(obj, dict):
        issues.append(Issue("error", "endpoints", "must be a mapping"))
        return
    custom = obj.get("custom")
    if custom is not None:
        if not isinstance(custom, list):
            issues.append(Issue("error", "endpoints.custom", "must be a list"))
        else:
            for i, entry in enumerate(custom):
                _validate_custom_endpoint(entry, i, issues)


def validate_file(path: Path) -> list[Issue]:
    issues: list[Issue] = []

    try:
        yaml = YAML(typ="safe")
        with path.open("r", encoding="utf-8") as f:
            data = yaml.load(f)
    except YAMLError as exc:
        issues.append(Issue("error", str(path), f"YAML parse error: {exc}"))
        return issues
    except OSError as exc:
        issues.append(Issue("error", str(path), f"could not read: {exc}"))
        return issues

    if not isinstance(data, dict):
        issues.append(Issue("error", str(path), "root must be a mapping"))
        return issues

    _check_known_keys(data, ALLOWED_TOP_LEVEL, "<root>", issues)

    version = data.get("version")
    if version is None:
        issues.append(Issue("error", "version", "required"))
    elif not isinstance(version, str):
        issues.append(Issue("error", "version", "must be a string"))
    elif version != EXPECTED_VERSION:
        issues.append(Issue("warning", "version", f"is {version!r}; expected {EXPECTED_VERSION!r}"))

    if "cache" in data and not isinstance(data["cache"], bool):
        issues.append(Issue("error", "cache", "must be a boolean"))

    if "fileStrategy" in data:
        fs = data["fileStrategy"]
        if isinstance(fs, str):
            if fs not in FILE_STRATEGY_VALUES:
                issues.append(Issue("error", "fileStrategy", f"must be one of {sorted(FILE_STRATEGY_VALUES)}"))
        elif not isinstance(fs, dict):
            issues.append(Issue("error", "fileStrategy", "must be a string or mapping"))

    if "imageOutputType" in data:
        iot = data["imageOutputType"]
        if not isinstance(iot, str) or iot not in IMAGE_OUTPUT_TYPES:
            issues.append(Issue("error", "imageOutputType", f"must be one of {sorted(IMAGE_OUTPUT_TYPES)}"))

    if "rateLimits" in data:
        _validate_rate_limits(data["rateLimits"], issues)
    if "interface" in data:
        _validate_interface(data["interface"], issues)
    if "memory" in data:
        _validate_memory(data["memory"], issues)
    if "endpoints" in data:
        _validate_endpoints(data["endpoints"], issues)
    else:
        issues.append(Issue("error", "endpoints", "required"))

    return issues


def main(argv: list[str]) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    if argv:
        targets = [Path(a) if Path(a).is_absolute() else repo_root / a for a in argv]
    else:
        targets = sorted(repo_root.glob("librechat-*.yaml"))

    if not targets:
        print("no files matched", file=sys.stderr)
        return 2

    exit_code = 0
    for path in targets:
        if not path.exists():
            print(f"missing: {path}", file=sys.stderr)
            exit_code = max(exit_code, 2)
            continue

        issues = validate_file(path)
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]

        if not issues:
            print(f"OK  {path.name}")
            continue

        marker = "FAIL" if errors else "WARN"
        print(f"{marker} {path.name}")
        for issue in issues:
            print(issue)
        if errors:
            exit_code = max(exit_code, 1)

    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
