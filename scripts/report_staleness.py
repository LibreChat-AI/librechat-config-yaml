"""Detect provider entries whose `models.default` lists haven't changed in N weeks.

A silent staleness signal for fetchers that may have silently broken
(scrapers returning a cached page, an API that started returning empty
results that the staleness gate masked, etc.). Reads line info from
ruamel.yaml's round-trip parser and asks git for the most recent commit
touching each provider's models.default block.

Exit code is always 0: this is a report, not a gate.

Usage:
    python scripts/report_staleness.py
    python scripts/report_staleness.py --weeks 6 --file librechat-env-l.yaml --json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ruamel.yaml import YAML


DEFAULT_WEEKS = 4
DEFAULT_FILE = "librechat-env-f.yaml"


def find_provider_ranges(file_path: Path) -> dict[str, tuple[int, int]]:
    """Return {provider_name: (start_line, end_line)} for each
    endpoints.custom[*].models.default block, 1-based inclusive."""
    yaml = YAML(typ="rt")
    with file_path.open("r", encoding="utf-8") as f:
        data = yaml.load(f)

    if not isinstance(data, dict):
        return {}
    endpoints = data.get("endpoints")
    if not isinstance(endpoints, dict):
        return {}
    custom = endpoints.get("custom")
    if not isinstance(custom, list):
        return {}

    ranges: dict[str, tuple[int, int]] = {}
    for entry in custom:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        models = entry.get("models")
        if not isinstance(name, str) or not isinstance(models, dict):
            continue
        default = models.get("default")
        if default is None or not hasattr(default, "lc") or len(default) == 0:
            continue
        start = default.lc.item(0)[0] + 1
        end = default.lc.item(len(default) - 1)[0] + 1
        ranges[name] = (start, end)
    return ranges


def blame_max_committer_time(repo_root: Path, rel_path: str, start: int, end: int) -> int:
    """Run `git blame --porcelain -L start,end` and return the maximum
    committer-time epoch seconds. Returns 0 on failure."""
    result = subprocess.run(
        ["git", "-C", str(repo_root), "blame", "--porcelain",
         "-L", f"{start},{end}", rel_path],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return 0
    max_t = 0
    for line in result.stdout.splitlines():
        if line.startswith("committer-time "):
            try:
                t = int(line.split(" ", 1)[1])
            except (ValueError, IndexError):
                continue
            if t > max_t:
                max_t = t
    return max_t


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weeks", type=int, default=DEFAULT_WEEKS)
    parser.add_argument("--file", type=str, default=DEFAULT_FILE)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    yaml_path = repo_root / args.file
    if not yaml_path.exists():
        print(f"missing: {yaml_path}", file=sys.stderr)
        return 0

    ranges = find_provider_ranges(yaml_path)
    if not ranges:
        print("no providers with models.default found", file=sys.stderr)
        return 0

    now = datetime.now(timezone.utc)
    threshold_epoch = int((now - timedelta(weeks=args.weeks)).timestamp())
    rel = str(yaml_path.relative_to(repo_root))

    stale: list[dict] = []
    fresh: list[str] = []

    for name, (start, end) in sorted(ranges.items()):
        max_t = blame_max_committer_time(repo_root, rel, start, end)
        if max_t == 0:
            continue
        when = datetime.fromtimestamp(max_t, tz=timezone.utc)
        days = (now - when).days
        if max_t < threshold_epoch:
            stale.append({
                "provider": name,
                "last_changed": when.isoformat(),
                "days_stale": days,
            })
        else:
            fresh.append(name)

    stale.sort(key=lambda x: x["days_stale"], reverse=True)

    report = {
        "file": args.file,
        "threshold_weeks": args.weeks,
        "generated_at": now.isoformat(),
        "stale": stale,
        "fresh": fresh,
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        if stale:
            print(f"Stale providers (no model-list change in > {args.weeks} weeks) in {args.file}:")
            for s in stale:
                print(f"  - {s['provider']}: last changed {s['last_changed']} ({s['days_stale']} days ago)")
        else:
            print(f"All {len(fresh)} providers fresh (changed within {args.weeks} weeks).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
