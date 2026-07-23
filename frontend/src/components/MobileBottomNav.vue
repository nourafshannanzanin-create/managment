<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { useWorkflowHub } from '../stores/workflowHub'

const route = useRoute()
const { state } = useWorkflowHub()
const isLicenseLocked = computed(() => Boolean(state.currentUser.licenseStatus?.isLocked || state.currentUser.licenseStatus?.is_locked))

const items = computed(() => {
  if (state.currentUser.isHq && !state.currentUser.isHqAdmin) {
    return [{ to: '/hq', label: 'پشتیبانی', icon: 'support_agent' }]
  }

  if (isLicenseLocked.value) {
    return [
      { to: '/dashboard', label: 'خانه', icon: 'home' },
      { to: '/wallet', label: 'کیف پول', icon: 'account_balance_wallet' },
      { to: '/support', label: 'پشتیبانی', icon: 'support_agent' },
    ]
  }

  if (state.currentUser.isHq) {
    return [
      { to: '/hq', label: 'HQ', icon: 'admin_panel_settings' },
      { to: '/dashboard', label: 'خانه', icon: 'home' },
      { to: '/wallet', label: 'کیف پول', icon: 'account_balance_wallet' },
    ]
  }

  const navItems = [
    { to: '/dashboard', label: 'خانه', icon: 'home' },
    { to: '/requests', label: 'درخواست', icon: 'list_alt' },
    { to: '/approvals', label: 'تایید', icon: 'verified' },
  ]

  if (state.currentUser.canAccessExpenses !== false) {
    navItems.push({ to: '/expenses', label: 'هزینه', icon: 'receipt_long' })
  }

  if (state.currentUser.canAccessUsers || state.currentUser.canManageUsers) {
    navItems.push({ to: '/users', label: 'کاربران', icon: 'group' })
  } else if (state.currentUser.canViewReports) {
    navItems.push({ to: '/reports', label: 'گزارش', icon: 'monitoring' })
  } else if (state.currentUser.canAccessSettings || state.currentUser.canManageUsers) {
    navItems.push({ to: '/settings', label: 'تنظیمات', icon: 'settings' })
  } else {
    navItems.push({ to: '/wallet', label: 'کیف پول', icon: 'account_balance_wallet' })
  }

  navItems.push({ to: '/support', label: 'پشتیبانی', icon: 'support_agent' })
  return navItems.slice(0, 5)
})
</script>

<template>
  <nav class="mobile-bottom-nav" aria-label="ناوبری موبایل">
    <RouterLink
      v-for="item in items"
      :key="item.to + '-' + item.label"
      :to="item.to"
      :class="['mobile-bottom-link', route.path === item.to && 'is-active']"
    >
      <IconlyIcon :name="item.icon" decorative />
      <small>{{ item.label }}</small>
    </RouterLink>
  </nav>
</template>

<style scoped>
.mobile-bottom-nav {
  display: none;
}

@media (max-width: 920px) {
  .mobile-bottom-nav {
    position: fixed;
    inset-inline: 0;
    bottom: 0;
    z-index: 55;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(0, 1fr));
    gap: 2px;
    width: 100%;
    max-width: none;
    max-height: none;
    padding: 6px 8px calc(6px + env(safe-area-inset-bottom, 0px));
    overflow: visible;
    background: #f7fbfa;
    border: 0;
    border-top: 1px solid rgba(52, 144, 139, 0.14);
    border-radius: 0;
    box-shadow: 0 -6px 20px rgba(40, 110, 105, 0.08);
    backdrop-filter: none;
    transform: none;
    left: auto;
    transition: opacity 0.18s ease, visibility 0.18s ease;
  }

  .mobile-bottom-link {
    min-width: 0;
    min-height: 52px;
    padding: 6px 4px;
    border-radius: 12px;
    display: grid;
    justify-items: center;
    align-content: center;
    gap: 2px;
    color: #45605c;
    text-decoration: none;
    background: transparent;
    transition: background-color 0.16s ease, color 0.16s ease;
  }

  .mobile-bottom-link :deep(.iconly-shell) {
    font-size: 18px;
  }

  .mobile-bottom-link small {
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 10px;
    font-weight: 700;
    line-height: 1.2;
  }

  .mobile-bottom-link.is-active {
    color: #34908B;
    background: #dcefec;
    box-shadow: none;
  }
}
</style>
