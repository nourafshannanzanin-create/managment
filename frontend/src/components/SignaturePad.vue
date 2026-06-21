<script setup>
import { onMounted, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const canvasRef = ref(null)
let context
let drawing = false

function resizeCanvas() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ratio = window.devicePixelRatio || 1
  const width = canvas.clientWidth
  const height = canvas.clientHeight
  canvas.width = width * ratio
  canvas.height = height * ratio
  context = canvas.getContext('2d')
  context.scale(ratio, ratio)
  context.lineWidth = 2.2
  context.lineCap = 'round'
  context.strokeStyle = '#244952'
  context.fillStyle = '#ffffff'
  context.fillRect(0, 0, width, height)
  if (props.modelValue) drawImage(props.modelValue)
}

function drawImage(dataUrl) {
  const canvas = canvasRef.value
  if (!canvas || !context) return
  const image = new Image()
  image.onload = () => {
    context.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight)
    context.fillStyle = '#ffffff'
    context.fillRect(0, 0, canvas.clientWidth, canvas.clientHeight)
    context.drawImage(image, 0, 0, canvas.clientWidth, canvas.clientHeight)
  }
  image.src = dataUrl
}

function getPoint(event) {
  const canvas = canvasRef.value
  const rect = canvas.getBoundingClientRect()
  const source = event.touches?.[0] || event
  return { x: source.clientX - rect.left, y: source.clientY - rect.top }
}

function start(event) {
  drawing = true
  const point = getPoint(event)
  context.beginPath()
  context.moveTo(point.x, point.y)
}

function move(event) {
  if (!drawing) return
  event.preventDefault()
  const point = getPoint(event)
  context.lineTo(point.x, point.y)
  context.stroke()
}

function end() {
  if (!drawing) return
  drawing = false
  emit('update:modelValue', canvasRef.value.toDataURL('image/png'))
}

function clearPad() {
  emit('update:modelValue', '')
  resizeCanvas()
}

watch(
  () => props.modelValue,
  (value) => {
    if (value && canvasRef.value && context) drawImage(value)
    if (!value && canvasRef.value && context) resizeCanvas()
  },
)

onMounted(() => {
  resizeCanvas()
  window.addEventListener('resize', resizeCanvas)
})

defineExpose({ clearPad })
</script>

<template>
  <div class="signature-pad-shell">
    <canvas
      ref="canvasRef"
      class="signature-pad"
      @mousedown="start"
      @mousemove="move"
      @mouseup="end"
      @mouseleave="end"
      @touchstart.prevent="start"
      @touchmove.prevent="move"
      @touchend="end"
    ></canvas>
    <button class="action-btn tone-soft signature-clear" @click="clearPad">
      <span class="material-symbols-outlined">ink_eraser</span>
      <span>پاک کردن</span>
    </button>
  </div>
</template>
