<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { claimTitleHint, releaseTitleHint } from '../utils/titleHintRegistry'

const props = defineProps({
  text: { type: String, default: '' },
  label: { type: String, default: 'راهنمای این بخش' },
  size: { type: String, default: 'md' },
})

const route = useRoute()
const open = ref(false)
const rootRef = ref(null)
const triggerRef = ref(null)
const panelRef = ref(null)
const panelStyle = ref({})
const placement = ref('below')

const hintText = computed(() => String(props.text || '').trim())
const isVisible = computed(() => Boolean(hintText.value))

function close() {
  if (!open.value) return
  open.value = false
  releaseTitleHint(close)
}

function positionPanel() {
  const trigger = triggerRef.value
  const panel = panelRef.value
  if (!trigger || !panel) return

  const rect = trigger.getBoundingClientRect()
  const gap = 10
  const viewportPad = 12
  const width = Math.min(340, Math.max(220, window.innerWidth - viewportPad * 2))
  const height = panel.offsetHeight || 96

  let left = rect.left + rect.width / 2 - width / 2
  left = Math.max(viewportPad, Math.min(left, window.innerWidth - width - viewportPad))

  let top = rect.bottom + gap
  let nextPlacement = 'below'
  if (top + height > window.innerHeight - viewportPad && rect.top - gap - height >= viewportPad) {
    top = rect.top - gap - height
    nextPlacement = 'above'
  }

  placement.value = nextPlacement
  panelStyle.value = {
    width: `${width}px`,
    left: `${Math.round(left)}px`,
    top: `${Math.round(top)}px`,
  }
}

async function openHint() {
  if (!isVisible.value || open.value) return
  claimTitleHint(close)
  open.value = true
  await nextTick()
  positionPanel()
  await nextTick()
  positionPanel()
}

function toggle() {
  if (!isVisible.value) return
  if (open.value) close()
  else void openHint()
}

function onDocPointer(event) {
  if (!open.value) return
  const target = event.target
  if (rootRef.value?.contains(target) || panelRef.value?.contains(target)) return
  close()
}

function onKeydown(event) {
  if (event.key === 'Escape') close()
}

onMounted(() => {
  document.addEventListener('pointerdown', onDocPointer, true)
  document.addEventListener('keydown', onKeydown)
  window.addEventListener('resize', close)
  window.addEventListener('scroll', close, true)
})

onBeforeUnmount(() => {
  close()
  document.removeEventListener('pointerdown', onDocPointer, true)
  document.removeEventListener('keydown', onKeydown)
  window.removeEventListener('resize', close)
  window.removeEventListener('scroll', close, true)
})

watch(() => route.fullPath, close)
watch(hintText, close)
</script>

<template>
  <span v-if="isVisible" ref="rootRef" class="title-hint" :data-size="size">
    <button
      ref="triggerRef"
      class="title-hint-trigger"
      type="button"
      :aria-expanded="open ? 'true' : 'false'"
      :aria-label="label"
      :title="label"
      @click.stop="toggle"
    >
      <span class="title-hint-orb" aria-hidden="true">
        <svg class="title-hint-svg" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="8.25" class="title-hint-svg-outer" />
          <circle cx="12" cy="12" r="3.35" class="title-hint-svg-inner" />
        </svg>
      </span>
      <span class="title-hint-pulse" aria-hidden="true" />
    </button>

    <Teleport to="body">
      <Transition name="title-hint-pop">
        <div
          v-if="open"
          ref="panelRef"
          class="title-hint-panel"
          :data-placement="placement"
          role="dialog"
          :aria-label="label"
          :style="panelStyle"
          @click.stop
        >
          <div class="title-hint-panel-glow" aria-hidden="true" />
          <div class="title-hint-panel-head">
            <span class="title-hint-panel-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="8.25" stroke="currentColor" stroke-width="1.9" />
                <circle cx="12" cy="12" r="3.35" fill="currentColor" />
              </svg>
            </span>
            <strong>{{ label }}</strong>
            <button class="title-hint-close" type="button" aria-label="بستن" @click="close">
              <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M7 7l10 10M17 7L7 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
              </svg>
            </button>
          </div>
          <p>{{ hintText }}</p>
        </div>
      </Transition>
    </Teleport>
  </span>
</template>

<style scoped>
.title-hint {
  position: relative;
  display: inline-flex;
  align-items: center;
  flex: 0 0 auto;
  vertical-align: middle;
}

.title-hint-trigger {
  --hint-size: 26px;
  --hint-icon: 15px;
  position: relative;
  width: var(--hint-size);
  height: var(--hint-size);
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  display: inline-grid;
  place-items: center;
  cursor: pointer;
  color: #0f6b54;
  background: transparent;
  isolation: isolate;
  transition:
    transform 220ms cubic-bezier(0.22, 1, 0.36, 1),
    color 180ms ease;
}

.title-hint[data-size='sm'] .title-hint-trigger {
  --hint-size: 22px;
  --hint-icon: 13px;
}

.title-hint[data-size='lg'] .title-hint-trigger {
  --hint-size: 30px;
  --hint-icon: 17px;
}

.title-hint-orb {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at 32% 28%, rgba(255, 255, 255, 0.95), transparent 42%),
    linear-gradient(145deg, #edfaf5 0%, #d7f0e6 48%, #c5e8db 100%);
  box-shadow:
    inset 0 0 0 1.5px rgba(15, 107, 84, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.85),
    0 1px 2px rgba(12, 48, 38, 0.06),
    0 6px 14px rgba(15, 107, 84, 0.12);
  transition:
    background 200ms ease,
    box-shadow 200ms ease,
    transform 220ms cubic-bezier(0.22, 1, 0.36, 1);
}

.title-hint-svg {
  width: var(--hint-icon);
  height: var(--hint-icon);
  display: block;
}

.title-hint-svg-outer {
  fill: none;
  stroke: currentColor;
  stroke-width: 1.9;
}

.title-hint-svg-inner {
  fill: currentColor;
}

.title-hint-pulse {
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  pointer-events: none;
  box-shadow: 0 0 0 0 rgba(15, 107, 84, 0.18);
  opacity: 0;
  transition: opacity 220ms ease, box-shadow 220ms ease, transform 220ms ease;
}

.title-hint-trigger:hover .title-hint-orb,
.title-hint-trigger:focus-visible .title-hint-orb {
  background:
    radial-gradient(circle at 32% 28%, #ffffff, transparent 46%),
    linear-gradient(145deg, #ffffff 0%, #d9f4ea 52%, #b7e5d4 100%);
  box-shadow:
    inset 0 0 0 1.5px rgba(15, 107, 84, 0.34),
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    0 2px 4px rgba(12, 48, 38, 0.08),
    0 10px 22px rgba(15, 107, 84, 0.18);
  transform: scale(1.05);
}

.title-hint-trigger:hover,
.title-hint-trigger:focus-visible {
  color: #0a5744;
  transform: translateY(-1px);
  outline: none;
}

.title-hint-trigger:hover .title-hint-pulse,
.title-hint-trigger:focus-visible .title-hint-pulse {
  opacity: 1;
  box-shadow: 0 0 0 5px rgba(15, 107, 84, 0.1);
}

.title-hint-trigger[aria-expanded='true'] {
  color: #fff;
  transform: translateY(-1px) scale(1.04);
}

.title-hint-trigger[aria-expanded='true'] .title-hint-orb {
  background:
    radial-gradient(circle at 30% 26%, rgba(255, 255, 255, 0.28), transparent 42%),
    linear-gradient(145deg, #1a9a78 0%, #0f6b54 55%, #0a5744 100%);
  box-shadow:
    inset 0 0 0 1.5px rgba(255, 255, 255, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.22),
    0 8px 20px rgba(15, 107, 84, 0.28);
  transform: scale(1.06);
}

.title-hint-trigger[aria-expanded='true'] .title-hint-pulse {
  opacity: 1;
  box-shadow: 0 0 0 6px rgba(15, 107, 84, 0.14);
}

.title-hint-trigger:active .title-hint-orb {
  transform: scale(0.96);
}
</style>

<style>
.title-hint-panel {
  position: fixed;
  z-index: 12000;
  padding: 14px 14px 13px;
  border-radius: 18px;
  overflow: hidden;
  color: #1d2b27;
  background:
    linear-gradient(165deg, rgba(255, 255, 255, 0.97), rgba(241, 248, 244, 0.95));
  border: 1px solid rgba(15, 107, 84, 0.14);
  box-shadow:
    0 22px 56px rgba(18, 42, 34, 0.16),
    0 2px 8px rgba(18, 42, 34, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(16px) saturate(1.2);
  -webkit-backdrop-filter: blur(16px) saturate(1.2);
  transform-origin: top center;
}

.title-hint-panel[data-placement='above'] {
  transform-origin: bottom center;
}

.title-hint-panel-glow {
  position: absolute;
  inset: auto -24% -48% 18%;
  height: 78%;
  background: radial-gradient(circle, rgba(26, 154, 120, 0.18), transparent 70%);
  pointer-events: none;
}

.title-hint-panel-head {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.title-hint-panel-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  color: #fff;
  background:
    radial-gradient(circle at 30% 26%, rgba(255, 255, 255, 0.28), transparent 42%),
    linear-gradient(145deg, #1a9a78 0%, #0f6b54 55%, #0a5744 100%);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.16),
    0 6px 14px rgba(15, 107, 84, 0.22);
}

.title-hint-panel-icon svg {
  width: 15px;
  height: 15px;
  display: block;
}

.title-hint-panel-head strong {
  flex: 1 1 auto;
  min-width: 0;
  font-size: 12.5px;
  font-weight: 750;
  letter-spacing: -0.01em;
  color: #0a5744;
}

.title-hint-close {
  width: 28px;
  height: 28px;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  display: inline-grid;
  place-items: center;
  cursor: pointer;
  color: rgba(45, 62, 55, 0.7);
  background: rgba(15, 107, 84, 0.07);
  transition: background 160ms ease, color 160ms ease, transform 160ms ease;
}

.title-hint-close svg {
  width: 12px;
  height: 12px;
  display: block;
}

.title-hint-close:hover,
.title-hint-close:focus-visible {
  color: #0a5744;
  background: rgba(15, 107, 84, 0.14);
  outline: none;
  transform: scale(1.05);
}

.title-hint-panel p {
  position: relative;
  margin: 0;
  font-size: 13px;
  line-height: 1.75;
  color: rgba(35, 48, 43, 0.84);
  text-align: right;
}

.title-hint-pop-enter-active,
.title-hint-pop-leave-active {
  transition:
    opacity 160ms ease,
    transform 220ms cubic-bezier(0.22, 1, 0.36, 1);
}

.title-hint-pop-enter-from,
.title-hint-pop-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.96);
}

.title-hint-panel[data-placement='above'].title-hint-pop-enter-from,
.title-hint-panel[data-placement='above'].title-hint-pop-leave-to {
  transform: translateY(-8px) scale(0.96);
}

@media (max-width: 720px) {
  .title-hint-panel {
    border-radius: 16px;
    padding: 12px;
  }

  .title-hint-panel p {
    font-size: 12.5px;
    line-height: 1.7;
  }
}
</style>
