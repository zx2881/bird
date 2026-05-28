import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Landing',
    component: () => import('../views/Landing.vue')
  },
  {
    path: '/home',
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
    path: '/location/:id',
    name: 'LocationDetail',
    component: () => import('../views/LocationDetail.vue'),
    props: true
  },
  {
    path: '/semantic-search',
    name: 'SemanticSearch',
    component: () => import('../views/SemanticSearch.vue')
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
