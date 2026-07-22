<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
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
  restrictToCurrentMonth: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const root = ref(null)
const panel = ref(null)
const open = ref(false)
const inputValue = ref('')
const panelStyle = ref({})
const todayJalali = getTodayJalali()
const currentMonth = { jy: todayJalali.jy, jm: todayJalali.jm }

function compareJalali(a, b) {
  if (a.jy !== b.jy) return a.jy - b.jy
  if (a.jm !== b.jm) return a.jm - b.jm
  return a.jd - b.jd
}

function isOutsideViewMonth(value) {
  return value.jy !== viewMonth.value.jy || value.jm !== viewMonth.value.jm
}

function isOutOfSelectableRange(value) {
  if (!props.restrictToCurrentMonth) return false
  return value.jy !== currentMonth.jy || value.jm !== currentMonth.jm
}

function getInitialMonth() {
  if (props.modelValue) {
    const selected = props.modelType === 'jalali' ? parseJalali(props.modelValue) : parseJalali(isoToJalali(props.modelValue))
    if (selected) return { jy: selected.jy, jm: selected.jm }
  }
  return { ...currentMonth }
}

const viewMonth = ref(getInitialMonth())

const selectedJalali = computed(() => {
  if (!props.modelValue) return null
  if (props.modelType === 'jalali') return parseJalali(props.modelValue)
  return parseJalali(isoToJalali(props.modelValue))
})

const weeks = computed(() =>
  getMonthMatrix(viewMonth.value.jy, viewMonth.value.jm).map((week) =>
    week.map((day) =>
      day
        ? {
            ...day,
            disabled: isOutsideViewMonth(day.jalali) || isOutOfSelectableRange(day.jalali),
          }
        : null,
    ),
  ),
)
const weekdays = getPersianWeekdays()
const monthLabel = computed(() => getJalaliMonthLabel(viewMonth.value.jy, viewMonth.value.jm))
const canPrevMonth = computed(() => !props.restrictToCurrentMonth)
const canNextMonth = computed(() => !props.restrictToCurrentMonth)

watch(
  () => props.modelValue,
  (value) => {
    inputValue.value = props.modelType === 'jalali' ? normalizeDigits(value) : isoToJalali(value)
    viewMonth.value = getInitialMonth()
  },
  { immediate: true },
)

function emitValue(jalaliValue) {
  emit('update:modelValue', props.modelType === 'jalali' ? jalaliValue : jalaliToIso(jalaliValue))
}

function isToday(day) {
  if (!day) return false
  return (
    day.jalali.jy === todayJalali.jy &&
    day.jalali.jm === todayJalali.jm &&
    day.jalali.jd === todayJalali.jd
  )
}

function buildPanelStyle() {
  if (!root.value || !panel.value) return
  const rect = root.value.getBoundingClientRect()
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  const mobile = viewportWidth <= 760
  const sidePadding = mobile ? 8 : 12
  const width = Math.max(220, Math.min(rect.width, viewportWidth - sidePadding * 2))
  const left = Math.max(sidePadding, Math.min(rect.left, viewportWidth - width - sidePadding))
  const top = rect.bottom + 8
  const maxHeight = Math.max(220, viewportHeight - top - sidePadding)

  panelStyle.value = {
    position: 'fixed',
    top: `${top}px`,
    left: `${left}px`,
    right: 'auto',
    bottom: 'auto',
    width: `${width}px`,
    maxWidth: `calc(100vw - ${sidePadding * 2}px)`,
    maxHeight: `${maxHeight}px`,
    overflowY: 'auto',
    zIndex: '2200',
  }
}

async function openPanel() {
  open.value = true
  await nextTick()
  buildPanelStyle()
}

function toggleOpen() {
  if (open.value) {
    close()
    return
  }
  void openPanel()
}

function close() {
  open.value = false
}

function selectDay(day) {
  if (day.disabled) return
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
  if (!canPrevMonth.value) return
  viewMonth.value = shiftJalaliMonth(viewMonth.value.jy, viewMonth.value.jm, -1)
}

function nextMonth() {
  if (!canNextMonth.value) return
  viewMonth.value = shiftJalaliMonth(viewMonth.value.jy, viewMonth.value.jm, 1)
}

function applyTypedValue() {
  const parsed = parseJalali(inputValue.value)
  if (!parsed) {
    inputValue.value = props.modelType === 'jalali' ? normalizeDigits(props.modelValue) : isoToJalali(props.modelValue)
    return
  }
  if (isOutOfSelectableRange(parsed)) {
    inputValue.value = props.modelType === 'jalali' ? normalizeDigits(props.modelValue) : isoToJalali(props.modelValue)
    return
  }

  const normalized = `${parsed.jy}/${String(parsed.jm).padStart(2, '0')}/${String(parsed.jd).padStart(2, '0')}`
  inputValue.value = normalized
  viewMonth.value = { jy: parsed.jy, jm: parsed.jm }
  emitValue(normalized)
}

function onDocumentClick(event) {
  const target = event.target
  if (root.value?.contains(target) || panel.value?.contains(target)) return
  close()
}

function onViewportChange() {
  if (!open.value) return
  buildPanelStyle()
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  window.addEventListener('resize', onViewportChange)
  window.addEventListener('scroll', onViewportChange, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
  window.removeEventListener('resize', onViewportChange)
  window.removeEventListener('scroll', onViewportChange, true)
})

watch(open, async (isOpen) => {
  if (!isOpen) return
  await nextTick()
  buildPanelStyle()
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
        @focus="openPanel"
        @blur="applyTypedValue"
      />
      <button class="shamsi-picker-toggle" type="button" @click.stop="toggleOpen">
        <IconlyIcon name="calendar_month" decorative />
      </button>
    </div>
  </div>

  <Teleport to="body">
    <div v-if="open" ref="panel" class="shamsi-picker-panel shamsi-picker-panel-teleport" :style="panelStyle">
      <div class="shamsi-picker-head">
        <button type="button" class="icon-btn" :disabled="!canNextMonth" @click="nextMonth">
          <IconlyIcon name="chevron_right" decorative />
        </button>
        <strong>{{ monthLabel }}</strong>
        <button type="button" class="icon-btn" :disabled="!canPrevMonth" @click="prevMonth">
          <IconlyIcon name="chevron_left" decorative />
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
              day && isToday(day) && 'is-today',
              day?.disabled && 'is-disabled',
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
  </Teleport>
</template>
