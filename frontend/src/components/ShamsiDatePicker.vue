<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  getJalaliMonthLabel,
  getMonthMatrix,
  getPersianWeekdays,
  getTodayJalali,
  isoToJalali,
  jalaliToIso,
  normalizeDigits,
  parseJalali,
  shiftJalaliMonth,
} from '../utils/jalali'

const props = defineProps({
  modelValue: { type: String, default: '' },
  modelType: { type: String, default: 'iso' },
  placeholder: { type: String, default: 'انتخاب تاریخ' },
})

const emit = defineEmits(['update:modelValue'])

const root = ref(null)
const open = ref(false)
const inputValue = ref('')

function getInitialMonth() {
  if (props.modelValue) {
    if (props.modelType === 'jalali') {
      const parsed = parseJalali(props.modelValue)
      if (parsed) return { jy: parsed.jy, jm: parsed.jm }
    } else {
      const jalali = parseJalali(isoToJalali(props.modelValue))
      if (jalali) return { jy: jalali.jy, jm: jalali.jm }
    }
  }

  const today = getTodayJalali()
  return { jy: today.jy, jm: today.jm }
}

const viewMonth = ref(getInitialMonth())

const selectedJalali = computed(() => {
  if (!props.modelValue) return null
  if (props.modelType === 'jalali') return parseJalali(props.modelValue)
  return parseJalali(isoToJalali(props.modelValue))
})

const weeks = computed(() => getMonthMatrix(viewMonth.value.jy, viewMonth.value.jm))
const weekdays = getPersianWeekdays()
const monthLabel = computed(() => getJalaliMonthLabel(viewMonth.value.jy, viewMonth.value.jm))

watch(
  () => props.modelValue,
  (value) => {
    inputValue.value = props.modelType === 'jalali' ? normalizeDigits(value) : isoToJalali(value)
    const parsed = parseJalali(inputValue.value)
    if (parsed) {
      viewMonth.value = { jy: parsed.jy, jm: parsed.jm }
    }
  },
  { immediate: true },
)

function emitValue(jalaliValue) {
  emit('update:modelValue', props.modelType === 'jalali' ? jalaliValue : jalaliToIso(jalaliValue))
}

function toggleOpen() {
  open.value = !open.value
}

function close() {
  open.value = false
}

function selectDay(day) {
  emitValue(day.formatted)
  inputValue.value = day.formatted
  close()
}

function clearValue() {
  emit('update:modelValue', '')
  inputValue.value = ''
  close()
}

function prevMonth() {
  viewMonth.value = shiftJalaliMonth(viewMonth.value.jy, viewMonth.value.jm, -1)
}

function nextMonth() {
  viewMonth.value = shiftJalaliMonth(viewMonth.value.jy, viewMonth.value.jm, 1)
}

function applyTypedValue() {
  const parsed = parseJalali(inputValue.value)
  if (!parsed) {
    inputValue.value = props.modelType === 'jalali' ? normalizeDigits(props.modelValue) : isoToJalali(props.modelValue)
    return
  }

  const normalized = `${parsed.jy}/${String(parsed.jm).padStart(2, '0')}/${String(parsed.jd).padStart(2, '0')}`
  inputValue.value = normalized
  viewMonth.value = { jy: parsed.jy, jm: parsed.jm }
  emitValue(normalized)
}

function onDocumentClick(event) {
  if (root.value && !root.value.contains(event.target)) {
    close()
  }
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
})
</script>

<template>
  <div ref="root" class="shamsi-picker">
    <div class="shamsi-picker-input-wrap">
      <input
        v-model="inputValue"
        class="shamsi-picker-input"
        type="text"
        inputmode="numeric"
        dir="ltr"
        :placeholder="placeholder"
        @focus="open = true"
        @blur="applyTypedValue"
      />
      <button class="shamsi-picker-toggle" type="button" @click.stop="toggleOpen">
        <span class="material-symbols-outlined">calendar_month</span>
      </button>
    </div>

    <div v-if="open" class="shamsi-picker-panel">
      <div class="shamsi-picker-head">
        <button type="button" class="icon-btn" @click="nextMonth">
          <span class="material-symbols-outlined">chevron_right</span>
        </button>
        <strong>{{ monthLabel }}</strong>
        <button type="button" class="icon-btn" @click="prevMonth">
          <span class="material-symbols-outlined">chevron_left</span>
        </button>
      </div>

      <div class="shamsi-picker-weekdays">
        <span v-for="item in weekdays" :key="item">{{ item }}</span>
      </div>

      <div class="shamsi-picker-grid">
        <template v-for="(week, weekIndex) in weeks" :key="weekIndex">
          <button
            v-for="(day, dayIndex) in week"
            :key="`${weekIndex}-${dayIndex}`"
            type="button"
            :disabled="!day"
            :class="[
              'shamsi-picker-day',
              day && selectedJalali && selectedJalali.jy === day.jalali.jy && selectedJalali.jm === day.jalali.jm && selectedJalali.jd === day.jalali.jd && 'is-selected',
              !day && 'is-empty',
            ]"
            @click="day && selectDay(day)"
          >
            {{ day?.day || '' }}
          </button>
        </template>
      </div>

      <div class="shamsi-picker-actions">
        <button type="button" class="action-btn tone-soft" @click="clearValue">پاک کردن</button>
      </div>
    </div>
  </div>
</template>
