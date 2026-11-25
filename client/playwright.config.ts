import { defineConfig } from '@playwright/test'

// The tests drive the real stack (nginx -> API -> Postgres -> Redis) started by docker compose; see scripts/test.sh.
export default defineConfig({
  testDir: './e2e',
  timeout: 120_000,
  expect: { timeout: 5_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  outputDir: 'test-results',
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:8080',
    ignoreHTTPSErrors: true,
    headless: !process.env.HEADED, // HEADED=1 opens real browser windows so you can watch the two sessions
    trace: 'on', // a trace for every run, so there is always one to inspect (test-results/**/trace.zip)
  },
})
