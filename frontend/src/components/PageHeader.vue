<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import TitleHint from './TitleHint.vue'

defineProps({
  eyebrow: { type: String, default: '' },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  searchValue: { type: String, default: '' },
  searchPlaceholder: { type: String, default: '' },
  showSearch: { type: Boolean, default: false },
  actionLabel: { type: String, default: '' },
  actionIcon: { type: String, default: 'add' },
  actionTone: { type: String, default: 'primary' },
})

const emit = defineEmits(['update:searchValue', 'action', 'menu'])
</script>

<template>
  <header class="page-header" aria-labelledby="page-title">
    <div class="page-header-copy">
      <span v-if="eyebrow" class="page-eyebrow">{{ eyebrow }}</span>
      <div class="page-header-title-row">
        <h1 id="page-title">{{ title }}</h1>
        <TitleHint :text="description" label="درباره این صفحه" size="lg" />
      </div>
    </div>

    <div v-if="showSearch || actionLabel" class="page-header-tools">
      <label v-if="showSearch" class="search-shell page-header-search">
        <IconlyIcon name="search" decorative />
        <input
          :value="searchValue"
          type="search"
          :placeholder="searchPlaceholder"
          @input="emit('update:searchValue', $event.target.value)"
        />
      </label>

      <button
        v-if="actionLabel"
        :class="['action-btn', `tone-${actionTone}`]"
        type="button"
        @click="emit('action')"
      >
        <IconlyIcon :name="actionIcon" decorative />
        <span>{{ actionLabel }}</span>
      </button>
    </div>
  </header>
</template>

<style scoped>
.page-header-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.page-header-title-row h1 {
  margin: 0;
  min-width: 0;
}
</style>
