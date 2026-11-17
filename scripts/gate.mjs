#!/usr/bin/env node
/**
 * Cross-platform gate dispatcher used by npm scripts in the root package.json.
 *   node gate.mjs node <script> [args…]   -> run a Node script from repo root
 *   node gate.mjs python <args…>          -> run pytest via the backend venv
 * Windows uses .venv/Scripts/python.exe, POSIX uses .venv/bin/python (or `python3`).
 */
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const [kind, ...args] = process.argv.slice(2);

let cmd;
let cwd = root;
if (kind === 'node') {
  cmd = process.execPath;
} else if (kind === 'python') {
  const venv = process.platform === 'win32'
    ? path.join(root, 'novel_reader/backend/.venv/Scripts/python.exe')
    : path.join(root, 'novel_reader/backend/.venv/bin/python');
  cmd = existsSync(venv) ? venv : (process.platform === 'win32' ? 'python' : 'python3');
  cwd = path.join(root, 'novel_reader/backend');
} else {
  console.error(`Unknown gate kind: ${kind}`);
  process.exit(1);
}

const child = spawnSync(cmd, args, { cwd, stdio: 'inherit', shell: false });
process.exit(child.status ?? 1);
