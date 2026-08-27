<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { computed, onMounted } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import UserAvatar from './UserAvatar.vue'
import { buildMainNavItems, isNavItemActive } from '../config/appNav'
import { unlockTicketAlerts } from '../utils/ticketAlert'
import { prefetchRoute } from '../utils/prefetchRoute'
import { useWorkflowHub } from '../stores/workflowHub'

defineProps({
  mobileMenuOpen: { type: Boolean, required: true },
  toggleSidebar: { type: Function, required: true },
})

const route = useRoute()
const router = useRouter()
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

const organizationTitle = computed(
  () => state.hq.selectedOrganization?.name || state.currentUser.organization || 'مجموعه',
)

onMounted(() => {
  const warmBadges = () => {
    void loadChatUnreadConversations()
    void loadTaskingDashboard(false).catch(() => {})
  }
  if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
    window.requestIdleCallback(warmBadges, { timeout: 2500 })
  } else {
    window.setTimeout(warmBadges, 400)
  }
})

const badges = computed(() => ({
  support: supportUnreadCount.value,
  chat: chatUnreadCount.value,
  tasking: taskingBadgeCount.value,
  requests: requestInboxCount.value,
  expenses: expenseInboxCount.value,
  approvals: approvalInboxCount.value,
}))

const navItems = computed(() => buildMainNavItems(state, badges.value))

function navActive(item) {
  return isNavItemActive(item, route.path)
}

function warmNav(item) {
  prefetchRoute(router, item?.to)
}
</script>

<template>
  <aside
    :class="['shell-sidebar', 'sidebar-luxe', mobileMenuOpen && 'is-open']"
    @pointerdown="unlockTicketAlerts"
  >
    <div class="sidebar-brand-card">
      <div class="sidebar-brand-glow" aria-hidden="true" />
      <div class="sidebar-brand-inner">
        <div class="brand-mark-luxe">
          <img src="/logo/green.webp" alt="کارنومند" width="40" height="40" decoding="async" />
        </div>
        <div class="brand-copy">
          <strong>{{ organizationTitle }}</strong>
          <small class="brand-subtitle">مرکز مدیریت کارنومند</small>
        </div>
      </div>
    </div>

    <div class="sidebar-section-label">منوی اصلی</div>

    <nav class="sidebar-nav sidebar-nav-luxe" aria-label="ناوبری اصلی">
      <RouterLink
        v-for="item in navItems"
        :key="item.id || item.to"
        :to="item.to"
        :class="['nav-link', 'nav-link-luxe', navActive(item) && 'is-active']"
        :aria-current="navActive(item) ? 'page' : undefined"
        @pointerenter="warmNav(item)"
        @focusin="warmNav(item)"
        @click="mobileMenuOpen ? toggleSidebar() : undefined"
      >
        <span class="nav-link-icon-wrap" aria-hidden="true">
          <IconlyIcon :name="item.icon" decorative />
        </span>
        <span class="nav-link-label">{{ item.label }}</span>
        <span v-if="item.badgeLabel" class="nav-link-badge">{{ item.badgeLabel }}</span>
      </RouterLink>
    </nav>

    <footer class="sidebar-footer-luxe">
      <div class="sidebar-user-card">
        <UserAvatar :person="state.currentUser" :name="state.currentUser.name" size="sm" />
        <div class="sidebar-user-copy">
          <strong>{{ state.currentUser.name || 'کاربر' }}</strong>
          <small>{{ state.currentUser.jobTitle || state.currentUser.role || '' }}</small>
        </div>
      </div>

      <button class="sidebar-logout sidebar-logout-luxe" type="button" @click="logout">
        <IconlyIcon name="logout" decorative />
        <span>خروج از سامانه</span>
      </button>
    </footer>
  </aside>
</template>
