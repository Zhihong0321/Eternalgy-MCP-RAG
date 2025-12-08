import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import ComponentLibrary from '../views/ComponentLibrary.vue'
import Agents from '../views/Agents.vue'
import Chat from '../views/Chat.vue'
import Mcps from '../views/Mcps.vue'
import Settings from '../views/Settings.vue'
import Tester from '../views/Tester.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/agents',
    name: 'Agents',
    component: Agents
  },
  {
    path: '/mcps',
    name: 'Mcps',
    component: Mcps
  },
  {
    path: '/chat/:agentId?',
    name: 'Chat',
    component: Chat
  },
  {
    path: '/tester/:agentId?',
    name: 'Tester',
    component: Tester,
    meta: { bare: true }
  },
  {
    path: '/components',
    name: 'ComponentLibrary',
    component: ComponentLibrary
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
