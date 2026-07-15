<script setup>
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
      <h1 id="page-title">{{ title }}</h1>
      <p v-if="description" class="page-header-description">{{ description }}</p>
    </div>

    <div v-if="showSearch || actionLabel" class="page-header-tools">
      <label v-if="showSearch" class="search-shell page-header-search">
        <span class="material-symbols-outlined" aria-hidden="true">search</span>
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
        <span class="material-symbols-outlined" aria-hidden="true">{{ actionIcon }}</span>
        <span>{{ actionLabel }}</span>
      </button>
    </div>
  </header>
</template>
