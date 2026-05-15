<!-- Thanks for contributing to librechat-config-yaml. -->

## Summary

<!-- One or two sentences on what this PR changes and why. -->

## Type of change

- [ ] Provider added / removed / renamed
- [ ] Model list curated (no script change)
- [ ] Fetcher script change (`scripts/providers/*.py`)
- [ ] Pipeline / workflow change (`.github/workflows/*`)
- [ ] Schema bump / preamble change (top-level keys)
- [ ] Documentation only

## Checklist

- [ ] If a new provider was added: entry exists in **all five** `librechat-*.yaml` files (env-l, env-f, up-l, up-f, test), a fetcher exists under `scripts/providers/`, and the README's "Get an API key" table has a row.
- [ ] Tests under `scripts/tests/` pass locally (`cd scripts && pytest -q`).
- [ ] `cd scripts && npm ci && cd .. && node scripts/validate_config.mjs` passes against all changed YAML files.
- [ ] The CI `Validate YAML` workflow is green.
- [ ] No secrets, API keys, hostnames, IPs, or other deployment-specific information are present in any file.

## Related issues

<!-- Closes #..., refs #... -->
