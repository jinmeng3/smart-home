import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    process.env.NODE_ENV === 'production' ? null : vueDevTools(),
  ].filter(Boolean),
  build: {
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/vue') || id.includes('node_modules/pinia')) {
            return 'vue-vendor'
          }

          if (id.includes('node_modules/element-plus') || id.includes('node_modules/@element-plus')) {
            return 'ui-vendor'
          }

          if (id.includes('node_modules/echarts') || id.includes('node_modules/zrender')) {
            return 'chart-vendor'
          }

          return undefined
        },
      },
    },
  },
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/uploads': 'http://127.0.0.1:8000',
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
