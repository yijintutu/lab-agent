import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    // 开发代理：把 /api 开头的请求交给 Vite 服务端转发到后端，浏览器不再跨域
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000', // 后端地址
        changeOrigin: true // 修改请求头中的 Host/Origin 为 target，核心配置
        // 不需要 rewrite：后端路由本身就是 /api 开头，转发时保留 /api 前缀
      },
      '/uploads': {
        target: 'http://127.0.0.1:8000', // 后端地址
        changeOrigin: true // 修改请求头中的 Host/Origin 为 target，核心配置
      }
    }
  }
})
