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

const navItems = computed(() => {
  const items = [
    { to: '/dashboard', label: 'Ø¯Ø§Ø´Ø¨ÙˆØ±Ø¯', icon: 'space_dashboard' },
    { to: '/requests', label: 'Ø¯Ø±Ø®ÙˆØ§Ø³Øªâ€ŒÙ‡Ø§', icon: 'assignment', badge: requestInboxCount.value },
  ]

  if (state.currentUser.canAccessExpenses !== false) {
    items.push({ to: '/expenses', label: 'Ù‡Ø²ÛŒÙ†Ù‡â€ŒÙ‡Ø§', icon: 'payments', badge: expenseInboxCount.value })
  }

  if (state.currentUser.isManager || state.currentUser.canUseHq) {
    items.push({ to: '/wallet', label: 'Ú©ÛŒÙ Ù¾ÙˆÙ„', icon: 'account_balance_wallet' })
  }

  items.push({ to: '/support', label: 'Ù¾Ø´ØªÛŒØ¨Ø§Ù†ÛŒ', icon: 'support_agent', badge: supportUnreadCount.value })

  if (state.currentUser.canAccessApprovals || state.currentUser.canApproveDocuments) {
    items.push({ to: '/approvals', label: 'ØªØ§ÛŒÛŒØ¯ÛŒÙ‡â€ŒÙ‡Ø§', icon: 'fact_check', badge: approvalInboxCount.value })
  }

  if (state.currentUser.canViewReports) {
    items.push({ to: '/reports', label: 'Ú¯Ø²Ø§Ø±Ø´Ø§Øª', icon: 'monitoring' })
  }

  if (state.currentUser.canAccessUsers || state.currentUser.canManageUsers) {
    items.push({ to: '/users', label: 'Ú©Ø§Ø±Ø¨Ø±Ø§Ù†', icon: 'groups' })
  }

  if (state.currentUser.canAccessSettings || state.currentUser.canManageUsers) {
    items.push({ to: '/settings', label: 'ØªÙ†Ø¸ÛŒÙ…Ø§Øª', icon: 'settings' })
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
        <strong>Ú©Ø§Ø±Ù…Ù†Ø¯</strong>
      </div>
      <button class="icon-btn mobile-toggle" type="button" @click="toggleSidebar">
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>

    <div class="sidebar-section-label">Ù…Ù†ÙˆÛŒ Ø§ØµÙ„ÛŒ</div>

    <nav class="sidebar-nav" aria-label="Ù†Ø§ÙˆØ¨Ø±ÛŒ Ø§ØµÙ„ÛŒ">
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
      <span>Ø®Ø±ÙˆØ¬ Ø§Ø² Ø³Ø§Ù…Ø§Ù†Ù‡</span>
    </button>
  </aside>
</template>

