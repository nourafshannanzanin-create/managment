<script setup>
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { useWorkflowHub } from '../stores/workflowHub'

const route = useRoute()
const { logout, state } = useWorkflowHub()

const displayName = computed(() => {
  const name = state.currentUser.name || 'کاربر'
  return name === 'آرمان کریمی' ? 'امید کریمی' : name
})

const navItems = computed(() => {
  const items = [
    { to: '/dashboard', label: 'داشبورد', icon: 'dashboard' },
    { to: '/requests', label: 'درخواست‌ها', icon: 'assignment' },
  ]
  if (state.currentUser.canAccessExpenses !== false) items.push({ to: '/expenses', label: 'هزینه‌ها', icon: 'payments' })
  if (state.currentUser.canApproveDocuments) items.push({ to: '/approvals', label: 'تاییدیه‌ها', icon: 'fact_check' })
  if (state.currentUser.canViewReports) items.push({ to: '/reports', label: 'گزارشات', icon: 'monitoring' })
  if (state.currentUser.canAccessUsers || state.currentUser.canManageUsers) items.push({ to: '/users', label: 'کاربران', icon: 'group' })
  items.push({ to: '/settings', label: 'تنظیمات', icon: 'settings' })
  return items
})
</script>

<template>
  <header class="topbar-shell">
    <div class="topbar-user">
      <div class="topbar-account">
        <button class="topbar-logout" @click="logout">
          <span class="material-symbols-outlined">logout</span>
          <span>خروج</span>
        </button>
        <div class="topbar-account-copy">
          <strong>{{ displayName }}</strong>
          <small>{{ state.currentUser.role || state.currentUser.department || 'عضو سامانه' }}</small>
        </div>
      </div>
    </div>

    <div class="topbar-nav-row">
      <nav class="topbar-nav" aria-label="Primary">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :class="['topbar-link', route.path === item.to && 'is-active']"
        >
          <span class="material-symbols-outlined">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
    </div>
  </header>
</template>
