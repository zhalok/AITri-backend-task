import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  // In dev the Vite server proxies the API to FastAPI. In production FastAPI serves the build itself.
  server: { proxy: { '/api': 'http://localhost:8000' } },
})
