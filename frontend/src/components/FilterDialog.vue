<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { reactive, watch } from 'vue'

import BaseModal from './BaseModal.vue'
import ShamsiDatePicker from './ShamsiDatePicker.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: 'فیلترها' },
  people: { type: Array, default: () => [] },
  filters: {
    type: Object,
    default: () => ({ query: '', person: '', startDate: '', endDate: '' }),
  },
})

const emit = defineEmits(['close', 'apply', 'reset'])

const draft = reactive({
  query: '',
  person: '',
  startDate: '',
  endDate: '',
})

watch(
  () => props.filters,
  (value) => {
    Object.assign(draft, {
      query: value?.query || '',
      person: value?.person || '',
      startDate: value?.startDate || '',
      endDate: value?.endDate || '',
    })
  },
  { immediate: true, deep: true },
)

function apply() {
  emit('apply', { ...draft })
}

function reset() {
  Object.assign(draft, { query: '', person: '', startDate: '', endDate: '' })
  emit('reset')
}
</script>

<template>
  <BaseModal :open="open" size="default" @close="emit('close')">
    <div class="modal-headline">
      <h2>{{ title }}</h2>
      <p>ویژگی‌های موردنظر را وارد کنید و سپس تایید بزنید.</p>
    </div>

    <div class="modal-grid two-col">
      <label class="field-shell">
        <span>جستجو</span>
        <input v-model="draft.query" type="text" placeholder="جستجو..." />
      </label>

      <label class="field-shell">
        <span>شخص</span>
        <select v-model="draft.person">
          <option value="">همه افراد</option>
          <option v-for="item in people" :key="item" :value="item">{{ item }}</option>
        </select>
      </label>

      <label class="field-shell">
        <span>از تاریخ</span>
        <ShamsiDatePicker v-model="draft.startDate" model-type="iso" placeholder="1405/03/29" />
      </label>

      <label class="field-shell">
        <span>تا تاریخ</span>
        <ShamsiDatePicker v-model="draft.endDate" model-type="iso" placeholder="1405/04/10" />
      </label>
    </div>

    <div class="modal-actions">
      <button class="action-btn tone-soft" type="button" @click="reset">
        <IconlyIcon name="restart_alt" decorative />
        <span>پاک کردن</span>
      </button>
      <button class="action-btn tone-primary" type="button" @click="apply">
        <IconlyIcon name="task_alt" decorative />
        <span>تایید فیلتر</span>
      </button>
    </div>
  </BaseModal>
</template>
