<script setup>
const props = defineProps({
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
  <header class="page-header">
    <div class="page-header-copy">
      <p v-if="eyebrow" class="page-eyebrow">{{ eyebrow }}</p>
      <h1>{{ title }}</h1>
    </div>

    <div class="page-header-tools">
      <button class="icon-btn mobile-menu-trigger" @click="emit('menu')">
        <span class="material-symbols-outlined">menu</span>
      </button>

      <label v-if="showSearch" class="search-shell">
        <span class="material-symbols-outlined">search</span>
        <input
          :value="searchValue"
          type="text"
          :placeholder="searchPlaceholder"
          @input="emit('update:searchValue', $event.target.value)"
        />
      </label>

      <button v-if="actionLabel" :class="['action-btn', `tone-${actionTone}`]" @click="emit('action')">
        <span class="material-symbols-outlined">{{ actionIcon }}</span>
        <span>{{ actionLabel }}</span>
      </button>
    </div>
  </header>
</template>



