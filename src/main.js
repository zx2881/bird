import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'leaflet/dist/leaflet.css'
import router from './router/index.js'
import App from './App.vue'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(ElementPlus)
app.use(router)
app.mount('#app')
