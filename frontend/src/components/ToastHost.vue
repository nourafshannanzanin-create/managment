<script setup>
import { toastState, removeNotification } from '../utils/notify'

function typeClass(type) {
  return {
    success: 'toast-success',
    error: 'toast-error',
    warning: 'toast-warning',
    info: 'toast-info',
  }[type] || 'toast-info'
}
</script>

<template>
  <div class="toast-host" aria-live="polite">
    <div
      v-for="item in toastState.items"
      :key="item.id"
      class="toast-item"
      :class="typeClass(item.type)"
      @click="removeNotification(item.id)"
    >
      <strong v-if="item.title">{{ item.title }}</strong>
      <span>{{ item.message }}</span>
    </div>
  </div>
</template>

<style scoped>
.toast-host {
  position: fixed;
  top: 1rem;
  inset-inline-start: 1rem;
  z-index: 99999;
  display: grid;
  gap: 0.55rem;
  width: min(22rem, calc(100vw - 2rem));
  pointer-events: none;
}

.toast-item {
  pointer-events: auto;
  border-radius: 0.9rem;
  padding: 0.85rem 1rem;
  background: rgba(15, 35, 40, 0.92);
  color: #f5fffd;
  box-shadow: 0 12px 30px rgba(12, 40, 42, 0.28);
  display: grid;
  gap: 0.2rem;
  cursor: pointer;
  animation: toast-in 0.28s ease;
}

.toast-item strong {
  font-size: 0.82rem;
}

.toast-item span {
  font-size: 0.9rem;
  line-height: 1.5;
}

.toast-success { border-right: 4px solid #3dbf8c; }
.toast-error { border-right: 4px solid #e45d5d; }
.toast-warning { border-right: 4px solid #e0a24a; }
.toast-info { border-right: 4px solid #34908b; }

@keyframes toast-in {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
