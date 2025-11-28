import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/personas': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
      '/chat': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
      '/export': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
      '/memories': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
      '/memories-live': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
      '/switch-model': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
    },
  },
});
