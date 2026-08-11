<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
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
        <IconlyIcon name="search" decorative />
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
        <IconlyIcon name="group" decorative />
        <span>شخص</span>
      </span>
      <div class="filter-field-control filter-select-wrap">
        <select class="filter-select" :value="person" @change="emit('update:person', $event.target.value)">
          <option value="">همه افراد</option>
          <option v-for="item in people" :key="item" :value="item">{{ item }}</option>
        </select>
        <IconlyIcon name="expand_more" class="filter-select-icon" decorative />
      </div>
    </label>

    <label class="field-shell compact-field filter-field">
      <span class="filter-field-label">
        <IconlyIcon name="event_upcoming" decorative />
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
        <IconlyIcon name="event_available" decorative />
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
      <IconlyIcon name="restart_alt" decorative />
      <span>پاک کردن</span>
    </button>
  </section>
</template>

<style scoped>
.modern-page-filters {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr)) auto;
  gap: 12px;
  align-items: end;
  width: 100%;
  max-width: none;
  margin: 0;
  padding: 0;
  background: transparent;
  border: 0;
  box-sizing: border-box;
}

.filter-field {
  display: grid;
  grid-template-rows: 16px 40px;
  align-items: stretch;
  gap: 6px;
  min-width: 0;
  width: 100%;
  min-height: 0;
  height: auto;
  padding: 0 !important;
  margin: 0;
  border-radius: 0;
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}

.filter-field-label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 16px;
  line-height: 16px;
  color: var(--muted, #5c6780);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0;
}

.filter-field-label .iconly-shell {
  font-size: 14px;
  color: var(--primary, #34908B);
}

.filter-field-control {
  position: relative;
  width: 100%;
  min-width: 0;
  height: 40px;
  min-height: 40px;
  max-height: 40px;
}

.filter-input,
.filter-select {
  box-sizing: border-box;
  width: 100%;
  height: 40px !important;
  min-height: 40px !important;
  max-height: 40px !important;
  border: 0 !important;
  border-radius: 10px !important;
  background: #e4f4f2 !important;
  padding: 0 12px !important;
  color: var(--text, #2a344c);
  font: inherit;
  font-size: 0.82rem;
  line-height: 40px;
  outline: none;
  box-shadow: none !important;
}

.filter-input::placeholder {
  color: rgba(90, 102, 128, 0.7);
}

.filter-input:focus,
.filter-select:focus,
.modern-page-filters :deep(.shamsi-picker-input:focus) {
  border: 0 !important;
  box-shadow: none;
  background: #f7fbfa !important;
}

.filter-select {
  appearance: none;
  padding-inline: 12px 36px !important;
  cursor: pointer;
  line-height: normal;
}

.filter-select-wrap {
  position: relative;
  height: 40px;
}

.filter-select-wrap :deep(.filter-select-icon) {
  position: absolute;
  inset-inline-end: 10px;
  inset-inline-start: auto;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
  color: #34908B;
  pointer-events: none;
  font-size: 16px;
  width: 16px;
  height: 16px;
}

.modern-filter-reset {
  box-sizing: border-box;
  align-self: end;
  height: 40px !important;
  min-height: 40px !important;
  max-height: 40px !important;
  border-radius: 10px;
  padding: 0 14px !important;
  background: #e4f4f2 !important;
  border: 0 !important;
  font-size: 0.8rem;
  margin: 0;
}

.modern-filter-reset .iconly-shell {
  font-size: 16px;
}

.modern-page-filters :deep(.shamsi-picker) {
  width: 100%;
  height: 40px;
}

.modern-page-filters :deep(.shamsi-picker-input-wrap) {
  box-sizing: border-box;
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
  height: 40px !important;
  min-height: 40px !important;
  max-height: 40px !important;
  border: 0 !important;
  border-radius: 10px !important;
  background: #e4f4f2 !important;
  box-shadow: none !important;
  padding-inline: 12px 36px !important;
  padding-block: 0 !important;
  margin: 0 !important;
}

.modern-page-filters :deep(.shamsi-picker-input) {
  box-sizing: border-box;
  height: 100% !important;
  min-height: 0 !important;
  max-height: 100% !important;
  width: 100%;
  padding: 0 !important;
  margin: 0 !important;
  background: transparent !important;
  border: 0 !important;
  font-size: 0.82rem;
  line-height: 40px;
}

.modern-page-filters :deep(.shamsi-picker-toggle) {
  position: absolute;
  inset-inline-end: 5px;
  inset-inline-start: auto;
  top: 50%;
  transform: translateY(-50%);
  width: 26px;
  height: 26px;
  border-radius: 8px;
  color: #34908B;
  background: #f3f9f7 !important;
  z-index: 2;
  padding: 0;
  margin: 0;
}

@media (max-width: 1320px) {
  .modern-page-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .modern-page-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 420px) {
  .modern-page-filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
