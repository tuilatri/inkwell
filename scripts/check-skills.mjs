#!/usr/bin/env node
/**
 * check-skills.mjs — integrity gate for the skill corpus.
 * Compares SKILL-SOURCES.md declared counts with the actual directories.
 * Exit 0 = match · exit 1 = drift (manifest must be updated).
 */
import { readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const manifest = readFileSync(path.join(root, 'SKILL-SOURCES.md'), 'utf8');

const activeDeclared = Number(manifest.match(/Active total:\s*\*\*(\d+) skill dirs\*\*/)?.[1] ?? -1);
const poolDeclared = Number(manifest.match(/pool:\s*\*\*(\d+) dirs\*\*/)?.[1] ?? -1);
const conventionsDeclared = Number(manifest.match(/Inkwell conventions \(\d+ domain skills\)\s*\|\s*(\d+)/)?.[1] ?? -1);

const dirs = (rel) => readdirSync(path.join(root, rel), { withFileTypes: true })
  .filter((entry) => entry.isDirectory()).map((entry) => entry.name);

const active = dirs('.claude/skills');
const pool = dirs('.claude/skills-disabled');
const conventions = dirs('.opencode/skills');

const checks = [
  ['active skills', activeDeclared, active.length],
  ['disabled pool', poolDeclared, pool.length],
  ['conventions skills', conventionsDeclared, conventions.length],
];

let failed = false;
for (const [label, declared, actual] of checks) {
  const ok = declared === actual;
  if (!ok) failed = true;
  console.log(`${ok ? 'PASS' : 'FAIL'} ${label}: manifest=${declared} actual=${actual}`);
}
if (failed) console.log('Update SKILL-SOURCES.md (or restore the missing skill directories).');
process.exit(failed ? 1 : 0);
