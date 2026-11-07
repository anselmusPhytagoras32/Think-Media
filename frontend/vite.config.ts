import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { env } from "node:process";
const apiTarget = env.THINKMEDIA_API_TARGET || "http://127.0.0.1:8000";
export default defineConfig({
  plugins: [react()],
  server: {
    watch: { usePolling: true, interval: 500 },
    proxy: {
      "/api": apiTarget,
      "/health": apiTarget,
    },
  },
  preview: { host: "127.0.0.1" },
});
