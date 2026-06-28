<script setup>
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { useWorkflowHub } from '../stores/workflowHub'

const route = useRoute()
const { logout, state, visibleNavItems } = useWorkflowHub()

const displayName = computed(() => {
  const name = state.currentUser.name || 'کاربر'
  return name === 'آرمان کریمی' ? 'امید کریمی' : name
})
</script>

<template>
  <header class="topbar-shell">
    <div class="topbar-user">
      <div class="topbar-account">
        <button class="topbar-logout" @click="logout">
          <span class="material-symbols-outlined">logout</span>
          <span>خروج</span>
        </button>
        <div class="topbar-account-copy">
          <strong>{{ displayName }}</strong>
          <small>{{ state.currentUser.role || state.currentUser.department || 'عضو سامانه' }}</small>
        </div>
      </div>
    </div>

    <div class="topbar-nav-row">
      <div class="topbar-brand">
        <div class="topbar-mark">
          <span class="material-symbols-outlined">dashboard_customize</span>
        </div>
        <div class="topbar-copy">
          <strong>کارنومند</strong>
          <small>{{ state.currentUser.organization || 'سازمان پیش فرض' }}</small>
        </div>
      </div>

      <nav class="topbar-nav" aria-label="Primary">
        <RouterLink
          v-for="item in visibleNavItems"
          :key="item.to"
          :to="item.to"
          :class="['topbar-link', route.path === item.to && 'is-active']"
        >
          <span class="material-symbols-outlined">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
    </div>
  </header>
</template>
