<script setup>
import { computed, ref } from 'vue'

import BaseModal from './BaseModal.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const props = defineProps({
  open: { type: Boolean, default: false },
  request: { type: Object, default: null },
  timeline: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

defineEmits(['close'])

const rejectReason = ref('')
const { canApproveSelectedRequest, approveSelectedRequest, rejectSelectedRequest, state } = useWorkflowHub()

const isApproved = computed(() => String(props.request?.status || '').includes('تایید'))
const isRejected = computed(() => String(props.request?.status || '').includes('رد'))

const requestTone = computed(() => {
  if (isApproved.value) return 'is-approved'
  if (isRejected.value) return 'is-rejected'
  return 'is-pending'
})

const requestIcon = computed(() => {
  if (isApproved.value) return 'verified'
  if (isRejected.value) return 'cancel'
  return 'schedule'
})

const requestStatusTitle = computed(() => {
  if (isApproved.value) return 'تایید شده'
  if (isRejected.value) return 'رد شده'
  return 'در جریان'
})

const requestStatusText = computed(() => {
  if (isApproved.value) return 'درخواست نهایی شده و گردش آن با موفقیت تکمیل شده است.'
  if (isRejected.value) return 'درخواست رد شده و برای ادامه نیاز به بازبینی یا ثبت مجدد دارد.'
  return 'درخواست هنوز در مسیر بررسی است و می‌توانید از همین پنجره اقدام مدیریتی انجام دهید.'
})

const metaItems = computed(() => {
  if (!props.request) return []
  return [
    { label: 'کد درخواست', value: props.request.id, icon: 'badge' },
    { label: 'ثبت‌کننده', value: props.request.owner, icon: 'person' },
    { label: 'مدیر اصلی', value: props.request.manager, icon: 'supervisor_account' },
    { label: 'مدیران ارجاعی', value: props.request.managerAssignees?.length ? props.request.managerAssignees.join('، ') : 'تعیین نشده', icon: 'group' },
    { label: 'کارمندان ارجاعی', value: props.request.employeeAssignees?.length ? props.request.employeeAssignees.join('، ') : 'تعیین نشده', icon: 'badge' },
    { label: 'اولویت', value: props.request.priority, icon: 'flag' },
  ]
})

async function handleReject() {
  await rejectSelectedRequest(rejectReason.value)
}
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div v-if="request" class="request-modal-shell" :class="requestTone">
      <section class="request-hero">
        <div class="request-hero-copy">
          <p class="page-eyebrow">جزئیات درخواست</p>
          <h2>{{ request.title }}</h2>
          <div class="request-hero-meta">
            <span class="request-type-pill">{{ request.department || 'بدون بخش' }}</span>
            <span class="request-meta-divider"></span>
            <span>{{ request.owner }}</span>
            <span class="request-meta-divider"></span>
            <span>{{ request.deadline || '-' }}</span>
          </div>
        </div>

        <div class="request-status-panel">
          <div class="request-status-icon">
            <span class="material-symbols-outlined">{{ requestIcon }}</span>
          </div>
          <div class="request-status-copy">
            <strong>{{ requestStatusTitle }}</strong>
            <p>{{ requestStatusText }}</p>
            <small>{{ request.status }}</small>
          </div>
        </div>
      </section>

      <section class="request-meta-board">
        <article v-for="item in metaItems" :key="item.label" class="request-meta-card">
          <div class="request-meta-icon">
            <span class="material-symbols-outlined">{{ item.icon }}</span>
          </div>
          <div class="request-meta-copy">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </article>
      </section>

      <section class="request-content-grid">
        <article class="request-surface">
          <div class="request-surface-head">
            <div>
              <p class="request-surface-kicker">شرح درخواست</p>
              <h3>توضیحات و جزئیات</h3>
              <small>خلاصه ثبت‌شده برای این درخواست در این بخش نمایش داده می‌شود.</small>
            </div>
          </div>

          <div class="request-description-box">
            <p>{{ request.description || 'برای این درخواست توضیحی ثبت نشده است.' }}</p>
          </div>
        </article>

        <div class="request-side-stack">
          <article class="request-surface">
            <div class="request-surface-head">
              <div>
                <p class="request-surface-kicker">گردش کار</p>
                <h3>تایم‌لاین اقدامات</h3>
                <small v-if="loading">در حال بارگذاری...</small>
              </div>
            </div>

            <div class="request-timeline-rail">
              <article v-for="item in timeline" :key="`${item.step}-${item.title}`" class="request-timeline-node">
                <div class="request-timeline-index">{{ item.step }}</div>
                <div class="request-timeline-copy">
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.note }}</p>
                </div>
              </article>
            </div>
          </article>

          <article v-if="canApproveSelectedRequest" class="request-surface">
            <div class="request-surface-head">
              <div>
                <p class="request-surface-kicker">اقدام</p>
                <h3>تصمیم مدیریتی</h3>
              </div>
            </div>

            <label class="request-reject-note">
              <span>علت رد</span>
              <textarea v-model="rejectReason" class="field-shell request-reject-textarea" rows="4" placeholder="در صورت نیاز علت رد را وارد کنید"></textarea>
            </label>

            <p v-if="state.lastError" class="inline-error">{{ state.lastError }}</p>

            <div class="request-action-row">
              <button class="action-btn tone-soft" type="button" @click="$emit('close')">
                <span class="material-symbols-outlined">close</span>
                <span>بستن</span>
              </button>
              <button class="action-btn tone-danger" type="button" @click="handleReject">
                <span class="material-symbols-outlined">cancel</span>
                <span>رد</span>
              </button>
              <button class="action-btn tone-primary" type="button" @click="approveSelectedRequest">
                <span class="material-symbols-outlined">check_circle</span>
                <span>تایید</span>
              </button>
            </div>
          </article>
        </div>
      </section>
    </div>
  </BaseModal>
</template>

<style scoped>
.request-modal-shell {
  display: grid;
  gap: 22px;
  padding: 8px 4px 4px;
}

.request-hero,
.request-surface,
.request-meta-card {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(38, 56, 92, 0.08);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 248, 252, 0.96)),
    var(--surface);
  box-shadow: 0 22px 50px rgba(28, 42, 76, 0.08);
}

.request-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(280px, 0.9fr);
  gap: 18px;
  padding: 24px;
  border-radius: 30px;
}

.request-hero::before,
.request-surface::before {
  content: '';
  position: absolute;
  inset: auto auto -40% -10%;
  width: 220px;
  height: 220px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(72, 103, 183, 0.12), transparent 70%);
  pointer-events: none;
}

.request-hero-copy,
.request-status-copy,
.request-meta-copy {
  display: grid;
  gap: 8px;
}

.request-hero-copy h2 {
  margin: 0;
  font-size: clamp(28px, 2.3vw, 38px);
  line-height: 1.3;
  color: #203255;
}

.request-hero-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  color: var(--muted);
  font-size: 13px;
}

.request-type-pill {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(72, 103, 183, 0.1);
  color: var(--primary);
  font-weight: 800;
}

.request-meta-divider {
  width: 5px;
  height: 5px;
  border-radius: 999px;
  background: rgba(82, 96, 126, 0.4);
}

.request-status-panel {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 16px;
  align-items: start;
  padding: 18px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(255, 255, 255, 0.66);
  backdrop-filter: blur(10px);
}

.request-status-icon,
.request-meta-icon {
  display: grid;
  place-items: center;
}

.request-status-icon {
  width: 64px;
  height: 64px;
  border-radius: 22px;
  font-size: 28px;
  color: #fff;
  background: linear-gradient(135deg, #4d67b2, #314783);
}

.request-status-copy strong {
  font-size: 20px;
  color: #203255;
}

.request-status-copy p,
.request-status-copy small,
.request-description-box p,
.request-timeline-copy p {
  margin: 0;
  line-height: 1.9;
  color: var(--muted);
}

.request-meta-board {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.request-meta-card {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 14px;
  align-items: center;
  padding: 18px;
  border-radius: 24px;
}

.request-meta-icon {
  width: 46px;
  height: 46px;
  border-radius: 16px;
  background: rgba(72, 103, 183, 0.08);
  color: var(--primary);
}

.request-meta-copy span {
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
}

.request-meta-copy strong {
  margin: 0;
  font-size: 16px;
  color: #203255;
  line-height: 1.55;
}

.request-content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.02fr) minmax(320px, 0.98fr);
  gap: 18px;
}

.request-side-stack {
  display: grid;
  gap: 18px;
  align-content: start;
}

.request-surface {
  display: grid;
  gap: 18px;
  padding: 22px;
  border-radius: 28px;
}

.request-surface-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.request-surface-kicker {
  margin: 0 0 8px;
  color: var(--muted);
  font-size: 11px;
  letter-spacing: 0.12em;
  font-weight: 800;
}

.request-surface-head h3 {
  margin: 0;
  font-size: 20px;
  color: #203255;
}

.request-surface-head small {
  display: block;
  margin-top: 6px;
  line-height: 1.8;
  color: var(--muted);
}

.request-description-box {
  min-height: 220px;
  padding: 20px;
  border-radius: 24px;
  border: 1px dashed rgba(72, 103, 183, 0.2);
  background: linear-gradient(180deg, rgba(248, 250, 254, 0.94), rgba(240, 244, 250, 0.96));
}

.request-timeline-rail {
  display: grid;
  gap: 14px;
}

.request-timeline-node {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 14px;
  align-items: start;
}

.request-timeline-index {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: #fff;
  font-weight: 800;
}

.request-timeline-copy {
  display: grid;
  gap: 6px;
}

.request-timeline-copy strong {
  color: #203255;
}

.request-reject-note {
  display: grid;
  gap: 10px;
}

.request-reject-note > span {
  font-size: 12px;
  font-weight: 800;
  color: var(--muted);
}

.request-reject-textarea {
  min-height: 126px;
  background: rgba(255, 255, 255, 0.76);
}

.request-action-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.inline-error {
  margin: 0;
  color: #b42318;
  font-size: 0.92rem;
}

.request-modal-shell.is-approved .request-status-icon {
  background: linear-gradient(135deg, #23936d, #176f52);
}

.request-modal-shell.is-rejected .request-status-icon {
  background: linear-gradient(135deg, #d36363, #ab4343);
}

.request-modal-shell.is-pending .request-status-icon {
  background: linear-gradient(135deg, #d39d36, #ab7720);
}

@media (max-width: 1100px) {
  .request-hero,
  .request-content-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .request-meta-board {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .request-modal-shell {
    gap: 16px;
    padding: 0;
  }

  .request-hero,
  .request-surface {
    padding: 18px;
    border-radius: 22px;
  }

  .request-meta-board {
    grid-template-columns: minmax(0, 1fr);
  }

  .request-status-panel {
    grid-template-columns: minmax(0, 1fr);
  }

  .request-action-row {
    flex-direction: column;
  }
}
</style>
