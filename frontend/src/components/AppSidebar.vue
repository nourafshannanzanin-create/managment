<script setup>
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

defineProps({
  mobileMenuOpen: { type: Boolean, required: true },
  toggleSidebar: { type: Function, required: true },
})

const route = useRoute()

const navItems = computed(() => [
  { to: '/dashboard', label: 'داشبورد', icon: 'dashboard' },
  { to: '/requests', label: 'درخواست‌ها', icon: 'assignment' },
  { to: '/expenses', label: 'هزینه‌ها', icon: 'payments' },
  { to: '/approvals', label: 'تاییدها', icon: 'fact_check' },
  { to: '/reports', label: 'گزارشات', icon: 'monitoring' },
  { to: '/users', label: 'کاربران', icon: 'group' },
  { to: '/settings', label: 'تنظیمات', icon: 'settings' },
])
</script>

<template>
  <aside :class="['shell-sidebar', mobileMenuOpen && 'is-open']">
    <div class="brand-strip">
      <div class="brand-mark">
        <span class="material-symbols-outlined">grid_view</span>
      </div>
      <div>
        <strong>کارومند</strong>
      </div>
      <button class="icon-btn mobile-toggle" @click="toggleSidebar">
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>

    <nav class="sidebar-nav">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :class="['nav-link', route.path === item.to && 'is-active']"
        @click="mobileMenuOpen ? toggleSidebar() : undefined"
      >
        <span class="material-symbols-outlined">{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>
  </aside>
</template>
