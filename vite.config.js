import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    // Avoid Windows excluded port ranges that commonly cover Vite's default 5173.
    port: 4173,
    // Allow the FRP root domain and any generated subdomain such as demo.frp-few.com.
    allowedHosts: ['.frp-few.com']
  }
})
