import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests/webview',
  timeout: 60_000,
  use: {
    baseURL: 'http://127.0.0.1:5173',
    viewport: { width: 1280, height: 720 }
  },
  webServer: {
    command: 'npm run dev:webview:serve',
    url: 'http://127.0.0.1:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000
  }
})
