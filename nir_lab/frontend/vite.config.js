import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE || '/',
  // Proxy API calls to the FastAPI backend during development
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  build: {
    outDir: '../backend/static',   // build output goes directly into backend/static/
    emptyOutDir: true,
  },
})
