import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/overview',
    name: 'Overview',
    component: () => import('../views/Overview.vue')
  },
  {
    path: '/categories',
    name: 'Categories',
    component: () => import('../views/Categories.vue')
  },
  {
    path: '/bird/:id',
    name: 'BirdDetail',
    component: () => import('../views/BirdDetail.vue'),
    props: true
  },
  {
    path: '/semantic-search',
    name: 'SemanticSearch',
    component: () => import('../views/SemanticSearch.vue')
  }
]

const router = createRouter({
  // 关键修改点：传入 import.meta.env.BASE_URL
  // 这会自动读取你 vite.config.js 里的 base: '/bird/'
  history: createWebHistory(import.meta.env.BASE_URL), 
  routes
})

export default router