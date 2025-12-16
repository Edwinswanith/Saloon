import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    watch: {
      usePolling: true, // Enable for Docker
    },
    hmr: {
      host: 'localhost',
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
