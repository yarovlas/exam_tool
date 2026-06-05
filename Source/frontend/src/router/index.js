import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../services/authStore'

const routes = [
  { path: '/', name: 'dashboard', component: () => import('../views/DashboardView.vue') },
  { path: '/examens', name: 'examens', component: () => import('../views/ExamensView.vue') },
  { path: '/studenten', name: 'studenten', component: () => import('../views/StudentenView.vue') },
  { path: '/beoordelaars', name: 'beoordelaars', component: () => import('../views/BeoordelaarsView.vue') },
  { path: '/opdrachten', name: 'opdrachten', component: () => import('../views/OpdrachtenView.vue') },
  { path: '/wachtwoord', name: 'wachtwoord', component: () => import('../views/WachtwoordView.vue') },
  { path: '/uitloggen', name: 'uitloggen', component: () => import('../views/UitloggenView.vue') },
  { path: '/inloggen', name: 'inloggen', component: () => import('../views/InloggenView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const publicRoutes = ['inloggen']

router.beforeEach((to, from, next) => {
  const { isAuthenticated } = useAuthStore()

  if (publicRoutes.includes(to.name) && isAuthenticated.value) {
    return next('/')
  }

  if (!publicRoutes.includes(to.name) && !isAuthenticated.value) {
    return next({ name: 'inloggen', query: { redirect: to.fullPath } })
  }

  next()
})

export default router
