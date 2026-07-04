<script setup>
import { nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { applyStitchHead, loadStitchBody, prepareStitchShell } from '../utils/stitch'

const props = defineProps({
  stitchId: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['ready'])
const root = ref(null)
const loadError = ref('')
const route = useRoute()

async function render() {
  if (!root.value) return
  loadError.value = ''
  root.value.innerHTML = ''
  try {
    const stitch = await loadStitchBody(props.stitchId)
    applyStitchHead(stitch.head)
    root.value.innerHTML = stitch.html
    prepareStitchShell(root.value)
    await nextTick()
    emit('ready', root.value)
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : 'Stitch page failed to load'
  }
}

defineExpose({
  getRoot: () => root.value,
  render,
})

onMounted(render)

watch(
  () => props.stitchId,
  () => {
    void render()
  },
)

watch(
  () => route.fullPath,
  () => {
    void render()
  },
)
</script>

<template>
  <section class="stitch-runtime-host">
    <div v-if="loadError" class="stitch-runtime-error">
      <strong>صفحه بارگذاری نشد</strong>
      <span>{{ loadError }}</span>
    </div>
    <div ref="root"></div>
  </section>
</template>

<style scoped>
.stitch-runtime-host {
  min-height: 100vh;
}

.stitch-runtime-error {
  min-height: 100vh;
  padding: 24px;
  display: grid;
  place-content: center;
  gap: 8px;
  text-align: center;
  color: #2E4374;
  background: rgba(229, 195, 166, 0.42);
}
</style>
