import { createRouter, createWebHistory } from 'vue-router'

import ApprovalsPage from '../pages/ApprovalsPage.vue'
import AttendancePage from '../pages/AttendancePage.vue'
import CloudPage from '../pages/CloudPage.vue'
import DashboardPage from '../pages/DashboardPage.vue'
import ExpensesPage from '../pages/ExpensesPage.vue'
import HqPanelPage from '../pages/HqPanelPage.vue'
import LandingPage from '../pages/LandingPage.vue'
import LoginPage from '../pages/LoginPage.vue'
import ReportsPage from '../pages/ReportsPage.vue'
import RequestsPage from '../pages/RequestsPage.vue'
import SettingsPage from '../pages/SettingsPage.vue'
import SupportPage from '../pages/SupportPage.vue'
import UsersPage from '../pages/UsersPage.vue'
import WalletPage from '../pages/WalletPage.vue'

const routes = [
  { path: '/', name: 'landing', component: LandingPage, meta: { public: true, publicCanvas: true, landing: true } },
  { path: '/login', name: 'login', component: LoginPage, meta: { public: true, publicCanvas: true } },
  { path: '/dashboard', name: 'dashboard', component: DashboardPage, meta: { fullCanvas: true } },
  { path: '/requests', name: 'requests', component: RequestsPage, meta: { fullCanvas: true } },
  { path: '/requests/new', redirect: '/requests' },
  { path: '/expenses', name: 'expenses', component: ExpensesPage, meta: { fullCanvas: true } },
  { path: '/wallet', name: 'wallet', component: WalletPage, meta: { fullCanvas: true } },
  { path: '/attendance', name: 'attendance', component: AttendancePage, meta: { fullCanvas: true, feature: 'attendance' } },
  { path: '/attendance/:token', name: 'public-attendance', component: AttendancePage, meta: { public: true, publicCanvas: true } },
  { path: '/cloud', name: 'cloud', component: CloudPage, meta: { fullCanvas: true, feature: 'cloud_storage' } },
  { path: '/support', name: 'support', component: SupportPage, meta: { fullCanvas: true } },
  { path: '/hq', name: 'hq', component: HqPanelPage, meta: { fullCanvas: true } },
  { path: '/approvals', name: 'approvals', component: ApprovalsPage, meta: { fullCanvas: true } },
  { path: '/reports', name: 'reports', component: ReportsPage, meta: { fullCanvas: true } },
  { path: '/users', name: 'users', component: UsersPage, meta: { fullCanvas: true } },
  { path: '/settings', name: 'settings', component: SettingsPage, meta: { fullCanvas: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to) {
    if (to.hash) {
      return { el: to.hash, behavior: 'smooth', top: 96 }
    }
    return { top: 0 }
  },
})

router.beforeEach((to) => {
  const token = localStorage.getItem('workflow-hub-token')
  if (!to.meta.public && !token) return '/'
  if (token && (to.path === '/login' || to.name === 'landing')) {
    return '/dashboard'
  }
  return true
})

export default router
