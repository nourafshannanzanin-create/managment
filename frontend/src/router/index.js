import { createRouter, createWebHistory } from 'vue-router'

import ApprovalsPage from '../pages/ApprovalsPage.vue'
import DashboardPage from '../pages/DashboardPage.vue'
import ExpensesPage from '../pages/ExpensesPage.vue'
import LoginPage from '../pages/LoginPage.vue'
import ReportsPage from '../pages/ReportsPage.vue'
import RequestCreatePage from '../pages/RequestCreatePage.vue'
import RequestsPage from '../pages/RequestsPage.vue'
import SettingsPage from '../pages/SettingsPage.vue'
import UsersPage from '../pages/UsersPage.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'login', component: LoginPage },
  { path: '/dashboard', name: 'dashboard', component: DashboardPage },
  { path: '/requests', name: 'requests', component: RequestsPage },
  { path: '/requests/new', name: 'request-create', component: RequestCreatePage },
  { path: '/expenses', name: 'expenses', component: ExpensesPage },
  { path: '/approvals', name: 'approvals', component: ApprovalsPage },
  { path: '/reports', name: 'reports', component: ReportsPage },
  { path: '/users', name: 'users', component: UsersPage },
  { path: '/settings', name: 'settings', component: SettingsPage },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

export default router
