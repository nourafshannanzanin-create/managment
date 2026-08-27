<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { computed } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { hubTabsForPath } from '../config/appNav'
import { prefetchRoute } from '../utils/prefetchRoute'
import { useWorkflowHub } from '../stores/workflowHub'

const route = useRoute()
const router = useRouter()
const {
  state,
  supportUnreadCount,
  chatUnreadCount,
  taskingBadgeCount,
  requestInboxCount,
  expenseInboxCount,
  approvalInboxCount,
} = useWorkflowHub()

const badges = computed(() => ({
  support: supportUnreadCount.value,
  chat: chatUnreadCount.value,
  tasking: taskingBadgeCount.value,
  requests: requestInboxCount.value,
  expenses: expenseInboxCount.value,
  approvals: approvalInboxCount.value,
}))

const hub = computed(() => hubTabsForPath(route.path, state, badges.value))
const tabs = computed(() => hub.value?.tabs || [])
const visible = computed(() => tabs.value.length > 1)

function isActive(to) {
  return route.path === to || route.path.startsWith(`${to}/`)
}

function warmTab(to) {
  prefetchRoute(router, to)
}
</script>

<template>
  <nav v-if="visible" class="hub-tab-bar" :aria-label="hub?.title || 'بخش‌ها'">
    <div class="hub-tab-bar-track">
      <RouterLink
        v-for="tab in tabs"
        :key="tab.to"
        :to="tab.to"
        :class="['hub-tab', isActive(tab.to) && 'is-active']"
        :aria-current="isActive(tab.to) ? 'page' : undefined"
        @pointerenter="warmTab(tab.to)"
        @focusin="warmTab(tab.to)"
      >
        <span class="hub-tab-icon" aria-hidden="true">
          <IconlyIcon :name="tab.icon" decorative />
        </span>
        <span class="hub-tab-label">{{ tab.label }}</span>
        <span v-if="tab.badgeLabel" class="hub-tab-badge">{{ tab.badgeLabel }}</span>
      </RouterLink>
    </div>
  </nav>
</template>

<style scoped>
.hub-tab-bar {
  position: static;
  top: auto;
  z-index: 1;
  margin: 0 0 14px;
}

@media (min-width: 921px) {
  .hub-tab-bar {
    position: sticky;
    top: 0;
    z-index: 8;
  }
}

.hub-tab-bar-track {
  display: flex;
  flex-wrap: nowrap;
  gap: 6px;
  padding: 6px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  border-radius: 16px;
  border: 1px solid rgba(52, 144, 139, 0.14);
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(10px);
}

.hub-tab-bar-track::-webkit-scrollbar {
  display: none;
}

.hub-tab {
  position: relative;
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  padding: 0 14px;
  border-radius: 12px;
  color: #4a6763;
  text-decoration: none;
  font-weight: 750;
  font-size: 0.84rem;
  white-space: nowrap;
  transition: background 0.18s ease, color 0.18s ease;
}

.hub-tab:hover {
  background: rgba(52, 144, 139, 0.08);
  color: #1f5c59;
}

.hub-tab.is-active {
  color: #fff;
  /* solid color — global CSS nukes background-image/gradients */
  background-color: #34908b;
  background-image: none;
}

.hub-tab-icon {
  display: inline-grid;
  place-items: center;
  width: 18px;
  height: 18px;
}

.hub-tab.is-active :deep(.iconly-img) {
  filter: brightness(0) invert(1);
}

.hub-tab-badge {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 800;
  background: rgba(225, 29, 72, 0.14);
  color: #c23a48;
}

.hub-tab.is-active .hub-tab-badge {
  background: rgba(255, 255, 255, 0.22);
  color: #fff;
}

@media (max-width: 760px) {
  .hub-tab-bar {
    position: static;
    top: auto;
    z-index: 1;
    margin-bottom: 10px;
  }

  .hub-tab {
    min-height: 38px;
    padding: 0 12px;
    font-size: 0.78rem;
    gap: 6px;
  }
}
</style>
