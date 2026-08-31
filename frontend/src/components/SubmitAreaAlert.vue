<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { nextTick, ref, watch } from 'vue'
import { useWorkflowHub } from '../stores/workflowHub'

const { state, clearLastError } = useWorkflowHub()
const rootEl = ref(null)

watch(
  () => state.lastErrorDetails?.message,
  async (message) => {
    if (!message) return
    await nextTick()
    rootEl.value?.scrollIntoView?.({ behavior: 'smooth', block: 'nearest' })
  },
)
</script>

<template>
  <section
    v-if="state.lastErrorDetails?.message"
    ref="rootEl"
    class="submit-area-alert"
    role="alert"
    aria-live="assertive"
  >
    <div class="submit-area-alert-icon" aria-hidden="true">
      <IconlyIcon name="error" decorative />
    </div>
    <div class="submit-area-alert-copy">
      <strong>{{ state.lastErrorDetails.title || 'خطا در انجام عملیات' }}</strong>
      <p>{{ state.lastErrorDetails.message }}</p>
      <ul v-if="state.lastErrorDetails.fields?.length" class="submit-area-alert-fields">
        <li v-for="item in state.lastErrorDetails.fields" :key="`${item.field}-${item.message}`">
          <span>{{ item.label }}</span>
          <em>{{ item.message }}</em>
        </li>
      </ul>
      <small v-if="state.lastErrorDetails.suggestion">{{ state.lastErrorDetails.suggestion }}</small>
    </div>
    <button class="submit-area-alert-close" type="button" aria-label="بستن پیام خطا" @click="clearLastError">
      <IconlyIcon name="close" decorative size="sm" />
    </button>
  </section>
</template>

<style scoped>
.submit-area-alert {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 0.75rem;
  align-items: start;
  margin-top: 0.35rem;
  margin-bottom: 0.75rem;
  padding: 0.9rem 1rem;
  border-radius: 1rem;
  border: 1px solid rgba(228, 93, 93, 0.22);
  background:
    linear-gradient(145deg, rgba(255, 251, 250, 0.98), rgba(254, 242, 242, 0.94));
  box-shadow: 0 10px 24px rgba(180, 35, 24, 0.1);
}

.submit-area-alert-icon {
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 0.8rem;
  display: grid;
  place-items: center;
  background: rgba(228, 93, 93, 0.14);
  color: #c2410c;
}

.submit-area-alert-copy {
  display: grid;
  gap: 0.35rem;
  min-width: 0;
}

.submit-area-alert-copy strong {
  color: #9a3412;
  font-size: 0.88rem;
}

.submit-area-alert-copy p,
.submit-area-alert-copy small {
  margin: 0;
  line-height: 1.65;
}

.submit-area-alert-copy p {
  color: #7f1d1d;
  font-size: 0.86rem;
}

.submit-area-alert-copy small {
  color: #9f4f4f;
  font-size: 0.76rem;
}

.submit-area-alert-fields {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 0.3rem;
}

.submit-area-alert-fields li {
  display: grid;
  gap: 0.08rem;
  padding: 0.4rem 0.55rem;
  border-radius: 0.65rem;
  background: rgba(228, 93, 93, 0.08);
}

.submit-area-alert-fields span {
  color: #9a3412;
  font-size: 0.74rem;
  font-weight: 700;
}

.submit-area-alert-fields em {
  color: #7f1d1d;
  font-style: normal;
  font-size: 0.8rem;
}

.submit-area-alert-close {
  width: 1.85rem;
  height: 1.85rem;
  border: 0;
  border-radius: 999px;
  background: rgba(154, 52, 18, 0.08);
  color: #9a3412;
  display: grid;
  place-items: center;
  cursor: pointer;
}
</style>
