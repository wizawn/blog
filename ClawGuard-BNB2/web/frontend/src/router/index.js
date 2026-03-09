import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import Trading from '@/views/Trading.vue'
import Strategy from '@/views/Strategy.vue'
import Analysis from '@/views/Analysis.vue'
import Risk from '@/views/Risk.vue'
import Settings from '@/views/Settings.vue'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/trading',
    name: 'Trading',
    component: Trading
  },
  {
    path: '/strategy',
    name: 'Strategy',
    component: Strategy
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: Analysis
  },
  {
    path: '/risk',
    name: 'Risk',
    component: Risk
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
