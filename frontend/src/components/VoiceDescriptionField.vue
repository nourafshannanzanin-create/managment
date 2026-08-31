<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  voiceFile: { type: [File, Object, null], default: null },
  voiceUrl: { type: String, default: '' },
  label: { type: String, default: 'توضیحات' },
  placeholder: { type: String, default: 'متن را بنویسید یا پیام صوتی ضبط کنید.' },
  rows: { type: Number, default: 4 },
  disabled: { type: Boolean, default: false },
  required: { type: Boolean, default: false },
  error: { type: Boolean, default: false },
  hint: { type: String, default: 'می‌توانید متن بنویسید یا پیام صوتی ضبط کنید.' },
})

const emit = defineEmits(['update:modelValue', 'update:voiceFile', 'clear-voice-url'])

const textareaRef = ref(null)
const canvasRef = ref(null)
const audioRef = ref(null)

const recording = ref(false)
const preparing = ref(false)
const playing = ref(false)
const elapsedMs = ref(0)
const durationMs = ref(0)
const playProgress = ref(0)
const localError = ref('')
const localPreviewUrl = ref('')

let mediaRecorder = null
let mediaStream = null
let audioContext = null
let analyser = null
let rafId = 0
let timerId = 0
let chunks = []

const hasLocalVoice = computed(() => Boolean(props.voiceFile || localPreviewUrl.value))
const hasRemoteVoice = computed(() => Boolean(props.voiceUrl) && !hasLocalVoice.value)
const hasVoice = computed(() => hasLocalVoice.value || hasRemoteVoice.value)
const activeAudioUrl = computed(() => localPreviewUrl.value || props.voiceUrl || '')

const elapsedLabel = computed(() => formatClock(elapsedMs.value))
const durationLabel = computed(() => formatClock(durationMs.value || elapsedMs.value))

function formatClock(ms) {
  const total = Math.max(0, Math.floor(Number(ms || 0) / 1000))
  const m = String(Math.floor(total / 60)).padStart(2, '0')
  const s = String(total % 60).padStart(2, '0')
  return `${m}:${s}`
}

function revokePreview() {
  if (localPreviewUrl.value && localPreviewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(localPreviewUrl.value)
  }
  localPreviewUrl.value = ''
}

function stopTracks() {
  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop())
    mediaStream = null
  }
}

function stopAnalyser() {
  if (rafId) cancelAnimationFrame(rafId)
  rafId = 0
  if (audioContext) {
    audioContext.close().catch(() => {})
    audioContext = null
  }
  analyser = null
}

function clearTimers() {
  if (timerId) clearInterval(timerId)
  timerId = 0
}

function drawIdleWave() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  const width = canvas.clientWidth || 280
  const height = canvas.clientHeight || 56
  canvas.width = width * dpr
  canvas.height = height * dpr
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, width, height)
  const bars = 36
  const gap = 3
  const barWidth = (width - gap * (bars - 1)) / bars
  for (let i = 0; i < bars; i += 1) {
    const amp = 0.18 + Math.sin(i * 0.45) * 0.08
    const h = Math.max(4, height * amp)
    const x = i * (barWidth + gap)
    const y = (height - h) / 2
    ctx.fillStyle = 'rgba(52, 144, 139, 0.28)'
    ctx.beginPath()
    ctx.roundRect(x, y, barWidth, h, 3)
    ctx.fill()
  }
}

function drawLiveWave() {
  const canvas = canvasRef.value
  if (!canvas || !analyser) return
  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  const width = canvas.clientWidth || 280
  const height = canvas.clientHeight || 56
  canvas.width = width * dpr
  canvas.height = height * dpr
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

  const buffer = new Uint8Array(analyser.frequencyBinCount)
  const paint = () => {
    analyser.getByteFrequencyData(buffer)
    ctx.clearRect(0, 0, width, height)
    const bars = 42
    const gap = 2.5
    const barWidth = (width - gap * (bars - 1)) / bars
    for (let i = 0; i < bars; i += 1) {
      const index = Math.floor((i / bars) * buffer.length)
      const value = buffer[index] / 255
      const h = Math.max(4, value * height * 0.92)
      const x = i * (barWidth + gap)
      const y = (height - h) / 2
      const alpha = 0.35 + value * 0.55
      ctx.fillStyle = `rgba(31, 92, 89, ${alpha})`
      ctx.beginPath()
      ctx.roundRect(x, y, barWidth, h, 3)
      ctx.fill()
    }
    rafId = requestAnimationFrame(paint)
  }
  paint()
}

async function startRecording() {
  if (props.disabled || recording.value || preparing.value) return
  localError.value = ''
  preparing.value = true
  try {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error('مرورگر از ضبط صدا پشتیبانی نمی‌کند.')
    }
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    })
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : ''
    mediaRecorder = mimeType ? new MediaRecorder(mediaStream, { mimeType }) : new MediaRecorder(mediaStream)
    chunks = []
    mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) chunks.push(event.data)
    }
    mediaRecorder.onstop = () => {
      const blobType = mediaRecorder?.mimeType || 'audio/webm'
      const blob = new Blob(chunks, { type: blobType })
      chunks = []
      const extension = blobType.includes('ogg') ? 'ogg' : blobType.includes('mp4') ? 'm4a' : 'webm'
      const file = new File([blob], `voice-note-${Date.now()}.${extension}`, { type: blobType })
      revokePreview()
      localPreviewUrl.value = URL.createObjectURL(blob)
      emit('update:voiceFile', file)
      emit('clear-voice-url')
      stopTracks()
      stopAnalyser()
      clearTimers()
      recording.value = false
      preparing.value = false
    }
    audioContext = new (window.AudioContext || window.webkitAudioContext)()
    const source = audioContext.createMediaStreamSource(mediaStream)
    analyser = audioContext.createAnalyser()
    analyser.fftSize = 256
    source.connect(analyser)
    drawLiveWave()
    elapsedMs.value = 0
    durationMs.value = 0
    timerId = window.setInterval(() => {
      elapsedMs.value += 1000
      if (elapsedMs.value >= 5 * 60 * 1000) stopRecording()
    }, 1000)
    mediaRecorder.start(250)
    recording.value = true
  } catch (error) {
    localError.value = error?.message || 'دسترسی به میکروفون ممکن نشد.'
    stopTracks()
    stopAnalyser()
  } finally {
    preparing.value = false
  }
}

function stopRecording() {
  if (!mediaRecorder || mediaRecorder.state === 'inactive') {
    recording.value = false
    stopTracks()
    stopAnalyser()
    clearTimers()
    return
  }
  durationMs.value = elapsedMs.value
  mediaRecorder.stop()
}

function cancelRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.onstop = null
    mediaRecorder.stop()
  }
  chunks = []
  recording.value = false
  preparing.value = false
  stopTracks()
  stopAnalyser()
  clearTimers()
  drawIdleWave()
}

function clearVoice() {
  cancelRecording()
  revokePreview()
  emit('update:voiceFile', null)
  emit('clear-voice-url')
  playing.value = false
  playProgress.value = 0
  if (audioRef.value) {
    audioRef.value.pause()
    audioRef.value.currentTime = 0
  }
}

async function togglePlayback() {
  const audio = audioRef.value
  if (!audio || !activeAudioUrl.value) return
  if (playing.value) {
    audio.pause()
    playing.value = false
    return
  }
  try {
    await audio.play()
    playing.value = true
  } catch {
    localError.value = 'پخش فایل صوتی ممکن نشد.'
  }
}

function onAudioTimeUpdate() {
  const audio = audioRef.value
  if (!audio || !audio.duration) return
  playProgress.value = (audio.currentTime / audio.duration) * 100
  durationMs.value = audio.duration * 1000
}

function onAudioEnded() {
  playing.value = false
  playProgress.value = 0
}

function seekAudio(event) {
  const audio = audioRef.value
  if (!audio || !audio.duration) return
  const rect = event.currentTarget.getBoundingClientRect()
  const ratio = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width))
  audio.currentTime = ratio * audio.duration
  playProgress.value = ratio * 100
}

onMounted(() => {
  drawIdleWave()
})

watch(
  () => props.voiceFile,
  (file) => {
    if (!file) return
    if (localPreviewUrl.value) return
    revokePreview()
    localPreviewUrl.value = URL.createObjectURL(file)
  },
)

onBeforeUnmount(() => {
  cancelRecording()
  revokePreview()
})
</script>

<template>
  <label :class="['field-shell voice-description-field', error && 'has-error', disabled && 'is-disabled']">
    <span class="voice-field-label-row">
      <span class="voice-field-label">
        {{ label }}
        <em v-if="required" class="voice-required">*</em>
      </span>
      <span class="voice-field-actions">
        <button
          class="voice-mini-btn is-mic"
          type="button"
          :class="{ 'is-recording': recording, 'is-busy': preparing }"
          :disabled="disabled || preparing"
          :title="recording ? 'توقف ضبط' : 'ضبط پیام صوتی'"
          @click.prevent="recording ? stopRecording() : startRecording()"
        >
          <span class="voice-mic-ring" aria-hidden="true"></span>
          <svg v-if="!recording" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 1 0-6 0v5a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2z" fill="currentColor"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" aria-hidden="true">
            <rect x="7" y="7" width="10" height="10" rx="2" fill="currentColor"/>
          </svg>
          <span>{{ recording ? 'توقف' : preparing ? '...' : 'ویس' }}</span>
        </button>
      </span>
    </span>

    <textarea
      ref="textareaRef"
      :value="modelValue"
      :rows="rows"
      :placeholder="placeholder"
      :disabled="disabled"
      @input="emit('update:modelValue', $event.target.value)"
    />

    <div class="voice-panel" :class="{ 'is-open': recording || hasVoice || preparing }">
      <canvas ref="canvasRef" class="voice-wave" height="56"></canvas>

      <div class="voice-panel-meta">
        <div class="voice-status">
          <strong v-if="recording">در حال ضبط</strong>
          <strong v-else-if="hasVoice">پیام صوتی آماده</strong>
          <strong v-else>آماده ضبط</strong>
          <small>{{ recording ? elapsedLabel : (hasVoice ? durationLabel : 'حداکثر ۵ دقیقه') }}</small>
        </div>

        <div class="voice-controls">
          <button
            v-if="recording"
            class="voice-ctrl danger"
            type="button"
            @click.prevent="cancelRecording"
          >
            لغو
          </button>
          <template v-else-if="hasVoice">
            <button class="voice-ctrl" type="button" :disabled="disabled" @click.prevent="togglePlayback">
              {{ playing ? 'توقف پخش' : 'پخش' }}
            </button>
            <button class="voice-ctrl" type="button" :disabled="disabled" @click.prevent="startRecording">
              ضبط مجدد
            </button>
            <button class="voice-ctrl danger" type="button" :disabled="disabled" @click.prevent="clearVoice">
              حذف
            </button>
          </template>
        </div>
      </div>

      <button
        v-if="hasVoice && !recording"
        class="voice-seek"
        type="button"
        :style="{ '--progress': `${playProgress}%` }"
        @click="seekAudio"
      >
        <span class="voice-seek-fill"></span>
      </button>

      <audio
        v-if="activeAudioUrl"
        ref="audioRef"
        :src="activeAudioUrl"
        preload="metadata"
        @timeupdate="onAudioTimeUpdate"
        @ended="onAudioEnded"
        @loadedmetadata="onAudioTimeUpdate"
      />
    </div>

    <small v-if="localError" class="voice-error">{{ localError }}</small>
    <small v-else class="voice-hint">{{ hint }}</small>
  </label>
</template>

<style scoped>
.voice-description-field {
  display: grid;
  gap: 8px;
}

.voice-field-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.voice-field-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 700;
}

.voice-required {
  color: #b42318;
  font-style: normal;
}

.voice-field-actions {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.voice-mini-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  padding: 0 10px;
  border: 0;
  border-radius: 999px;
  background: rgba(52, 144, 139, 0.12);
  color: #1f5c59;
  font: inherit;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
}

.voice-mini-btn svg {
  width: 14px;
  height: 14px;
}

.voice-mini-btn.is-mic {
  background: linear-gradient(135deg, #2f8f88, #1f5c59);
  color: #fff;
  box-shadow: 0 8px 18px rgba(31, 92, 89, 0.28);
}

.voice-mini-btn.is-recording {
  background: linear-gradient(135deg, #c2410c, #9a3412);
  animation: voicePulse 1.2s ease-in-out infinite;
}

.voice-mic-ring {
  position: absolute;
  inset: -4px;
  border-radius: inherit;
  border: 2px solid rgba(255, 255, 255, 0.35);
  opacity: 0;
  pointer-events: none;
}

.voice-mini-btn.is-recording .voice-mic-ring {
  opacity: 1;
  animation: voiceRing 1.2s ease-out infinite;
}

.voice-panel {
  display: grid;
  gap: 10px;
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  padding: 0 12px;
  border-radius: 14px;
  background:
    radial-gradient(120% 120% at 100% 0%, rgba(52, 144, 139, 0.16), transparent 55%),
    linear-gradient(180deg, rgba(248, 252, 251, 0.98), rgba(228, 244, 242, 0.9));
  border: 1px solid transparent;
  transition: max-height 0.28s ease, opacity 0.22s ease, padding 0.22s ease, border-color 0.22s ease;
}

.voice-panel.is-open {
  max-height: 220px;
  opacity: 1;
  padding: 12px;
  border-color: rgba(52, 144, 139, 0.18);
}

.voice-wave {
  width: 100%;
  height: 56px;
  display: block;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.55);
}

.voice-panel-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.voice-status {
  display: grid;
  gap: 2px;
}

.voice-status strong {
  color: #152523;
  font-size: 0.85rem;
}

.voice-status small,
.voice-hint,
.voice-error {
  color: #5f7773;
  font-size: 0.75rem;
}

.voice-error {
  color: #b42318;
}

.voice-controls {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 6px;
}

.voice-ctrl {
  min-height: 32px;
  padding: 0 12px;
  border: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  color: #1f5c59;
  font: inherit;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
}

.voice-ctrl.danger {
  color: #9a3412;
  background: rgba(254, 226, 226, 0.9);
}

.voice-seek {
  position: relative;
  width: 100%;
  height: 8px;
  border: 0;
  border-radius: 999px;
  background: rgba(52, 144, 139, 0.16);
  cursor: pointer;
  padding: 0;
}

.voice-seek-fill {
  position: absolute;
  inset: 0 auto 0 0;
  width: var(--progress, 0%);
  border-radius: inherit;
  background: linear-gradient(90deg, #2f8f88, #1f5c59);
}

@keyframes voicePulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.03); }
}

@keyframes voiceRing {
  0% { transform: scale(0.92); opacity: 0.8; }
  100% { transform: scale(1.18); opacity: 0; }
}

@media (max-width: 720px) {
  .voice-field-label-row {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
