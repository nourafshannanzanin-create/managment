<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { computed, onMounted } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import UserAvatar from './UserAvatar.vue'
import { formatBadgeCount } from '../utils/badges'
import { unlockTicketAlerts } from '../utils/ticketAlert'
import { useWorkflowHub } from '../stores/workflowHub'

defineProps({
  mobileMenuOpen: { type: Boolean, required: true },
  toggleSidebar: { type: Function, required: true },
})

const route = useRoute()
const {
  state,
  logout,
  supportUnreadCount,
  chatUnreadCount,
  taskingBadgeCount,
  requestInboxCount,
  expenseInboxCount,
  approvalInboxCount,
  loadChatUnreadConversations,
  loadTaskingDashboard,
} = useWorkflowHub()
const organizationTitle = computed(() => state.hq.selectedOrganization?.name || state.currentUser.organization || 'مجموعه')
const isLicenseLocked = computed(() => Boolean(state.currentUser.licenseStatus?.isLocked || state.currentUser.licenseStatus?.is_locked))

onMounted(() => {
  void loadChatUnreadConversations()
  void loadTaskingDashboard(false).catch(() => {})
})

const navItems = computed(() => {
  const items = []

  // HQ supporters: ticket-focused navigation
  if (state.currentUser.isHq && !state.currentUser.isHqAdmin) {
    items.push({ to: '/hq', label: 'میز پشتیبانی', icon: 'support_agent', badge: supportUnreadCount.value })
    items.push({ to: '/chat', label: 'گفتگو', icon: 'forum', badge: chatUnreadCount.value })
    return items.map((item) => ({ ...item, badgeLabel: formatBadgeCount(item.badge) }))
  }

  items.push({ to: '/dashboard', label: 'داشبورد', icon: 'space_dashboard' })

  if (isLicenseLocked.value) {
    items.push({ to: '/wallet', label: 'خرید نرم‌افزار', icon: 'shopping_cart' })
    if (state.currentUser.accessRole === 'admin' || state.currentUser.isHq) {
      items.push({ to: '/support', label: 'پشتیبانی', icon: 'support_agent', badge: supportUnreadCount.value })
    }
    return items.map((item) => ({ ...item, badgeLabel: formatBadgeCount(item.badge) }))
  }

  items.push({ to: '/tasking', label: 'تسکینگ', icon: 'task_alt', badge: taskingBadgeCount.value })
  items.push({ to: '/chat', label: 'گفتگو', icon: 'forum', badge: chatUnreadCount.value })
  items.push({ to: '/requests', label: 'درخواست‌ها', icon: 'assignment', badge: requestInboxCount.value })
  items.push({ to: '/approvals', label: 'تاییدیه‌ها', icon: 'fact_check', badge: approvalInboxCount.value })

  if (state.currentUser.canAccessExpenses !== false) {
    items.push({ to: '/expenses', label: 'هزینه‌ها', icon: 'payments', badge: expenseInboxCount.value })
  }

  if (state.currentUser.isHq || (state.currentUser.isManager && state.currentUser.menuAccess?.attendance === true)) {
    items.push({ to: '/attendance', label: 'ورود و خروج', icon: 'badge' })
  }

  if (state.currentUser.isManager || state.currentUser.canUseHq) {
    items.push({ to: '/wallet', label: 'کیف پول', icon: 'account_balance_wallet' })
  }

  if (!state.currentUser.isHq && state.currentUser.accessRole === 'admin') {
    items.push({ to: '/support', label: 'پشتیبانی', icon: 'support_agent', badge: supportUnreadCount.value })
  }

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
    items.push({ to: '/hq', label: 'HQ', icon: 'admin_panel_settings', badge: supportUnreadCount.value })
  }

  return items.map((item) => ({ ...item, badgeLabel: formatBadgeCount(item.badge) }))
})
</script>

<template>
  <aside :class="['shell-sidebar', mobileMenuOpen && 'is-open']" @pointerdown="unlockTicketAlerts">
    <div class="sidebar-brand">
      <div class="brand-copy">
        <strong>{{ organizationTitle }}</strong>
        <small class="brand-subtitle">مرکز مدیریت</small>
      </div>
      <div class="brand-mark">
        <img src="/logo/green.webp" alt="کارنومند" width="36" height="36" decoding="async" style="width:36px;height:36px;object-fit:contain;border-radius:10px;" />
      </div>
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
        <span v-if="item.badgeLabel" class="nav-link-badge">{{ item.badgeLabel }}</span>
      </RouterLink>
    </nav>

    <div class="sidebar-user-card">
      <UserAvatar :person="state.currentUser" :name="state.currentUser.name" size="sm" />
      <div class="sidebar-user-copy">
        <strong>{{ state.currentUser.name || 'کاربر' }}</strong>
        <small>{{ state.currentUser.jobTitle || state.currentUser.role || '' }}</small>
      </div>
    </div>

    <button class="action-btn tone-soft sidebar-logout" type="button" @click="logout">
      <IconlyIcon name="logout" decorative />
      <span>خروج از سامانه</span>
    </button>
  </aside>
</template>
