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
  min-height: 92px;
  padding: 20px 20px 18px;
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr) 88px;
  align-items: center;
  gap: 8px;
  background: #f7f9ff;
  border-bottom: 1px solid rgba(188, 200, 201, 0.3);
}

.mobile-topbar-side {
  display: flex;
  align-items: center;
  gap: 10px;
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
  color: #026166;
  font-size: 20px;
  font-weight: 800;
  line-height: 1.2;
}

.mobile-topbar-center p {
  margin: 4px 0 0;
  color: #6f797a;
  font-size: 12px;
  line-height: 1.4;
}
</style>
