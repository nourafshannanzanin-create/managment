<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>

<template>
  <header class="mobile-topbar">
    <div class="mobile-topbar-side mobile-topbar-side-right">
      <slot name="right" />
    </div>

    <div class="mobile-topbar-center">
      <h1>{{ title }}</h1>
      <p v-if="subtitle">{{ subtitle }}</p>
    </div>

    <div class="mobile-topbar-side mobile-topbar-side-left">
      <slot name="left" />
    </div>
  </header>
</template>

<style scoped>
.mobile-topbar {
  min-height: 56px;
  padding: 10px 14px;
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr) 56px;
  align-items: center;
  gap: 8px;
  background: #f7fbfa;
  border-bottom: 1px solid rgba(52, 144, 139, 0.12);
}

.mobile-topbar-side {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mobile-topbar-side-right {
  justify-content: flex-start;
}

.mobile-topbar-side-left {
  justify-content: flex-end;
}

.mobile-topbar-center {
  min-width: 0;
  text-align: center;
}

.mobile-topbar-center h1 {
  margin: 0;
  color: #152523;
  font-size: 0.95rem;
  font-weight: 750;
  line-height: 1.25;
}

.mobile-topbar-center p {
  margin: 2px 0 0;
  color: #45605c;
  font-size: 0.7rem;
  line-height: 1.3;
}
</style>
