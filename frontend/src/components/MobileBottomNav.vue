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
      { to: '/wallet', label: 'کیف پول', icon: 'account_balance_wallet' },
      { to: '/support', label: 'پشتیبانی', icon: 'support_agent', badge: supportUnreadCount.value },
    ]
  }

  if (state.currentUser.isHq) {
    return [
      { to: '/hq', label: 'HQ', icon: 'admin_panel_settings', badge: supportUnreadCount.value },
      { to: '/dashboard', label: 'خانه', icon: 'home' },
      { to: '/chat', label: 'گفتگو', icon: 'forum', badge: chatUnreadCount.value },
      { to: '/tasking', label: 'تسک', icon: 'task_alt', badge: taskingBadgeCount.value },
      { to: '/wallet', label: 'کیف پول', icon: 'account_balance_wallet' },
    ]
  }

  const navItems = [
    { to: '/dashboard', label: 'خانه', icon: 'home' },
    { to: '/tasking', label: 'تسک', icon: 'task_alt', badge: taskingBadgeCount.value },
    { to: '/chat', label: 'گفتگو', icon: 'forum', badge: chatUnreadCount.value },
    { to: '/requests', label: 'درخواست', icon: 'list_alt', badge: requestInboxCount.value },
    { to: '/approvals', label: 'تایید', icon: 'verified', badge: approvalInboxCount.value },
  ]

  if (state.currentUser.canAccessExpenses !== false && Number(expenseInboxCount.value || 0) > 0) {
    // Prefer showing expense badge when actionable items exist.
    navItems[4] = { to: '/expenses', label: 'هزینه', icon: 'receipt_long', badge: expenseInboxCount.value }
  }

  if (state.currentUser.accessRole === 'admin' && Number(supportUnreadCount.value || 0) > 0) {
    navItems.push({ to: '/support', label: 'پشتیبانی', icon: 'support_agent', badge: supportUnreadCount.value })
  }

  return navItems.slice(0, 5).map((item) => ({
    ...item,
    badgeLabel: formatBadgeCount(item.badge),
  }))
})
</script>

<template>
  <nav class="mobile-bottom-nav" aria-label="ناوبری موبایل" @pointerdown="unlockTicketAlerts">
    <RouterLink
      v-for="item in items"
      :key="item.to + '-' + item.label"
      :to="item.to"
      :class="['mobile-bottom-link', route.path === item.to && 'is-active']"
    >
      <span class="mobile-bottom-icon-wrap">
        <IconlyIcon :name="item.icon" decorative />
        <span v-if="item.badgeLabel" class="mobile-bottom-badge">{{ item.badgeLabel }}</span>
      </span>
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
    position: relative;
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

  .mobile-bottom-icon-wrap {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 22px;
  }

  .mobile-bottom-link :deep(.iconly-shell) {
    font-size: 18px;
  }

  .mobile-bottom-badge {
    position: absolute;
    top: -7px;
    inset-inline-end: -10px;
    min-width: 18px;
    height: 18px;
    padding: 0 5px;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: #e11d48;
    color: #fff;
    font-size: 10px;
    font-weight: 800;
    line-height: 1;
    box-shadow: 0 0 0 2px #f7fbfa;
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
