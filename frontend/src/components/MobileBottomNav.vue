<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { formatBadgeCount } from '../utils/badges'
import { unlockTicketAlerts } from '../utils/ticketAlert'
import { useWorkflowHub } from '../stores/workflowHub'

const route = useRoute()
const {
  state,
  supportUnreadCount,
  chatUnreadCount,
  taskingBadgeCount,
  requestInboxCount,
  expenseInboxCount,
  approvalInboxCount,
} = useWorkflowHub()
const isLicenseLocked = computed(() => Boolean(state.currentUser.licenseStatus?.isLocked || state.currentUser.licenseStatus?.is_locked))

const MOBILE_LABELS = {
  '/dashboard': 'خانه',
  '/tasking': 'تسک',
  '/chat': 'گفتگو',
  '/requests': 'درخواست',
  '/approvals': 'تأیید',
  '/expenses': 'هزینه',
  '/wallet': 'کیف',
  '/support': 'پشتیبان',
  '/hq': 'HQ',
}

function mobileLabel(item) {
  return MOBILE_LABELS[item.to] || item.label
}

function isNavActive(path) {
  if (route.path === path) return true
  return path !== '/dashboard' && route.path.startsWith(`${path}/`)
}

const items = computed(() => {
  if (state.currentUser.isHq && !state.currentUser.isHqAdmin) {
    return [
      { to: '/hq', label: 'پشتیبانی', icon: 'support_agent', badge: supportUnreadCount.value },
      { to: '/chat', label: 'گفتگو', icon: 'forum', badge: chatUnreadCount.value },
    ]
  }

  if (isLicenseLocked.value) {
    return [
      { to: '/dashboard', label: 'خانه', icon: 'home' },
      { to: '/wallet', label: 'کیف', icon: 'account_balance_wallet' },
      { to: '/support', label: 'پشتیبان', icon: 'support_agent', badge: supportUnreadCount.value },
    ]
  }

  if (state.currentUser.isHq) {
    return [
      { to: '/hq', label: 'HQ', icon: 'admin_panel_settings', badge: supportUnreadCount.value },
      { to: '/dashboard', label: 'خانه', icon: 'home' },
      { to: '/chat', label: 'گفتگو', icon: 'forum', badge: chatUnreadCount.value },
      { to: '/tasking', label: 'تسک', icon: 'task_alt', badge: taskingBadgeCount.value },
      { to: '/wallet', label: 'کیف', icon: 'account_balance_wallet' },
    ]
  }

  const navItems = [
    { to: '/dashboard', label: 'خانه', icon: 'home' },
    { to: '/tasking', label: 'تسک', icon: 'task_alt', badge: taskingBadgeCount.value },
    { to: '/chat', label: 'گفتگو', icon: 'forum', badge: chatUnreadCount.value },
    { to: '/requests', label: 'درخواست‌ها', icon: 'list_alt', badge: requestInboxCount.value },
    { to: '/approvals', label: 'تأیید', icon: 'verified', badge: approvalInboxCount.value },
  ]

  if (state.currentUser.canAccessExpenses !== false && Number(expenseInboxCount.value || 0) > 0) {
    navItems[4] = { to: '/expenses', label: 'هزینه', icon: 'receipt_long', badge: expenseInboxCount.value }
  }

  if (state.currentUser.accessRole === 'admin' && Number(supportUnreadCount.value || 0) > 0) {
    navItems.push({ to: '/support', label: 'پشتیبان', icon: 'support_agent', badge: supportUnreadCount.value })
  }

  return navItems.slice(0, 5).map((item) => ({
    ...item,
    shortLabel: mobileLabel(item),
    badgeLabel: formatBadgeCount(item.badge),
  }))
})
</script>

<template>
  <nav
    class="mobile-bottom-nav mobile-bottom-nav-luxe"
    aria-label="ناوبری موبایل"
    :style="{ '--nav-count': items.length }"
    @pointerdown="unlockTicketAlerts"
  >
    <div class="mobile-bottom-nav-inner">
      <RouterLink
        v-for="item in items"
        :key="item.to"
        :to="item.to"
        :class="['mobile-bottom-link', isNavActive(item.to) && 'is-active']"
        :aria-current="isNavActive(item.to) ? 'page' : undefined"
      >
        <span class="mobile-bottom-icon-slot" aria-hidden="true">
          <span class="mobile-bottom-icon-ring">
            <IconlyIcon :name="item.icon" decorative />
          </span>
          <span v-if="item.badgeLabel" class="mobile-bottom-badge">{{ item.badgeLabel }}</span>
        </span>
        <span class="mobile-bottom-label">{{ item.shortLabel }}</span>
      </RouterLink>
    </div>
  </nav>
</template>
