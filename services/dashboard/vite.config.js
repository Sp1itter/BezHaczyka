import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// PUNKT POLACZENIA: dokad dev-serwer przekazuje /api i /socket.io.
// Teraz mock Node (:4000). Po podpieciu bazy: adres services/api (np. http://127.0.0.1:8000).
const target = process.env.API_URL || "http://127.0.0.1:4000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: Number(process.env.WEB_PORT || 5180),
    proxy: {
      "/api": { target, changeOrigin: true },
      "/socket.io": { target, ws: true, changeOrigin: true },
    },
  },
});
