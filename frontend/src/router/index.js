import { createRouter, createWebHistory } from 'vue-router'

import { applyRouteSeo } from '../utils/seo'

const ApprovalsPage = () => import('../pages/ApprovalsPage.vue')
const AttendancePage = () => import('../pages/AttendancePage.vue')
const ChatPage = () => import('../pages/ChatPage.vue')
const CloudPage = () => import('../pages/CloudPage.vue')
const DashboardPage = () => import('../pages/DashboardPage.vue')
const ExpensesPage = () => import('../pages/ExpensesPage.vue')
const HqPanelPage = () => import('../pages/HqPanelPage.vue')
const LoginPage = () => import('../pages/LoginPage.vue')
const ReportsPage = () => import('../pages/ReportsPage.vue')
const RequestsPage = () => import('../pages/RequestsPage.vue')
const SettingsPage = () => import('../pages/SettingsPage.vue')
const SupportPage = () => import('../pages/SupportPage.vue')
const UsersPage = () => import('../pages/UsersPage.vue')
const WalletPage = () => import('../pages/WalletPage.vue')

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'login', component: LoginPage, meta: { public: true, publicCanvas: true, seo: { title: 'ورود به کارنومند', description: 'ورود به سامانه مدیریت گردش‌کار کارنومند.', robots: 'noindex, nofollow', canonicalPath: '/login' } } },
  { path: '/dashboard', name: 'dashboard', component: DashboardPage, meta: { fullCanvas: true } },
  { path: '/requests', name: 'requests', component: RequestsPage, meta: { fullCanvas: true } },
  { path: '/requests/new', redirect: '/requests' },
  { path: '/expenses', name: 'expenses', component: ExpensesPage, meta: { fullCanvas: true } },
  { path: '/wallet', name: 'wallet', component: WalletPage, meta: { fullCanvas: true } },
  { path: '/attendance', name: 'attendance', component: AttendancePage, meta: { fullCanvas: true, feature: 'attendance' } },
  { path: '/attendance/:token', name: 'public-attendance', component: AttendancePage, meta: { public: true, publicCanvas: true, seo: { robots: 'noindex, nofollow', canonicalPath: false } } },
  { path: '/cloud', name: 'cloud', component: CloudPage, meta: { fullCanvas: true, feature: 'cloud_storage' } },
  { path: '/support', name: 'support', component: SupportPage, meta: { fullCanvas: true } },
  { path: '/chat', name: 'chat', component: ChatPage, meta: { fullCanvas: true } },
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
  if (!to.meta.public && !token) return '/login'
  if (token && to.path === '/login') {
    return '/dashboard'
  }
  return true
})

router.afterEach((to) => {
  applyRouteSeo(to)
})

export default router
