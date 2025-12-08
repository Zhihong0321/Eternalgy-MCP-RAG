import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import ComponentLibrary from '../views/ComponentLibrary.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/components',
    name: 'ComponentLibrary',
    component: ComponentLibrary
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
