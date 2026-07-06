<script setup>
defineProps({
  error: { type: Object, default: null },
  compact: { type: Boolean, default: false },
})
</script>

<template>
  <section v-if="error?.message" :class="['error-notice', compact && 'is-compact']" role="alert">
    <div class="error-notice-icon">
      <span class="material-symbols-outlined">error</span>
    </div>
    <div class="error-notice-copy">
      <strong>{{ error.title || 'خطا در انجام عملیات' }}</strong>
      <p>{{ error.message }}</p>
      <div v-if="error.fields?.length" class="error-field-list">
        <span v-for="item in error.fields" :key="`${item.field}-${item.message}`">
          {{ item.label }}: {{ item.message }}
        </span>
      </div>
      <small v-if="error.suggestion">{{ error.suggestion }}</small>
    </div>
  </section>
</template>
