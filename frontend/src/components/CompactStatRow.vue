<script setup>
defineProps({
  items: { type: Array, required: true },
})
</script>

<template>
  <section class="stat-row">
    <article v-for="item in items" :key="item.id || item.label" class="stat-tile">
      <span>{{ item.label }}</span>
      <strong>{{ item.value }}</strong>
      <small v-if="item.detail">{{ item.detail }}</small>
    </article>
  </section>
</template>
