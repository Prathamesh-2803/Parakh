import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Helper to bypass API proxy for HTML navigation requests (SPA reloads)
const bypassHtml = (req) => {
  if (req.method === 'GET' && req.headers.accept && req.headers.accept.includes('text/html')) {
    return '/index.html';
  }
};

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      '/chat': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        bypass: bypassHtml,
      },
      '/recommend': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        bypass: bypassHtml,
      },
      '/verify': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        bypass: bypassHtml,
      },
      '/feedback': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/scan': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    }
  }
})
