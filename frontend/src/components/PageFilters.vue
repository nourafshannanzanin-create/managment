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
  <section :class="['page-filters', 'modern-page-filters', dense && 'is-dense']">
    <label class="field-shell compact-field filter-field is-search">
      <span class="filter-field-label">
        <span class="material-symbols-outlined">search</span>
        <span>جستجو</span>
      </span>
      <div class="filter-field-control">
        <input
          class="filter-input"
          :value="query"
          type="text"
          placeholder="نام، عنوان، شناسه..."
          @input="emit('update:query', $event.target.value)"
        />
      </div>
    </label>

    <label class="field-shell compact-field filter-field">
      <span class="filter-field-label">
        <span class="material-symbols-outlined">group</span>
        <span>شخص</span>
      </span>
      <div class="filter-field-control filter-select-wrap">
        <select class="filter-select" :value="person" @change="emit('update:person', $event.target.value)">
          <option value="">همه افراد</option>
          <option v-for="item in people" :key="item" :value="item">{{ item }}</option>
        </select>
        <span class="material-symbols-outlined filter-select-icon">expand_more</span>
      </div>
    </label>

    <label class="field-shell compact-field filter-field">
      <span class="filter-field-label">
        <span class="material-symbols-outlined">event_upcoming</span>
        <span>از تاریخ</span>
      </span>
      <div class="filter-field-control">
        <ShamsiDatePicker
          :model-value="startDate"
          model-type="iso"
          placeholder="1405/03/29"
          @update:model-value="emit('update:startDate', $event)"
        />
      </div>
    </label>

    <label class="field-shell compact-field filter-field">
      <span class="filter-field-label">
        <span class="material-symbols-outlined">event_available</span>
        <span>تا تاریخ</span>
      </span>
      <div class="filter-field-control">
        <ShamsiDatePicker
          :model-value="endDate"
          model-type="iso"
          placeholder="1405/04/10"
          @update:model-value="emit('update:endDate', $event)"
        />
      </div>
    </label>

    <button class="action-btn tone-soft filter-reset-btn modern-filter-reset" type="button" @click="emit('reset')">
      <span class="material-symbols-outlined">restart_alt</span>
      <span>پاک کردن</span>
    </button>
  </section>
</template>

<style scoped>
.modern-page-filters {
  display: grid;
  grid-template-columns: minmax(240px, 1.35fr) minmax(180px, 0.9fr) repeat(2, minmax(180px, 0.95fr)) auto;
  gap: 12px;
  align-items: stretch;
}

.filter-field {
  display: grid;
  gap: 10px;
  min-height: 84px;
  padding: 14px 16px;
  border-radius: 22px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 249, 252, 0.95)),
    var(--surface);
  border-color: rgba(36, 59, 107, 0.08);
}

.filter-field-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.04em;
}

.filter-field-label .material-symbols-outlined {
  font-size: 18px;
  color: var(--primary);
}

.filter-field-control {
  position: relative;
}

.filter-input,
.filter-select {
  width: 100%;
  min-height: 46px;
  border: 1px solid rgba(36, 59, 107, 0.1);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.85);
  padding: 0 14px;
  color: var(--text);
  font: inherit;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
}

.filter-input::placeholder {
  color: rgba(82, 96, 126, 0.78);
}

.filter-input:focus,
.filter-select:focus,
.modern-page-filters :deep(.shamsi-picker-input:focus) {
  border-color: rgba(72, 103, 183, 0.4);
  box-shadow: 0 0 0 4px rgba(72, 103, 183, 0.1);
  background: #fff;
}

.filter-select {
  appearance: none;
  padding-inline: 14px 42px;
  cursor: pointer;
}

.filter-select-wrap {
  position: relative;
}

.filter-select-icon {
  position: absolute;
  inset-inline-start: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--muted);
  pointer-events: none;
  font-size: 20px;
}

.modern-filter-reset {
  align-self: stretch;
  min-height: 84px;
  border-radius: 22px;
  padding-inline: 18px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(243, 246, 250, 0.95)),
    var(--surface);
  border: 1px dashed rgba(36, 59, 107, 0.18);
}

.modern-filter-reset .material-symbols-outlined {
  font-size: 20px;
}

.modern-page-filters :deep(.shamsi-picker),
.modern-page-filters :deep(.shamsi-picker-input-wrap) {
  width: 100%;
}

.modern-page-filters :deep(.shamsi-picker-input-wrap) {
  min-height: 46px;
  border: 1px solid rgba(36, 59, 107, 0.1);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.85);
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
}

.modern-page-filters :deep(.shamsi-picker-input) {
  min-height: 44px;
  padding-inline: 14px 48px;
  background: transparent;
  border: 0;
}

.modern-page-filters :deep(.shamsi-picker-toggle) {
  inset-inline-start: 6px;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  color: var(--primary);
  background: rgba(72, 103, 183, 0.08);
}

.modern-page-filters :deep(.shamsi-picker-panel) {
  margin-top: 10px;
  border-radius: 20px;
}

@media (max-width: 1320px) {
  .modern-page-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .modern-filter-reset {
    min-height: 58px;
  }
}

@media (max-width: 760px) {
  .modern-page-filters {
    grid-template-columns: minmax(0, 1fr);
  }

  .filter-field,
  .modern-filter-reset {
    min-height: auto;
  }
}
</style>
