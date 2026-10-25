import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base: './' makes every built asset path RELATIVE instead of absolute (/assets/...).
// GitHub Pages project sites serve from a sub-path like https://user.github.io/repo/,
// so relative paths are required for the CSS/JS/JSON to load there and locally.
//
// Two pages: index.html is the replay demo (video + phone), rider.html is the standalone
// rider web app (no video).
export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        rider: resolve(__dirname, 'rider.html'),
      },
    },
  },
})
