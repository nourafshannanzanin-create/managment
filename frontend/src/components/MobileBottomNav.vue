<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { buildMobileNavItems, isNavItemActive } from '../config/appNav'
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

const badges = computed(() => ({
  support: supportUnreadCount.value,
  chat: chatUnreadCount.value,
  tasking: taskingBadgeCount.value,
  requests: requestInboxCount.value,
  expenses: expenseInboxCount.value,
  approvals: approvalInboxCount.value,
}))

const items = computed(() => buildMobileNavItems(state, badges.value))

function navActive(item) {
  return isNavItemActive(item, route.path)
}
</script>

<template>
  <nav
    class="mobile-bottom-nav mobile-bottom-nav-simple"
    aria-label="ناوبری موبایل"
    :style="{ '--nav-count': items.length }"
    @pointerdown="unlockTicketAlerts"
  >
    <div class="mobile-bottom-nav-inner">
      <RouterLink
        v-for="item in items"
        :key="`${item.to}-${item.label}`"
        :to="item.to"
        :class="['mobile-bottom-link', navActive(item) && 'is-active']"
        :aria-current="navActive(item) ? 'page' : undefined"
      >
        <span class="mobile-bottom-icon-slot" aria-hidden="true">
          <IconlyIcon :name="item.icon" decorative />
          <span v-if="item.badgeLabel" class="mobile-bottom-badge">{{ item.badgeLabel }}</span>
        </span>
        <span class="mobile-bottom-label">{{ item.shortLabel || item.label }}</span>
      </RouterLink>
    </div>
  </nav>
</template>
