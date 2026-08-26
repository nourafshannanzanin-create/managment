<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  disabled: { type: Boolean, default: false },
  rootMargin: { type: String, default: '240px 0px' },
})

const emit = defineEmits(['reach-end'])

const rootEl = ref(null)
let observer = null

function disconnect() {
  if (observer) {
    observer.disconnect()
    observer = null
  }
}

function connect() {
  disconnect()
  if (props.disabled || typeof IntersectionObserver === 'undefined') return
  const node = rootEl.value
  if (!node) return

  observer = new IntersectionObserver(
    (entries) => {
      if (props.disabled) return
      if (entries.some((entry) => entry.isIntersecting)) {
        emit('reach-end')
      }
    },
    { root: null, rootMargin: props.rootMargin, threshold: 0.01 },
  )
  observer.observe(node)
}

onMounted(connect)
onBeforeUnmount(disconnect)

watch(
  () => props.disabled,
  (disabled) => {
    if (disabled) disconnect()
    else connect()
  },
)
</script>

<template>
  <div ref="rootEl" class="infinite-scroll-sentinel" aria-hidden="true">
    <slot />
  </div>
</template>

<style scoped>
.infinite-scroll-sentinel {
  width: 100%;
  min-height: 1px;
  display: grid;
  place-items: center;
  padding: 10px 0 4px;
}
</style>
