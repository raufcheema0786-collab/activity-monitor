import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // This app is loaded from a local file:// path by pywebview, not served
  // from a web root -- absolute asset paths (Vite's default) resolve
  // against the filesystem root under file:// and fail to load, leaving a
  // blank window. Relative paths make the built output work regardless of
  // where it's loaded from.
  base: './',
})
