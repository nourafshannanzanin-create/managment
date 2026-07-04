<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import { useWorkflowHub } from '../stores/workflowHub'

const route = useRoute()
const { logout, state, toggleSidebar } = useWorkflowHub()

const displayName = computed(() => state.currentUser.name || 'کاربر')

const routeMeta = computed(() => {
  const dictionary = {
    '/dashboard': { eyebrow: 'نمای کلی سازمان', title: 'داشبورد مدیریتی' },
    '/requests': { eyebrow: 'عملیات درخواست‌ها', title: 'مدیریت درخواست‌ها' },
    '/expenses': { eyebrow: 'کنترل مالی', title: 'هزینه‌ها و اسناد مالی' },
    '/approvals': { eyebrow: 'کنترل اسناد', title: 'تاییدیه‌ها و گردش امضا' },
    '/reports': { eyebrow: 'بینش سازمانی', title: 'گزارش‌ها و خروجی‌ها' },
    '/users': { eyebrow: 'سرمایه انسانی', title: 'کاربران و نقش‌ها' },
    '/settings': { eyebrow: 'پیکربندی سامانه', title: 'تنظیمات سازمان' },
  }

  return dictionary[route.path] || { eyebrow: 'سامانه سازمانی', title: 'کارمند' }
})
</script>

<template>
  <header class="topbar-shell">
    <div class="topbar-intro">
      <button class="icon-btn mobile-menu-trigger" type="button" @click="toggleSidebar">
        <span class="material-symbols-outlined">menu</span>
      </button>

      <div class="topbar-intro-copy">
        <span class="topbar-eyebrow">{{ routeMeta.eyebrow }}</span>
        <strong>{{ routeMeta.title }}</strong>
      </div>
    </div>

    <div class="topbar-actions">
      <div class="topbar-user-card">
        <div class="topbar-avatar">
          {{ (displayName || 'ک').slice(0, 1) }}
        </div>
        <div class="topbar-user-copy">
          <strong>{{ displayName }}</strong>
          <small>{{ state.currentUser.role || state.currentUser.department || 'عضو سامانه' }}</small>
        </div>
      </div>

      <button class="action-btn tone-soft topbar-logout" type="button" @click="logout">
        <span class="material-symbols-outlined">logout</span>
        <span>خروج</span>
      </button>
    </div>
  </header>
</template>
