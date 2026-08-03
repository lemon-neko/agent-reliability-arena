import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  use: { baseURL: "http://127.0.0.1:4173", trace: "retain-on-failure" },
  webServer: {
    command: "VITE_DEMO_MODE=true pnpm vite --mode demo --host 127.0.0.1 --port 4173",
    url: "http://127.0.0.1:4173/agent-reliability-arena/",
    reuseExistingServer: true,
  },
});
