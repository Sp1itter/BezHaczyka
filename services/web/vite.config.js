import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev: front na :5173, API na :8000. /api i /ws ida przez proxy, wiec kod frontu
// uzywa tych samych sciezek co za nginx w docker-compose.
const API = process.env.API_URL || "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: API, changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, "") },
      "/ws": { target: API.replace(/^http/, "ws"), ws: true },
    },
  },
});
