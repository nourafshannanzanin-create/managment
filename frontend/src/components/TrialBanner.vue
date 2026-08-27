<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  active: { type: Boolean, default: false },
  trialEndsAt: { type: String, default: '' },
  trialHours: { type: [Number, String], default: 24 },
})

const emit = defineEmits(['expired'])

const nowTick = ref(Date.now())
let timer = null

function toFaDigits(value) {
  return String(value ?? '').replace(/\d/g, (digit) => '۰۱۲۳۴۵۶۷۸۹'[digit] || digit)
}

function formatCountdown(totalSeconds) {
  const safe = Math.max(0, Number(totalSeconds) || 0)
  const hours = Math.floor(safe / 3600)
  const minutes = Math.floor((safe % 3600) / 60)
  const seconds = safe % 60
  const pad = (n) => String(n).padStart(2, '0')
  return toFaDigits(`${pad(hours)}:${pad(minutes)}:${pad(seconds)}`)
}

const endsAtMs = computed(() => {
  const parsed = Date.parse(props.trialEndsAt || '')
  return Number.isFinite(parsed) ? parsed : 0
})

const remainingSeconds = computed(() => {
  if (!endsAtMs.value) return 0
  return Math.max(0, Math.floor((endsAtMs.value - nowTick.value) / 1000))
})

const progressPercent = computed(() => {
  const totalSeconds = Math.max((Number(props.trialHours) || 24) * 3600, 1)
  return Math.min(100, Math.max(0, (remainingSeconds.value / totalSeconds) * 100))
})

const bannerText = computed(
  () => `زمان باقی‌مانده تا اتمام استفاده رایگان: ${formatCountdown(remainingSeconds.value)}`,
)

function stop() {
  if (timer) {
    window.clearInterval(timer)
    timer = null
  }
}

function start() {
  stop()
  nowTick.value = Date.now()
  timer = window.setInterval(() => {
    nowTick.value = Date.now()
  }, 1000)
}

watch(
  () => props.active,
  (active) => {
    if (active) start()
    else stop()
  },
  { immediate: true },
)

watch(remainingSeconds, (value, previous) => {
  if ((previous ?? 0) > 0 && value <= 0) emit('expired')
})

onMounted(() => {
  if (props.active) start()
})

onUnmounted(stop)
</script>

<template>
  <div v-if="active && remainingSeconds > 0" class="global-trial-banner" role="status" aria-live="polite">
    <div class="global-trial-banner__content">
      <IconlyIcon name="calendar" decorative />
      <strong>{{ bannerText }}</strong>
    </div>
    <div class="global-trial-banner__track" aria-hidden="true">
      <span class="global-trial-banner__fill" :style="{ width: `${progressPercent}%` }" />
    </div>
  </div>
</template>
