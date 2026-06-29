import { defineConfig, devices } from '@playwright/test'

const backendPython =
  process.platform === 'win32'
    ? 'backend\\.venv\\Scripts\\python.exe'
    : 'python'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html', { open: 'never' }], ['list']],
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: `${backendPython} -m uvicorn backend.main:app --port 8000`,
      cwd: '.',
      url: 'http://localhost:8000/api/health',
      reuseExistingServer: !process.env.CI,
      env: { INFERENCE_MODE: 'demo' },
    },
    {
      command: 'npm run dev',
      cwd: 'frontend',
      url: 'http://localhost:5173',
      reuseExistingServer: !process.env.CI,
    },
  ],
})
