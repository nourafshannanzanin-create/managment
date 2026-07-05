<script setup>
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { useWorkflowHub } from '../stores/workflowHub'

const route = useRoute()
const { state } = useWorkflowHub()

const items = computed(() => {
  const navItems = [
    { to: '/dashboard', label: 'خانه', icon: 'home' },
    { to: '/requests', label: 'درخواست', icon: 'list_alt' },
  ]
  if (state.currentUser.canAccessExpenses !== false) navItems.push({ to: '/expenses', label: 'هزینه', icon: 'receipt_long' })
  if (state.currentUser.canAccessUsers || state.currentUser.canManageUsers) {
    navItems.push({ to: '/users', label: 'کاربران', icon: 'group' })
  } else if (state.currentUser.canViewReports) {
    navItems.push({ to: '/reports', label: 'گزارش', icon: 'monitoring' })
  } else if (state.currentUser.canAccessApprovals || state.currentUser.canApproveDocuments) {
    navItems.push({ to: '/approvals', label: 'تایید', icon: 'verified' })
  }
  if (state.currentUser.canAccessSettings || state.currentUser.canManageUsers) {
    navItems.push({ to: '/settings', label: 'تنظیمات', icon: 'settings' })
  }
  return navItems
})
</script>

<template>
  <nav class="mobile-bottom-nav">
    <RouterLink
      v-for="item in items"
      :key="item.to + '-' + item.label"
      :to="item.to"
      :class="['mobile-bottom-link', route.path === item.to && 'is-active']"
    >
      <span class="material-symbols-outlined">{{ item.icon }}</span>
      <small>{{ item.label }}</small>
    </RouterLink>
  </nav>
</template>

<style scoped>
.mobile-bottom-nav {
  position: fixed;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 30;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
  width: min(720px, calc(100vw - 24px));
  padding: 10px 12px;
  background: rgba(229, 195, 166, 0.78);
  border-radius: 24px;
  box-shadow: 0 8px 24px rgba(46, 67, 116, 0.12);
}

.mobile-bottom-link {
  min-height: 62px;
  padding: 8px 4px;
  border-radius: 18px;
  display: grid;
  justify-items: center;
  align-content: center;
  gap: 4px;
  color: #4B527E;
  text-decoration: none;
  transition: transform 0.18s ease, background-color 0.18s ease, color 0.18s ease;
}

.mobile-bottom-link span {
  font-size: 28px;
  line-height: 1;
}

.mobile-bottom-link small {
  font-size: 11px;
  line-height: 1;
}

.mobile-bottom-link.is-active {
  color: #ffffff;
  background: #2E4374;
  box-shadow: 0 8px 18px rgba(46, 67, 116, 0.24);
  transform: translateY(4px);
}

@media (max-width: 640px) {
  .mobile-bottom-nav {
    top: 8px;
    width: calc(100vw - 16px);
    padding: 8px;
  }

  .mobile-bottom-link {
    min-height: 58px;
  }
}
</style>
