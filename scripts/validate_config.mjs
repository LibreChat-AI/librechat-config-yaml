#!/usr/bin/env node
/**
 * validate_config.mjs — schema validator for librechat-*.yaml files.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * WHY THIS EXISTS
 * ─────────────────────────────────────────────────────────────────────────────
 * This repo ships five user-facing YAML configs (env-l, env-f, up-l, up-f,
 * test) that downstream LibreChat deployments pin via CONFIG_PATH. A typo
 * (`fileStratgey:` instead of `fileStrategy:`) or a structurally invalid
 * endpoint silently breaks every deployment that points at the bad file.
 *
 * Hand-rolling allowlists / enum checks in Python was the previous approach
 * and required us to chase every `configSchema` change in LibreChat by hand.
 * Instead we import the *actual* Zod `configSchema` from the published
 * `librechat-data-provider` npm package, which is the same schema LibreChat
 * itself uses to parse `librechat.yaml` at startup. Dependabot opens a PR
 * whenever a new version is published, so schema drift is detected
 * automatically rather than manually.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * STRICT MODE
 * ─────────────────────────────────────────────────────────────────────────────
 * Upstream `configSchema` is built with `.strip()` semantics: unknown top-
 * level keys are silently dropped so plugin extensions in downstream
 * deployments don't blow up. In *this* repo the YAMLs are the canonical
 * reference everyone else pins, so we override with `.strict()` at the top
 * level. That promotes a typo from "silently ignored" to "CI failure with
 * a clear message," which is what we want here.
 *
 * Note: `.strict()` is applied only at the top level — nested objects keep
 * their upstream-defined strictness. This is enough to catch the common
 * misspelling class without rejecting future-but-not-yet-published nested
 * keys that may appear in a fresher LibreChat than our pinned data-provider.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * EXTRA CHECK: DUPLICATE MODEL IDS
 * ─────────────────────────────────────────────────────────────────────────────
 * Zod treats `models.default` as `string[]`, which means `["foo", "foo"]`
 * passes schema validation but is almost always a bug introduced by a
 * misbehaving fetcher or a bad merge. `findDuplicateModelIds` walks every
 * `endpoints.custom[*].models.default` list and reports any repeated id.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * EXIT CODES
 * ─────────────────────────────────────────────────────────────────────────────
 *   0 — every targeted file parsed and validated cleanly.
 *   1 — at least one file failed schema or duplicate-model validation.
 *   2 — invocation error: a path passed on the command line does not exist,
 *       or no files were resolvable. Distinct from 1 so CI / wrappers can
 *       tell "your config is broken" apart from "you typed the wrong path."
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * USAGE
 * ─────────────────────────────────────────────────────────────────────────────
 *   # validate all five canonical files
 *   node scripts/validate_config.mjs
 *
 *   # validate one or more specific files
 *   node scripts/validate_config.mjs librechat-env-f.yaml librechat-test.yaml
 */

import { configSchema } from 'librechat-data-provider';
import yaml from 'js-yaml';
import { readFileSync, existsSync } from 'node:fs';
import { resolve, basename, dirname, join, isAbsolute } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(__dirname, '..');

const DEFAULT_FILES = [
  'librechat-env-l.yaml',
  'librechat-env-f.yaml',
  'librechat-up-l.yaml',
  'librechat-up-f.yaml',
  'librechat-test.yaml',
];

const strictSchema = configSchema.strict();

function findDuplicateModelIds(data) {
  const issues = [];
  const custom = data?.endpoints?.custom;
  if (!Array.isArray(custom)) return issues;
  for (let i = 0; i < custom.length; i++) {
    const entry = custom[i];
    const list = entry?.models?.default;
    if (!Array.isArray(list)) continue;
    const seen = new Set();
    const dupes = new Set();
    for (const m of list) {
      if (typeof m !== 'string') continue;
      if (seen.has(m)) dupes.add(m);
      seen.add(m);
    }
    for (const d of dupes) {
      issues.push({
        path: `endpoints.custom[${i}].models.default`,
        message: `duplicate model id ${JSON.stringify(d)} in ${entry?.name ?? '<unnamed>'}`,
      });
    }
  }
  return issues;
}

function validateFile(filePath) {
  let raw;
  try {
    raw = readFileSync(filePath, 'utf8');
  } catch (e) {
    return { ok: false, errors: [{ path: '<file>', message: `read failed: ${e.message}` }] };
  }

  let data;
  try {
    data = yaml.load(raw);
  } catch (e) {
    return { ok: false, errors: [{ path: '<yaml>', message: `parse error: ${e.message}` }] };
  }

  const result = strictSchema.safeParse(data);
  const errors = [];

  if (!result.success) {
    for (const issue of result.error.issues) {
      errors.push({
        path: issue.path.length ? issue.path.join('.') : '<root>',
        message: `${issue.message} [${issue.code}]`,
      });
    }
  }

  errors.push(...findDuplicateModelIds(data));

  return { ok: errors.length === 0, errors };
}

function main(argv) {
  const requested = argv.length
    ? argv.map(a => (isAbsolute(a) ? a : join(repoRoot, a)))
    : DEFAULT_FILES.map(f => join(repoRoot, f));

  const targets = [];
  const missing = [];
  for (const p of requested) {
    if (existsSync(p)) {
      targets.push(p);
    } else {
      missing.push(p);
      console.error(`missing: ${p}`);
    }
  }

  if (targets.length === 0) {
    console.error('no files to validate');
    return 2;
  }

  let exitCode = 0;
  for (const path of targets) {
    const name = basename(path);
    const result = validateFile(path);
    if (result.ok) {
      console.log(`OK   ${name}`);
    } else {
      console.log(`FAIL ${name}`);
      for (const err of result.errors) {
        console.log(`     ${err.path}: ${err.message}`);
      }
      exitCode = 1;
    }
  }

  // If the caller named files we couldn't resolve, surface that as an
  // invocation error (exit 2) — but only if every targeted file passed,
  // since a real validation failure is more important to report.
  if (missing.length > 0 && exitCode === 0) {
    return 2;
  }
  return exitCode;
}

process.exit(main(process.argv.slice(2)));
