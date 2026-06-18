<script setup>
defineProps({
  open: { type: Boolean, default: false },
  size: { type: String, default: 'default' },
})

const emit = defineEmits(['close'])
</script>

<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="open" class="modal-layer" @click.self="emit('close')">
        <div :class="['modal-shell', `size-${size}`]">
          <button class="icon-btn modal-close" @click="emit('close')">
            <span class="material-symbols-outlined">close</span>
          </button>
          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
