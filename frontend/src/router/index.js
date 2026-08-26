import { createRouter, createWebHistory } from 'vue-router'

import { applyRouteSeo } from '../utils/seo'
import { useWorkflowHub } from '../stores/workflowHub'

// Eager load landing so `/` never flashes empty or falls through while chunk loads.
import LandingPage from '../pages/LandingPage.vue'

const ArchivePage = () => import('../pages/ArchivePage.vue')
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
const TaskingPage = () => import('../pages/TaskingPage.vue')
const UsersPage = () => import('../pages/UsersPage.vue')
const WalletPage = () => import('../pages/WalletPage.vue')

function isPublicPath(path = '') {
  return path === '/' || path === '/login' || path.startsWith('/attendance/')
}

const routes = [
  {
    path: '/',
    name: 'landing',
    component: LandingPage,
    meta: {
      public: true,
      publicCanvas: true,
      landing: true,
      seo: {
        title: 'کارنومند | سامانه مدیریت گردش‌کار سازمانی',
        description: 'کارنومند، سامانه مدیریت گردش‌کار سازمانی برای ثبت و پیگیری درخواست‌ها، هزینه‌ها، تأیید اسناد و گزارش‌ها.',
        robots: 'index, follow',
        canonicalPath: '/',
      },
    },
  },
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
    meta: {
      public: true,
      publicCanvas: true,
      seo: {
        title: 'ورود به کارنومند',
        description: 'ورود به سامانه کارنومند.',
        robots: 'noindex, nofollow',
        canonicalPath: '/login',
      },
    },
  },
  { path: '/dashboard', name: 'dashboard', component: DashboardPage, meta: { fullCanvas: true } },
  { path: '/tasking', name: 'tasking', component: TaskingPage, meta: { fullCanvas: true } },
  { path: '/requests', name: 'requests', component: RequestsPage, meta: { fullCanvas: true } },
  { path: '/requests/new', redirect: '/requests' },
  { path: '/expenses', name: 'expenses', component: ExpensesPage, meta: { fullCanvas: true } },
  { path: '/wallet', name: 'wallet', component: WalletPage, meta: { fullCanvas: true } },
  { path: '/attendance', name: 'attendance', component: AttendancePage, meta: { fullCanvas: true, feature: 'attendance' } },
  {
    path: '/attendance/:token',
    name: 'public-attendance',
    component: AttendancePage,
    meta: { public: true, publicCanvas: true, seo: { robots: 'noindex, nofollow', canonicalPath: false } },
  },
  { path: '/archive', name: 'archive', component: ArchivePage, meta: { fullCanvas: true } },
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

  // Landing and other public pages must never be bounced away for guests.
  if (to.meta.public || to.meta.landing || isPublicPath(to.path)) {
    // Only skip the login screen when already authenticated — keep landing sticky.
    if (token && to.path === '/login') return '/dashboard'
    return true
  }

  if (!token) return '/login'

  if (to.path === '/support') {
    const { state } = useWorkflowHub()
    const role = String(state.currentUser?.accessRole || '')
    const isHq = Boolean(state.currentUser?.isHq || state.currentUser?.canUseHq)
    if (state.sessionReady && !isHq && role !== 'admin') return '/dashboard'
  }

  return true
})

router.afterEach((to) => {
  applyRouteSeo(to)
})

export default router
