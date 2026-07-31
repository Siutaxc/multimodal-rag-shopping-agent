import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    pool: "threads",
    setupFiles: ["./vitest.setup.ts"],
    include: ["**/*.test.{ts,tsx}"],
    coverage: {
      reporter: ["text", "json", "html"],
    },
  },
});
