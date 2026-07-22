<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
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
const isLicenseLocked = computed(() => Boolean(state.currentUser.licenseStatus?.isLocked || state.currentUser.licenseStatus?.is_locked))

const navItems = computed(() => {
  const items = [
    { to: '/dashboard', label: 'داشبورد', icon: 'space_dashboard' },
  ]

  if (isLicenseLocked.value) {
    items.push({ to: '/wallet', label: 'خرید نرم‌افزار', icon: 'shopping_cart' })
    items.push({ to: '/support', label: 'پشتیبانی', icon: 'support_agent', badge: supportUnreadCount.value })
    return items
  }

  items.push({ to: '/requests', label: 'درخواست‌ها', icon: 'assignment', badge: requestInboxCount.value })
  items.push({ to: '/approvals', label: 'تاییدیه‌ها', icon: 'fact_check', badge: approvalInboxCount.value })

  if (state.currentUser.canAccessExpenses !== false) {
    items.push({ to: '/expenses', label: 'هزینه‌ها', icon: 'payments', badge: expenseInboxCount.value })
  }

  if (state.currentUser.isHq || state.currentUser.menuAccess?.attendance === true) {
    items.push({ to: '/attendance', label: 'ورود و خروج', icon: 'badge' })
  }

  if (state.currentUser.isManager || state.currentUser.canUseHq) {
    items.push({ to: '/wallet', label: 'کیف پول', icon: 'account_balance_wallet' })
  }

  if (state.currentUser.isHq || state.currentUser.menuAccess?.cloud_storage === true) {
    items.push({ to: '/cloud', label: 'فضای ابری', icon: 'cloud' })
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
        <IconlyIcon name="corporate_fare" decorative />
      </div>
      <div class="brand-copy">
        <strong>{{ organizationTitle }}</strong>
        <small class="brand-subtitle">مرکز مدیریت</small>
      </div>
      <button class="icon-btn mobile-toggle" type="button" aria-label="بستن منو" @click="toggleSidebar">
        <IconlyIcon name="close" decorative />
      </button>
    </div>

    <div class="sidebar-section-label">منوی اصلی</div>

    <nav class="sidebar-nav" aria-label="ناوبری اصلی">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :class="['nav-link', route.path === item.to && 'is-active']"
        :aria-current="route.path === item.to ? 'page' : undefined"
        @click="mobileMenuOpen ? toggleSidebar() : undefined"
      >
        <IconlyIcon :name="item.icon" decorative />
        <span class="nav-link-label">{{ item.label }}</span>
        <span v-if="item.badge" class="nav-link-badge">{{ item.badge }}</span>
      </RouterLink>
    </nav>

    <button class="action-btn tone-soft sidebar-logout" type="button" @click="logout">
      <IconlyIcon name="logout" decorative />
      <span>خروج از سامانه</span>
    </button>
  </aside>
</template>
