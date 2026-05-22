import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  // 1. 核心路径配置：确保 GitHub Pages 能找到资源
  base: '/bird/', 

  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: '全球鸟类多样性知识探索平台',
        short_name: '鸟类知识图谱',
        description: '全球鸟类分布与生物多样性保护知识图谱',
        theme_color: '#0f766e',
        background_color: '#f4efe2',
        display: 'standalone',
        icons: [
          { src: '/favicon.svg', sizes: 'any', type: 'image/svg+xml' }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,png,svg,ico,webmanifest}'],
        globIgnores: ['**/knowledge.json', '**/data/**/*.json'],
        runtimeCaching: [
          {
            urlPattern: /\/data\/.*\.json$/,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'bird-graph-data-chunks',
              expiration: {
                maxEntries: 4000,
                maxAgeSeconds: 86400 * 30
              }
            }
          },
          {
            urlPattern: /^https:\/\/picsum\.photos\/.*/,
            handler: 'CacheFirst',
            options: { 
              cacheName: 'bird-images', 
              expiration: { maxEntries: 100, maxAgeSeconds: 86400 * 30 } 
            }
          }
        ]
      }
    })
  ],
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: ['.frp-few.com'] 
  }
})
