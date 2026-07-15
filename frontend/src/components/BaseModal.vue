<script setup>
import { nextTick, ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  size: { type: String, default: 'default' },
})

const emit = defineEmits(['close'])
const modalShell = ref(null)

watch(
  () => props.open,
  async (isOpen) => {
    if (!isOpen) return
    await nextTick()
    modalShell.value?.focus()
  },
)
</script>

<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="open" class="modal-layer" @pointerdown.self="emit('close')" @click.self="emit('close')">
        <div
          ref="modalShell"
          :class="['modal-shell', `size-${size}`]"
          role="dialog"
          aria-modal="true"
          tabindex="-1"
          @click.stop
          @keydown.esc.stop.prevent="emit('close')"
        >
          <button class="icon-btn modal-close" type="button" aria-label="بستن پنجره" @click="emit('close')">
            <span class="material-symbols-outlined" aria-hidden="true">close</span>
          </button>
          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
