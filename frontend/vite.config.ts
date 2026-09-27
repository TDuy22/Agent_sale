import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In dev, /api and /health are proxied to the FastAPI backend,
// so the browser talks to a single origin.
const BACKEND_URL = "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": BACKEND_URL,
      "/health": BACKEND_URL,
    },
  },
});
