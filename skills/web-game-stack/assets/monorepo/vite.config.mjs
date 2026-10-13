import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

export default defineConfig({
  plugins: [react()],
  publicDir: path.resolve('vendor/als-web/public'),
  server: { host: '0.0.0.0', port: 5173 },
})
