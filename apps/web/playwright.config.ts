import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  use: {
    baseURL: "http://127.0.0.1:4175",
    trace: "retain-on-failure",
    channel: (process.env.PLAYWRIGHT_CHANNEL ??
      (process.platform === "darwin" ? "chrome" : undefined)) as "chrome" | undefined,
  },
  webServer: {
    command: "VITE_DEMO_MODE=true pnpm exec vite --mode demo --host 127.0.0.1 --port 4175 --strictPort",
    url: "http://127.0.0.1:4175/agent-reliability-arena/",
    reuseExistingServer: false,
  },
});
