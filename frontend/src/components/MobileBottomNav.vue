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
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 7px;
  width: min(360px, calc(100vw - 20px));
  max-height: calc(100dvh - 16px);
  padding: 8px;
  overflow-y: auto;
  background: rgba(255, 250, 245, 0.92);
  border: 1px solid rgba(46, 67, 116, 0.1);
  border-radius: 18px;
  box-shadow: 0 12px 30px rgba(46, 67, 116, 0.14);
  backdrop-filter: blur(18px);
  -webkit-overflow-scrolling: touch;
}

.mobile-bottom-link {
  min-width: 0;
  min-height: 48px;
  padding: 7px 6px;
  border-radius: 14px;
  display: grid;
  justify-items: center;
  align-content: center;
  gap: 3px;
  color: #4B527E;
  text-decoration: none;
  background: rgba(46, 67, 116, 0.05);
  transition: transform 0.18s ease, background-color 0.18s ease, color 0.18s ease;
}

.mobile-bottom-link span {
  font-size: 21px;
  line-height: 1;
}

.mobile-bottom-link small {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 10px;
  font-weight: 800;
  line-height: 1.2;
}

.mobile-bottom-link.is-active {
  color: #ffffff;
  background: #2E4374;
  box-shadow: 0 8px 16px rgba(46, 67, 116, 0.22);
}

@media (max-width: 640px) {
  .mobile-bottom-nav {
    top: 8px;
    width: min(340px, calc(100vw - 14px));
    gap: 6px;
    padding: 7px;
  }

  .mobile-bottom-link {
    min-height: 44px;
  }
}
</style>
