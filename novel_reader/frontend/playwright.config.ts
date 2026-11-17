import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { resolve } from 'node:path'
import { defineConfig } from '@playwright/test'

const root = fileURLToPath(new URL('.', import.meta.url))

// Secrets stay local: read the untracked .env without printing its values.
try {
  const envFile = resolve(root, '../.env')
  for (const line of readFileSync(envFile, 'utf8').split(/\r?\n/)) {
    const match = line.match(/^(ADMIN_USERNAME|ADMIN_PASSWORD)=(.*)$/)
    if (match && !process.env[`E2E_${match[1]}`]) process.env[`E2E_${match[1]}`] = match[2]
  }
} catch {
  // No .env — the spec will skip login-dependent checks.
}

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 120_000,
  use: {
    baseURL: 'http://localhost:5173',
    channel: 'chrome',
    headless: true,
  },
  webServer: [
    {
      command: 'npm run dev',
      url: 'http://localhost:5173',
      reuseExistingServer: true,
      timeout: 60_000,
    },
    {
      command: '.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000',
      cwd: resolve(root, '../backend'),
      url: 'http://localhost:8000/api/novels',
      reuseExistingServer: true,
      timeout: 180_000,
    },
  ],
})
