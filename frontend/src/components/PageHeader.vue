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
  <section class="page-header">
    <div class="page-header-copy">
      <span v-if="eyebrow" class="page-eyebrow">{{ eyebrow }}</span>
      <h1>{{ title }}</h1>
      <p v-if="description" class="page-header-description">{{ description }}</p>
    </div>

    <div v-if="showSearch || actionLabel" class="page-header-tools">
      <label v-if="showSearch" class="search-shell search-shell-wide">
        <span class="material-symbols-outlined">search</span>
        <input
          :value="searchValue"
          type="text"
          :placeholder="searchPlaceholder || 'جستجو...'"
          @input="emit('update:searchValue', $event.target.value)"
        />
      </label>

      <button v-if="actionLabel" :class="['action-btn', `tone-${actionTone}`]" type="button" @click="emit('action')">
        <span class="material-symbols-outlined">{{ actionIcon }}</span>
        <span>{{ actionLabel }}</span>
      </button>
    </div>
  </section>
</template>
