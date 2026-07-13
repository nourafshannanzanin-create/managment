<script setup>
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { useWorkflowHub } from '../stores/workflowHub'

defineProps({
  mobileMenuOpen: { type: Boolean, required: true },
  toggleSidebar: { type: Function, required: true },
})

const route = useRoute()
const { state, logout, supportUnreadCount, requestInboxCount, expenseInboxCount, approvalInboxCount } = useWorkflowHub()
const organizationTitle = computed(() => state.hq.selectedOrganization?.name || state.currentUser.organization || 'مجموعه')

const navItems = computed(() => {
  const items = [
    { to: '/dashboard', label: 'داشبورد', icon: 'space_dashboard' },
    { to: '/requests', label: 'درخواست‌ها', icon: 'assignment', badge: requestInboxCount.value },
    { to: '/approvals', label: 'تاییدیه‌ها', icon: 'fact_check', badge: approvalInboxCount.value },
  ]

  if (state.currentUser.canAccessExpenses !== false) {
    items.push({ to: '/expenses', label: 'هزینه‌ها', icon: 'payments', badge: expenseInboxCount.value })
  }

  if (state.currentUser.isManager || state.currentUser.canUseHq) {
    items.push({ to: '/wallet', label: 'کیف پول', icon: 'account_balance_wallet' })
  }

  items.push({ to: '/support', label: 'پشتیبانی', icon: 'support_agent', badge: supportUnreadCount.value })

  if (state.currentUser.canViewReports) {
    items.push({ to: '/reports', label: 'گزارشات', icon: 'monitoring' })
  }

  if (state.currentUser.canAccessUsers || state.currentUser.canManageUsers) {
    items.push({ to: '/users', label: 'کاربران', icon: 'groups' })
  }

  if (state.currentUser.canAccessSettings || state.currentUser.canManageUsers) {
    items.push({ to: '/settings', label: 'تنظیمات', icon: 'settings' })
  }

  if (state.currentUser.canUseHq) {
    items.push({ to: '/hq', label: 'HQ', icon: 'admin_panel_settings' })
  }

  return items
})
</script>

<template>
  <aside :class="['shell-sidebar', mobileMenuOpen && 'is-open']">
    <div class="sidebar-brand">
      <div class="brand-mark">
        <span class="material-symbols-outlined">corporate_fare</span>
      </div>
      <div class="brand-copy">
        <strong>{{ organizationTitle }}</strong>
      </div>
      <button class="icon-btn mobile-toggle" type="button" @click="toggleSidebar">
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>

    <div class="sidebar-section-label">منوی اصلی</div>

    <nav class="sidebar-nav" aria-label="ناوبری اصلی">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :class="['nav-link', route.path === item.to && 'is-active']"
        @click="mobileMenuOpen ? toggleSidebar() : undefined"
      >
        <span class="material-symbols-outlined">{{ item.icon }}</span>
        <span class="nav-link-label">{{ item.label }}</span>
        <span v-if="item.badge" class="nav-link-badge">{{ item.badge }}</span>
      </RouterLink>
    </nav>

    <button class="action-btn tone-soft sidebar-logout" type="button" @click="logout">
      <span class="material-symbols-outlined">logout</span>
      <span>خروج از سامانه</span>
    </button>
  </aside>
</template>

