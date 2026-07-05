<script setup>
import ShamsiDatePicker from './ShamsiDatePicker.vue'

defineProps({
  query: { type: String, default: '' },
  person: { type: String, default: '' },
  startDate: { type: String, default: '' },
  endDate: { type: String, default: '' },
  people: { type: Array, default: () => [] },
  dense: { type: Boolean, default: false },
})

const emit = defineEmits(['update:query', 'update:person', 'update:startDate', 'update:endDate', 'reset'])
</script>

<template>
  <section :class="['page-filters', dense && 'is-dense']">
    <label class="field-shell compact-field">
      <span>جستجو</span>
      <input :value="query" type="text" placeholder="نام، عنوان، شناسه..." @input="emit('update:query', $event.target.value)" />
    </label>

    <label class="field-shell compact-field">
      <span>شخص</span>
      <select :value="person" @change="emit('update:person', $event.target.value)">
        <option value="">همه افراد</option>
        <option v-for="item in people" :key="item" :value="item">{{ item }}</option>
      </select>
    </label>

    <label class="field-shell compact-field">
      <span>از تاریخ</span>
      <ShamsiDatePicker
        :model-value="startDate"
        model-type="iso"
        placeholder="1405/03/29"
        @update:model-value="emit('update:startDate', $event)"
      />
    </label>

    <label class="field-shell compact-field">
      <span>تا تاریخ</span>
      <ShamsiDatePicker
        :model-value="endDate"
        model-type="iso"
        placeholder="1405/04/10"
        @update:model-value="emit('update:endDate', $event)"
      />
    </label>

    <button class="action-btn tone-soft filter-reset-btn" type="button" @click="emit('reset')">
      <span class="material-symbols-outlined">restart_alt</span>
      <span>پاک کردن</span>
    </button>
  </section>
</template>
