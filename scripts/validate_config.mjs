#!/usr/bin/env node
/**
 * Validate every librechat-*.yaml against the published Zod `configSchema`
 * exported by `librechat-data-provider`. Dependabot keeps that package on
 * the latest published version; bumps automatically follow LibreChat
 * releases.
 *
 * Upstream `configSchema` uses `.strip()` (silently drops unknown keys) to
 * accommodate plugin extensions in downstream deployments. In this repo
 * the YAMLs are the canonical reference, so we apply `.strict()` at the
 * top level to catch typos like `fileStratgey:` or `intereface:`.
 *
 * One extra post-Zod check Zod doesn't cover: duplicate model IDs inside
 * a custom endpoint's `models.default`.
 *
 * Exit codes:
 *   0 - all files valid
 *   1 - one or more files failed validation
 *   2 - invocation error (missing files, etc.)
 *
 * Usage:
 *   node scripts/validate_config.mjs
 *   node scripts/validate_config.mjs librechat-env-f.yaml
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
  const targets = (argv.length
    ? argv.map(a => (isAbsolute(a) ? a : join(repoRoot, a)))
    : DEFAULT_FILES.map(f => join(repoRoot, f))
  ).filter(p => {
    if (existsSync(p)) return true;
    console.error(`missing: ${p}`);
    return false;
  });

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
  return exitCode;
}

process.exit(main(process.argv.slice(2)));
