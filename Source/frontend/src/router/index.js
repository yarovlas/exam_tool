import { createRouter, createWebHistory } from 'vue-router'
import BeoordelaarsView from '../views/BeoordelaarsView.vue'
import DashboardView from '../views/DashboardView.vue'
import ExamensView from '../views/ExamensView.vue'
import OpdrachtenView from '../views/OpdrachtenView.vue'
import StudentenView from '../views/StudentenView.vue'
import UitloggenView from '../views/UitloggenView.vue'
import InloggenView from '../views/InloggenView.vue'

const routes = [
  { path: '/', name: 'dashboard', component: DashboardView },
  { path: '/examens', name: 'examens', component: ExamensView },
  { path: '/studenten', name: 'studenten', component: StudentenView },
  { path: '/beoordelaars', name: 'beoordelaars', component: BeoordelaarsView },
  { path: '/opdrachten', name: 'opdrachten', component: OpdrachtenView },
  { path: '/uitloggen', name: 'uitloggen', component: UitloggenView },
  { path: '/inloggen', name: 'inloggen', component: InloggenView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
