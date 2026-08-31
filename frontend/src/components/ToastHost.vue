<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { toastState, removeNotification } from '../utils/notify'

const hostStyle = ref(null)
let observer = null
let rafId = 0

function typeMeta(type) {
  return {
    success: { className: 'toast-success', icon: 'check_circle', label: 'موفق' },
    error: { className: 'toast-error', icon: 'error', label: 'خطا' },
    warning: { className: 'toast-warning', icon: 'warning', label: 'هشدار' },
    info: { className: 'toast-info', icon: 'info', label: 'اطلاع' },
  }[type] || { className: 'toast-info', icon: 'info', label: 'اطلاع' }
}

function findSubmitAnchor(shell) {
  const actions = shell.querySelector(
    '.modal-actions, .action-group.modal-actions, .user-modal-actions, section.user-modal-actions, .task-action-row',
  )
  if (!actions) return null

  return (
    actions.querySelector('.tone-primary') ||
    actions.querySelector('button[type="submit"]') ||
    actions.lastElementChild ||
    actions
  )
}

function resolveAnchor() {
  if (typeof window === 'undefined') return

  const layers = Array.from(document.querySelectorAll('body > .modal-layer'))
  const layer = layers[layers.length - 1]
  if (!layer) {
    hostStyle.value = null
    return
  }

  const shell = layer.querySelector('.modal-shell')
  if (!shell) {
    hostStyle.value = null
    return
  }

  const submitTarget = findSubmitAnchor(shell) || shell
  const shellRect = shell.getBoundingClientRect()
  const targetRect = submitTarget.getBoundingClientRect()
  const gap = 10
  const width = Math.min(320, Math.max(240, shellRect.width - 32))

  const left = Math.min(
    Math.max(shellRect.left + 16, targetRect.left),
    Math.max(shellRect.left + 16, shellRect.right - width - 16),
  )

  hostStyle.value = {
    bottom: `${Math.max(16, window.innerHeight - targetRect.top + gap)}px`,
    left: `${left}px`,
    right: 'auto',
    insetInlineEnd: 'auto',
    width: `${width}px`,
  }
}

function scheduleAnchorUpdate() {
  if (rafId) cancelAnimationFrame(rafId)
  rafId = requestAnimationFrame(() => {
    rafId = 0
    resolveAnchor()
  })
}

onMounted(() => {
  scheduleAnchorUpdate()
  window.addEventListener('resize', scheduleAnchorUpdate)
  window.addEventListener('scroll', scheduleAnchorUpdate, true)
  observer = new MutationObserver(scheduleAnchorUpdate)
  observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['class', 'style', 'open'],
  })
})

watch(
  () => toastState.items.length,
  () => scheduleAnchorUpdate(),
)

onUnmounted(() => {
  window.removeEventListener('resize', scheduleAnchorUpdate)
  window.removeEventListener('scroll', scheduleAnchorUpdate, true)
  observer?.disconnect()
  if (rafId) cancelAnimationFrame(rafId)
})
</script>

<template>
  <Teleport to="body">
    <div
      class="toast-host"
      :class="{ 'is-modal-anchored': Boolean(hostStyle) }"
      :style="hostStyle || undefined"
      aria-live="assertive"
      aria-atomic="true"
    >
      <TransitionGroup name="toast-stack" tag="div" class="toast-stack">
        <article
          v-for="item in toastState.items"
          :key="item.id"
          class="toast-card"
          :class="typeMeta(item.type).className"
          role="alert"
        >
          <div class="toast-accent" aria-hidden="true"></div>

          <div class="toast-icon" aria-hidden="true">
            <IconlyIcon :name="typeMeta(item.type).icon" decorative size="lg" />
          </div>

          <div class="toast-copy">
            <div class="toast-head">
              <strong>{{ item.title || typeMeta(item.type).label }}</strong>
              <button
                class="toast-close"
                type="button"
                aria-label="بستن اعلان"
                @click.stop="removeNotification(item.id)"
              >
                <IconlyIcon name="close" decorative size="sm" />
              </button>
            </div>

            <p v-if="item.message" class="toast-message">{{ item.message }}</p>

            <ul v-if="item.fields?.length" class="toast-fields">
              <li v-for="field in item.fields" :key="`${field.field}-${field.message}`">
                <span>{{ field.label }}</span>
                <em>{{ field.message }}</em>
              </li>
            </ul>

            <small v-if="item.suggestion" class="toast-suggestion">{{ item.suggestion }}</small>
          </div>

          <span class="toast-progress" :style="{ animationDuration: `${item.duration}ms` }"></span>
        </article>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-host {
  position: fixed;
  inset-inline-end: 1rem;
  bottom: calc(env(safe-area-inset-bottom, 0px) + 1rem);
  z-index: 2147483000;
  width: min(22rem, calc(100vw - 2rem));
  pointer-events: none;
}

.toast-host.is-modal-anchored {
  inset-inline-end: auto;
}

.toast-stack {
  display: grid;
  gap: 0.75rem;
  width: 100%;
}

.toast-card {
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 0.85rem;
  align-items: start;
  padding: 0.95rem 1rem 1rem;
  border-radius: 1.1rem;
  border: 1px solid rgba(255, 255, 255, 0.72);
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.97), rgba(236, 248, 246, 0.94));
  box-shadow:
    0 18px 42px rgba(15, 35, 40, 0.18),
    0 4px 14px rgba(52, 144, 139, 0.12);
  backdrop-filter: blur(14px);
  pointer-events: auto;
}

.toast-accent {
  position: absolute;
  inset-block: 0;
  inset-inline-start: 0;
  width: 4px;
  border-radius: 0 999px 999px 0;
  background: currentColor;
  opacity: 0.85;
}

.toast-icon {
  width: 2.35rem;
  height: 2.35rem;
  border-radius: 0.85rem;
  display: grid;
  place-items: center;
  background: rgba(52, 144, 139, 0.12);
  color: #1f5c59;
}

.toast-copy {
  display: grid;
  gap: 0.45rem;
  min-width: 0;
}

.toast-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.toast-head strong {
  color: #102422;
  font-size: 0.92rem;
  line-height: 1.5;
}

.toast-close {
  flex: 0 0 auto;
  width: 1.85rem;
  height: 1.85rem;
  border: 0;
  border-radius: 999px;
  background: rgba(16, 36, 34, 0.06);
  color: #4d6662;
  display: grid;
  place-items: center;
  cursor: pointer;
}

.toast-message {
  margin: 0;
  color: #274542;
  font-size: 0.88rem;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.toast-fields {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 0.35rem;
}

.toast-fields li {
  display: grid;
  gap: 0.1rem;
  padding: 0.45rem 0.6rem;
  border-radius: 0.7rem;
  background: rgba(52, 144, 139, 0.08);
}

.toast-fields span {
  color: #1f5c59;
  font-size: 0.76rem;
  font-weight: 700;
}

.toast-fields em {
  color: #35514e;
  font-style: normal;
  font-size: 0.82rem;
  line-height: 1.55;
}

.toast-suggestion {
  color: #5f7773;
  font-size: 0.78rem;
  line-height: 1.6;
}

.toast-progress {
  position: absolute;
  inset-inline: 0;
  bottom: 0;
  height: 3px;
  transform-origin: right center;
  animation-name: toast-progress;
  animation-timing-function: linear;
  animation-fill-mode: forwards;
  background: currentColor;
  opacity: 0.35;
}

.toast-success {
  color: #1f7a57;
}

.toast-success .toast-icon {
  background: rgba(61, 191, 140, 0.16);
  color: #1f7a57;
}

.toast-error {
  color: #c2410c;
}

.toast-error .toast-icon {
  background: rgba(228, 93, 93, 0.14);
  color: #c2410c;
}

.toast-warning {
  color: #b7791f;
}

.toast-warning .toast-icon {
  background: rgba(224, 162, 74, 0.16);
  color: #b7791f;
}

.toast-info {
  color: #1f5c59;
}

.toast-info .toast-icon {
  background: rgba(52, 144, 139, 0.14);
  color: #1f5c59;
}

.toast-stack-enter-active,
.toast-stack-leave-active {
  transition: opacity 0.24s ease, transform 0.24s ease;
}

.toast-stack-enter-from,
.toast-stack-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.98);
}

.toast-stack-move {
  transition: transform 0.24s ease;
}

@keyframes toast-progress {
  from { transform: scaleX(1); }
  to { transform: scaleX(0); }
}

@media (max-width: 900px) {
  .toast-host:not(.is-modal-anchored) {
    inset-inline-end: 0.85rem;
    bottom: calc(env(safe-area-inset-bottom, 0px) + 5.25rem);
    width: min(20rem, calc(100vw - 1.7rem));
  }
}
</style>
