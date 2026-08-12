<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import IconlyIcon from './base/IconlyIcon.vue'
import { formatTimeDisplay, padTimePart, parseTimeValue } from '../utils/duration'
import { buildAnchoredPanelStyle } from '../utils/pickerPosition'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: 'انتخاب ساعت' },
  minuteStep: { type: Number, default: 5 },
  clearable: { type: Boolean, default: true },
})

const emit = defineEmits(['update:modelValue'])

const root = ref(null)
const panel = ref(null)
const open = ref(false)
const panelStyle = ref({})
const draftHour = ref(17)
const draftMinute = ref(0)

const hours = Array.from({ length: 24 }, (_, index) => index)
const minutes = computed(() => {
  const step = Math.max(1, Number(props.minuteStep) || 5)
  const values = []
  for (let minute = 0; minute < 60; minute += step) values.push(minute)
  if (!values.includes(draftMinute.value)) values.push(draftMinute.value)
  return values.sort((a, b) => a - b)
})

const displayValue = computed(() =>
  props.modelValue ? formatTimeDisplay(props.modelValue) : props.placeholder,
)

const draftValue = computed(
  () => `${padTimePart(draftHour.value)}:${padTimePart(draftMinute.value)}`,
)

function syncDraftFromModel() {
  const parsed = parseTimeValue(props.modelValue, '17:00')
  const [hour, minute] = parsed.split(':').map(Number)
  draftHour.value = hour
  draftMinute.value = minute
}

function buildPanelStyle() {
  if (!root.value || !panel.value) return
  panelStyle.value = buildAnchoredPanelStyle(root.value, panel.value, {
    minWidth: 220,
    preferredWidth: Math.max(root.value.getBoundingClientRect().width, 240),
    matchAnchorWidth: root.value.getBoundingClientRect().width >= 220,
  })
}

async function openPanel() {
  syncDraftFromModel()
  open.value = true
  await nextTick()
  buildPanelStyle()
  requestAnimationFrame(buildPanelStyle)
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

function setDraftHour(hour) {
  draftHour.value = Number(hour) || 0
}

function setDraftMinute(minute) {
  draftMinute.value = Number(minute) || 0
}

function applyValue() {
  emit('update:modelValue', draftValue.value)
  close()
}

function clearValue() {
  emit('update:modelValue', '')
  close()
}

function onDocumentPointerDown(event) {
  if (!open.value) return
  const target = event.target
  if (root.value?.contains(target) || panel.value?.contains(target)) return
  emit('update:modelValue', draftValue.value)
  close()
}

function onViewportChange() {
  if (!open.value) return
  buildPanelStyle()
}

onMounted(() => {
  document.addEventListener('pointerdown', onDocumentPointerDown, true)
  window.addEventListener('resize', onViewportChange)
  window.addEventListener('scroll', onViewportChange, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onDocumentPointerDown, true)
  window.removeEventListener('resize', onViewportChange)
  window.removeEventListener('scroll', onViewportChange, true)
})

watch(
  () => props.modelValue,
  () => {
    if (!open.value) syncDraftFromModel()
  },
  { immediate: true },
)
</script>

<template>
  <div ref="root" class="time-picker">
    <button class="time-picker-trigger" type="button" @click.stop="toggleOpen">
      <span :class="['time-picker-value', !modelValue && 'is-placeholder']">{{ displayValue }}</span>
      <IconlyIcon name="schedule" decorative />
    </button>
  </div>

  <Teleport to="body">
    <div
      v-if="open"
      ref="panel"
      class="picker-panel time-picker-panel"
      :style="panelStyle"
      @pointerdown.stop
      @click.stop
    >
      <div class="picker-panel-head">
        <strong>انتخاب ساعت</strong>
        <small>{{ formatTimeDisplay(draftValue) }}</small>
      </div>
      <div class="time-picker-columns">
        <div class="time-picker-column">
          <small>ساعت</small>
          <div class="time-picker-scroll">
            <button
              v-for="hour in hours"
              :key="`h-${hour}`"
              type="button"
              :class="['time-picker-option', draftHour === hour && 'is-selected']"
              @click="setDraftHour(hour)"
            >
              {{ padTimePart(hour) }}
            </button>
          </div>
        </div>
        <div class="time-picker-column">
          <small>دقیقه</small>
          <div class="time-picker-scroll">
            <button
              v-for="minute in minutes"
              :key="`m-${minute}`"
              type="button"
              :class="['time-picker-option', draftMinute === minute && 'is-selected']"
              @click="setDraftMinute(minute)"
            >
              {{ padTimePart(minute) }}
            </button>
          </div>
        </div>
      </div>
      <div class="picker-panel-actions">
        <button v-if="clearable" type="button" class="action-btn tone-soft" @click="clearValue">پاک کردن</button>
        <button type="button" class="action-btn tone-primary" @click="applyValue">تأیید</button>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.time-picker {
  width: 100%;
  min-width: 0;
  max-width: 100%;
}
.time-picker-trigger {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  min-height: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 12px;
  border: 1px solid rgba(52, 144, 139, 0.16);
  background: #fff;
  cursor: pointer;
  color: #134e4a;
  font-weight: 700;
}
.time-picker-value {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.time-picker-value.is-placeholder {
  color: #94a3b8;
  font-weight: 600;
}
</style>
