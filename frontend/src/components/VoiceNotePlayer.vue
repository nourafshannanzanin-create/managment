<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  url: { type: String, default: '' },
  label: { type: String, default: 'پیام صوتی توضیحات' },
})

const audioRef = ref(null)
const playing = ref(false)
const progress = ref(0)
const duration = ref(0)

const hasUrl = computed(() => Boolean(String(props.url || '').trim()))
const timeLabel = computed(() => {
  const total = Math.max(0, Math.floor(duration.value || 0))
  const m = String(Math.floor(total / 60)).padStart(2, '0')
  const s = String(total % 60).padStart(2, '0')
  return `${m}:${s}`
})

async function toggle() {
  const audio = audioRef.value
  if (!audio || !hasUrl.value) return
  if (playing.value) {
    audio.pause()
    playing.value = false
    return
  }
  await audio.play()
  playing.value = true
}

function onTime() {
  const audio = audioRef.value
  if (!audio) return
  duration.value = audio.duration || duration.value
  progress.value = audio.duration ? (audio.currentTime / audio.duration) * 100 : 0
}

function onEnded() {
  playing.value = false
  progress.value = 0
}

function seek(event) {
  const audio = audioRef.value
  if (!audio?.duration) return
  const rect = event.currentTarget.getBoundingClientRect()
  const ratio = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width))
  audio.currentTime = ratio * audio.duration
  progress.value = ratio * 100
}

watch(
  () => props.url,
  () => {
    playing.value = false
    progress.value = 0
  },
)
</script>

<template>
  <div v-if="hasUrl" class="voice-note-player">
    <div class="voice-note-copy">
      <strong>{{ label }}</strong>
      <small>{{ timeLabel }}</small>
    </div>
    <button class="voice-note-play" type="button" @click="toggle">
      {{ playing ? 'توقف' : 'پخش ویس' }}
    </button>
    <button class="voice-note-seek" type="button" :style="{ '--progress': `${progress}%` }" @click="seek">
      <span></span>
    </button>
    <audio
      ref="audioRef"
      :src="url"
      preload="metadata"
      @timeupdate="onTime"
      @loadedmetadata="onTime"
      @ended="onEnded"
    />
  </div>
</template>

<style scoped>
.voice-note-player {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px 12px;
  align-items: center;
  padding: 12px 14px;
  border-radius: 14px;
  background:
    linear-gradient(160deg, rgba(255, 255, 255, 0.96), rgba(228, 244, 242, 0.88));
  border: 1px solid rgba(52, 144, 139, 0.16);
}

.voice-note-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.voice-note-copy strong {
  color: #152523;
  font-size: 0.86rem;
}

.voice-note-copy small {
  color: #5f7773;
  font-size: 0.74rem;
}

.voice-note-play {
  min-height: 34px;
  padding: 0 14px;
  border: 0;
  border-radius: 999px;
  background: linear-gradient(135deg, #2f8f88, #1f5c59);
  color: #fff;
  font: inherit;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
}

.voice-note-seek {
  grid-column: 1 / -1;
  position: relative;
  height: 8px;
  border: 0;
  border-radius: 999px;
  background: rgba(52, 144, 139, 0.16);
  padding: 0;
  cursor: pointer;
}

.voice-note-seek span {
  position: absolute;
  inset: 0 auto 0 0;
  width: var(--progress, 0%);
  border-radius: inherit;
  background: linear-gradient(90deg, #2f8f88, #1f5c59);
}
</style>
