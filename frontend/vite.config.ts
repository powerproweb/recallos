import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    // Output the production build directly into the desktop static directory
    outDir: "../desktop/static",
    emptyOutDir: true,
  },
  server: {
    // Dev server proxies API calls to the FastAPI backend
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
