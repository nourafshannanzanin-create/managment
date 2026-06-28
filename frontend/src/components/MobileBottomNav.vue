<script setup>
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { useWorkflowHub } from '../stores/workflowHub'

const route = useRoute()
const { canManageUsers, canViewReports } = useWorkflowHub()

const specialItem = computed(() => {
  if (route.path === '/users') return { to: '/users', label: 'کاربران', icon: 'group' }
  if (route.path === '/reports') return { to: '/reports', label: 'گزارش', icon: 'monitoring' }
  if (canManageUsers.value) return { to: '/users', label: 'کاربران', icon: 'group' }
  if (canViewReports.value) return { to: '/reports', label: 'گزارش', icon: 'monitoring' }
  return { to: '/settings', label: 'تنظیمات', icon: 'settings' }
})

const items = computed(() => [
  { to: '/dashboard', label: 'خانه', icon: 'home' },
  { to: '/requests', label: 'درخواست', icon: 'list_alt' },
  { to: '/expenses', label: 'هزینه', icon: 'receipt_long' },
  specialItem.value,
  { to: '/settings', label: 'تنظیمات', icon: 'settings' },
])
</script>

<template>
  <nav class="mobile-bottom-nav">
    <RouterLink
      v-for="item in items"
      :key="`${item.to}-${item.label}`"
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
  background: #cfe0fb;
  border-radius: 24px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.mobile-bottom-link {
  min-height: 62px;
  padding: 8px 4px;
  border-radius: 18px;
  display: grid;
  justify-items: center;
  align-content: center;
  gap: 4px;
  color: #28363a;
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
  background: #2d7a7f;
  box-shadow: 0 8px 18px rgba(2, 97, 102, 0.22);
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
