<script setup>
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { useWorkflowHub } from '../stores/workflowHub'

defineProps({
  mobileMenuOpen: { type: Boolean, required: true },
  toggleSidebar: { type: Function, required: true },
})

const route = useRoute()
const { state, visibleNavItems, logout } = useWorkflowHub()

const displayName = computed(() => {
  const name = state.currentUser.name || 'کاربر'
  return name === 'آرمان کریمی' ? 'امید کریمی' : name
})
</script>

<template>
  <aside :class="['shell-sidebar', mobileMenuOpen && 'is-open']">
    <div class="brand-strip">
      <div class="brand-mark">
        <span class="material-symbols-outlined">stacked_line_chart</span>
      </div>
      <div class="brand-copy">
        <strong>کارنومند</strong>
        <small>{{ state.currentUser.organization || 'سازمان' }}</small>
      </div>
      <button class="icon-btn mobile-toggle" @click="toggleSidebar">
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>

    <div class="profile-strip">
      <div class="avatar-pill">{{ state.currentUser.avatar || 'U' }}</div>
      <div class="profile-copy">
        <strong>{{ displayName }}</strong>
        <p>{{ state.currentUser.role || state.currentUser.department }}</p>
      </div>
    </div>

    <nav class="sidebar-nav">
      <RouterLink
        v-for="item in visibleNavItems"
        :key="item.to"
        :to="item.to"
        :class="['nav-link', route.path === item.to && 'is-active']"
        @click="mobileMenuOpen ? toggleSidebar() : undefined"
      >
        <span class="material-symbols-outlined">{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>

    <button class="action-btn tone-soft sidebar-logout" @click="logout">
      <span class="material-symbols-outlined">logout</span>
      <span>خروج</span>
    </button>
  </aside>
</template>
