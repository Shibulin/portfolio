import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// TextRoom Vue 前端构建配置
// - base:'./' → 产物用相对路径，便于 FastAPI 直接挂载 dist
// - assetsDir:'static' → 避开后端已占用的 /assets（AI 场景图路径）
export default defineConfig({
  plugins: [vue()],
  base: './',
  build: {
    outDir: 'dist',
    assetsDir: 'static',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    // 开发模式下把后端资源透传过去，前端只需跑 vite
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/assets': 'http://127.0.0.1:8000',
      '/videos': 'http://127.0.0.1:8000',
      '/scene-map.json': 'http://127.0.0.1:8000',
    },
  },
})
