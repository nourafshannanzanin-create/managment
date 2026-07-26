<script setup>
import TitleHint from './TitleHint.vue'

defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  as: { type: String, default: 'h3' },
  hintLabel: { type: String, default: 'درباره این بخش' },
  size: { type: String, default: 'md' },
})
</script>

<template>
  <div class="section-heading-inline">
    <component :is="as" class="section-heading-inline__title">{{ title }}</component>
    <TitleHint :text="description" :label="hintLabel" :size="size" />
  </div>
</template>

<style scoped>
.section-heading-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.section-heading-inline__title {
  margin: 0;
  min-width: 0;
}
</style>
