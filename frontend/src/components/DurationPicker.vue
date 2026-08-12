<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import IconlyIcon from './base/IconlyIcon.vue'
import { formatDurationFa } from '../utils/duration'
import { buildAnchoredPanelStyle } from '../utils/pickerPosition'

const props = defineProps({
  modelValue: { type: Number, default: 60 },
  placeholder: { type: String, default: 'انتخاب زمان تخمینی' },
  maxHours: { type: Number, default: 16 },
  minuteStep: { type: Number, default: 5 },
})

const emit = defineEmits(['update:modelValue'])

const root = ref(null)
const panel = ref(null)
const open = ref(false)
const panelStyle = ref({})
const draftHours = ref(1)
const draftMinutes = ref(0)

const hourOptions = computed(() =>
  Array.from({ length: Math.max(1, Number(props.maxHours) || 16) + 1 }, (_, index) => index),
)
const minuteOptions = computed(() => {
  const step = Math.max(1, Number(props.minuteStep) || 5)
  const values = []
  for (let minute = 0; minute < 60; minute += step) values.push(minute)
  return values
})

const presets = [
  { label: '۱۵ دقیقه', minutes: 15 },
  { label: '۳۰ دقیقه', minutes: 30 },
  { label: '۱ ساعت', minutes: 60 },
  { label: '۲ ساعت', minutes: 120 },
  { label: '۴ ساعت', minutes: 240 },
]

const displayValue = computed(() => {
  const total = Number(props.modelValue || 0)
  if (!total) return props.placeholder
  return formatDurationFa(total)
})

const draftTotal = computed(() => Number(draftHours.value || 0) * 60 + Number(draftMinutes.value || 0))

function syncDraftFromModel() {
  const total = Math.max(0, Number(props.modelValue) || 0)
  draftHours.value = Math.floor(total / 60)
  let minutes = total % 60
  const step = Math.max(1, Number(props.minuteStep) || 5)
  if (minutes % step !== 0) {
    minutes = Math.round(minutes / step) * step
    if (minutes >= 60) {
      draftHours.value += 1
      minutes = 0
    }
  }
  draftMinutes.value = minutes
}

function commit(totalMinutes, { closePanel = true } = {}) {
  const total = Math.max(0, Number(totalMinutes) || 0)
  if (total <= 0) return false
  draftHours.value = Math.floor(total / 60)
  draftMinutes.value = total % 60
  emit('update:modelValue', total)
  if (closePanel) close()
  return true
}

function buildPanelStyle() {
  if (!root.value || !panel.value) return
  const anchorWidth = root.value.getBoundingClientRect().width
  panelStyle.value = buildAnchoredPanelStyle(root.value, panel.value, {
    minWidth: 260,
    preferredWidth: Math.max(anchorWidth, 300),
    matchAnchorWidth: anchorWidth >= 280,
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
    if (draftTotal.value > 0) {
      emit('update:modelValue', draftTotal.value)
    }
    close()
    return
  }
  void openPanel()
}

function close() {
  open.value = false
}

function setDraftHours(hour) {
  draftHours.value = Number(hour) || 0
}

function setDraftMinutes(minute) {
  draftMinutes.value = Number(minute) || 0
}

function applyPreset(minutes) {
  commit(minutes, { closePanel: true })
}

function applyValue() {
  commit(draftTotal.value, { closePanel: true })
}

function onDocumentPointerDown(event) {
  if (!open.value) return
  const target = event.target
  if (root.value?.contains(target) || panel.value?.contains(target)) return
  // Save current draft when dismissing by outside tap
  if (draftTotal.value > 0) {
    emit('update:modelValue', draftTotal.value)
  }
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
  <div ref="root" class="duration-picker">
    <button class="duration-picker-trigger" type="button" @click.stop="toggleOpen">
      <span :class="['duration-picker-value', !modelValue && 'is-placeholder']">{{ displayValue }}</span>
      <IconlyIcon name="schedule" decorative />
    </button>
  </div>

  <Teleport to="body">
    <div
      v-if="open"
      ref="panel"
      class="picker-panel duration-picker-panel"
      :style="panelStyle"
      @pointerdown.stop
      @click.stop
    >
      <div class="picker-panel-head">
        <strong>زمان تخمینی</strong>
        <small>{{ formatDurationFa(draftTotal) }}</small>
      </div>

      <div class="duration-presets">
        <button
          v-for="item in presets"
          :key="item.minutes"
          type="button"
          :class="['duration-preset', Number(modelValue) === item.minutes && 'is-selected']"
          @click="applyPreset(item.minutes)"
        >
          {{ item.label }}
        </button>
      </div>

      <div class="time-picker-columns">
        <div class="time-picker-column">
          <small>ساعت</small>
          <div class="time-picker-scroll">
            <button
              v-for="hour in hourOptions"
              :key="`dh-${hour}`"
              type="button"
              :class="['time-picker-option', draftHours === hour && 'is-selected']"
              @click="setDraftHours(hour)"
            >
              {{ hour }}
            </button>
          </div>
        </div>
        <div class="time-picker-column">
          <small>دقیقه</small>
          <div class="time-picker-scroll">
            <button
              v-for="minute in minuteOptions"
              :key="`dm-${minute}`"
              type="button"
              :class="['time-picker-option', draftMinutes === minute && 'is-selected']"
              @click="setDraftMinutes(minute)"
            >
              {{ minute }}
            </button>
          </div>
        </div>
      </div>

      <div class="picker-panel-actions">
        <button type="button" class="action-btn tone-soft" @click="close">انصراف</button>
        <button type="button" class="action-btn tone-primary" :disabled="draftTotal <= 0" @click="applyValue">تأیید</button>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.duration-picker {
  width: 100%;
  min-width: 0;
  max-width: 100%;
}
.duration-picker-trigger {
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
.duration-picker-value {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.duration-picker-value.is-placeholder {
  color: #94a3b8;
  font-weight: 600;
}
</style>
