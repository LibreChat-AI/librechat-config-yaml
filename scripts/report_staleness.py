"""report_staleness.py — flag provider model lists that haven't moved in N weeks.

────────────────────────────────────────────────────────────────────────────────
WHY THIS EXISTS
────────────────────────────────────────────────────────────────────────────────
The daily `update_models.py` workflow has an existing safety gate that aborts
when a fetcher returns < 50 % of the previously known model count. That gate
catches *sudden* breakage well, but it's blind to a different failure mode:

  - A scraper-based fetcher (Perplexity, SambaNova, NanoGPT, …) starts hitting
    a cached page and quietly returns the same list week after week.
  - A vendor's `/models` API silently drops new families but keeps returning
    the old ones, so the count never falls.
  - A fetcher's API key expires into a "free tier" subset and the response
    stays plausibly large.

In all three cases the model list is wrong but the daily pipeline is happy.
This script surfaces those by reporting providers whose `models.default` block
hasn't seen a commit in `--weeks` (default 4).

It is a *report*, not a gate: exit code is always 0. The weekly workflow
turns the JSON output into a tracking issue (see staleness-report.yml).

────────────────────────────────────────────────────────────────────────────────
HOW IT WORKS
────────────────────────────────────────────────────────────────────────────────
1. Round-trip-parse the YAML with ruamel.yaml. ruamel preserves source line
   numbers on every node via `.lc.item(i)`, which PyYAML does not. We use
   that to find the exact `(start_line, end_line)` range of each provider's
   `endpoints.custom[*].models.default` list.
2. For each range, run `git blame --porcelain -L start,end <file>` and take
   the maximum `committer-time` epoch across the blamed lines. That's the
   most recent commit that touched the model list.
3. Compare against the threshold `now - weeks` and bucket each provider as
   `stale`, `fresh`, or `blame_failed` (the last bucket exists so partial
   reports look partial — see "blame failures" below).

────────────────────────────────────────────────────────────────────────────────
SINGLE-FILE SCOPE
────────────────────────────────────────────────────────────────────────────────
By default we only inspect `librechat-env-f.yaml`. The five YAML files in
this repo are kept structurally equivalent by `update_models.py`, so the
staleness signal for any one of them generalizes to all of them. Running
across all five would just produce five copies of the same list.

If a future provider lands in only some of the files (intentionally), bump
`--file` on the workflow or run the script multiple times locally.

────────────────────────────────────────────────────────────────────────────────
BLAME FAILURES
────────────────────────────────────────────────────────────────────────────────
`git blame` can fail (shallow clone, file moved across a rename boundary,
git binary missing). Earlier versions silently `continue`d on failure, which
made a partial report look complete. We now record those providers in a
`blame_failed` bucket and emit a stderr warning so the report consumer can
tell coverage was incomplete.

────────────────────────────────────────────────────────────────────────────────
USAGE
────────────────────────────────────────────────────────────────────────────────
    # default: human-readable, 4-week threshold, env-f file
    python scripts/report_staleness.py

    # JSON output (workflow consumes this)
    python scripts/report_staleness.py --json

    # different threshold / different file
    python scripts/report_staleness.py --weeks 6 --file librechat-env-l.yaml
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
    endpoints.custom[*].models.default block, 1-based inclusive.

    Uses ruamel's round-trip parser so that every loaded sequence node
    carries `.lc.item(i)` line/column metadata. Without that we'd have no
    way to ask git blame about the right line range.
    """
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
    committer-time epoch seconds across the blamed lines.

    Returns 0 on any failure (non-zero exit, missing git, parse error). The
    caller treats 0 as "blame failed" rather than "epoch zero" — no commit
    in this repo has a 1970 timestamp.
    """
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
    parser.add_argument("--weeks", type=int, default=DEFAULT_WEEKS,
                        help=f"Stale threshold in weeks (default {DEFAULT_WEEKS})")
    parser.add_argument("--file", type=str, default=DEFAULT_FILE,
                        help=f"YAML file to inspect (default {DEFAULT_FILE})")
    parser.add_argument("--json", action="store_true",
                        help="Emit machine-readable JSON instead of human text")
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
    blame_failed: list[str] = []

    for name, (start, end) in sorted(ranges.items()):
        max_t = blame_max_committer_time(repo_root, rel, start, end)
        if max_t == 0:
            # Distinct from "old" — git blame returned no usable data.
            # Surface it instead of silently dropping the provider, so a
            # broken blame setup doesn't disguise itself as 100% fresh.
            blame_failed.append(name)
            print(f"warning: git blame failed for provider {name!r} "
                  f"(lines {start}-{end} of {rel})", file=sys.stderr)
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
        "blame_failed": blame_failed,
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
        if blame_failed:
            print(f"\nBlame failed for {len(blame_failed)} provider(s): "
                  f"{', '.join(blame_failed)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
