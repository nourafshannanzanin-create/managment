<script setup>
import { computed, ref } from 'vue'

import BaseModal from './BaseModal.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const props = defineProps({
  open: { type: Boolean, default: false },
  expense: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})

defineEmits(['close'])

const rejectReason = ref('')
const { canApproveSelectedExpense, approveSelectedExpense, rejectSelectedExpense } = useWorkflowHub()

const isApproved = computed(() => String(props.expense?.status || '').includes('تایید'))
const isRejected = computed(() => String(props.expense?.status || '').includes('رد'))

const expenseTone = computed(() => {
  if (isApproved.value) return 'is-approved'
  if (isRejected.value) return 'is-rejected'
  return 'is-pending'
})

const expenseIcon = computed(() => {
  if (isApproved.value) return 'verified'
  if (isRejected.value) return 'cancel'
  return 'payments'
})

const expenseStatusTitle = computed(() => {
  if (isApproved.value) return 'تایید شده'
  if (isRejected.value) return 'رد شده'
  return 'در حال بررسی'
})

const expenseStatusText = computed(() => {
  if (isApproved.value) return 'این هزینه تایید شده و پرونده مالی آن تکمیل شده است.'
  if (isRejected.value) return 'این هزینه رد شده و برای ادامه نیاز به بازبینی مدارک دارد.'
  return 'این هزینه هنوز در صف بررسی است و تصمیم نهایی از همین پنجره ثبت می‌شود.'
})

const metaItems = computed(() => {
  if (!props.expense) return []
  return [
    { label: 'کد هزینه', value: props.expense.id, icon: 'badge' },
    { label: 'ثبت‌کننده', value: props.expense.owner, icon: 'person' },
    { label: 'بخش', value: props.expense.department, icon: 'apartment' },
    { label: 'نوع', value: props.expense.category || '-', icon: 'category' },
    { label: 'مبلغ', value: props.expense.amount, icon: 'payments' },
    { label: 'تاریخ', value: props.expense.submittedAt || '-', icon: 'calendar_month' },
  ]
})

async function handleReject() {
  await rejectSelectedExpense(rejectReason.value)
}
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div v-if="expense" class="expense-modal-shell" :class="expenseTone">
      <section class="expense-hero">
        <div class="expense-hero-copy">
          <p class="page-eyebrow">جزئیات هزینه</p>
          <h2>{{ expense.title }}</h2>
          <div class="expense-hero-meta">
            <span class="expense-type-pill">{{ expense.category || 'هزینه سازمانی' }}</span>
            <span class="expense-meta-divider"></span>
            <span>{{ expense.department }}</span>
            <span class="expense-meta-divider"></span>
            <span>{{ expense.owner }}</span>
          </div>
        </div>

        <div class="expense-status-panel">
          <div class="expense-status-icon">
            <span class="material-symbols-outlined">{{ expenseIcon }}</span>
          </div>
          <div class="expense-status-copy">
            <strong>{{ expenseStatusTitle }}</strong>
            <p>{{ expenseStatusText }}</p>
            <small>{{ expense.status }}</small>
          </div>
        </div>
      </section>

      <section class="expense-meta-board">
        <article v-for="item in metaItems" :key="item.label" class="expense-meta-card">
          <div class="expense-meta-icon">
            <span class="material-symbols-outlined">{{ item.icon }}</span>
          </div>
          <div class="expense-meta-copy">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </article>
      </section>

      <section class="expense-content-grid">
        <article class="expense-surface">
          <div class="expense-surface-head">
            <div>
              <p class="expense-surface-kicker">شرح هزینه</p>
              <h3>توضیحات ثبت‌شده</h3>
              <small v-if="loading">در حال بارگذاری...</small>
            </div>
          </div>

          <div class="expense-description-box">
            <p>{{ expense.description || 'توضیحی برای این هزینه ثبت نشده است.' }}</p>
          </div>
        </article>

        <div class="expense-side-stack">
          <article class="expense-surface">
            <div class="expense-surface-head">
              <div>
                <p class="expense-surface-kicker">اسناد</p>
                <h3>فاکتور و مستندات</h3>
                <small>فایل فاکتور از این بخش قابل باز کردن است.</small>
              </div>
            </div>

            <div v-if="expense.invoiceUrl" class="expense-file-stage">
              <a class="action-btn tone-primary" :href="expense.invoiceUrl" target="_blank" rel="noreferrer">
                <span class="material-symbols-outlined">description</span>
                <span>مشاهده فاکتور</span>
              </a>
            </div>
            <div v-else class="expense-file-empty">
              <div class="expense-file-badge">
                <span class="material-symbols-outlined">description</span>
              </div>
              <strong>فاکتور ثبت نشده است</strong>
              <p>برای این هزینه هنوز فایلی بارگذاری نشده است.</p>
            </div>
          </article>

          <article v-if="canApproveSelectedExpense" class="expense-surface">
            <div class="expense-surface-head">
              <div>
                <p class="expense-surface-kicker">اقدام</p>
                <h3>تصمیم نهایی روی هزینه</h3>
              </div>
            </div>

            <label class="expense-reject-note">
              <span>علت رد</span>
              <textarea v-model="rejectReason" class="field-shell expense-reject-textarea" rows="4" placeholder="در صورت نیاز علت رد را وارد کنید"></textarea>
            </label>

            <div class="expense-action-row">
              <button class="action-btn tone-soft" type="button" @click="$emit('close')">
                <span class="material-symbols-outlined">close</span>
                <span>بستن</span>
              </button>
              <button class="action-btn tone-danger" type="button" @click="handleReject">
                <span class="material-symbols-outlined">cancel</span>
                <span>رد</span>
              </button>
              <button class="action-btn tone-primary" type="button" @click="approveSelectedExpense">
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
.expense-modal-shell {
  display: grid;
  gap: 22px;
  padding: 8px 4px 4px;
}

.expense-hero,
.expense-surface,
.expense-meta-card {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(38, 56, 92, 0.08);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 248, 252, 0.96)),
    var(--surface);
  box-shadow: 0 22px 50px rgba(28, 42, 76, 0.08);
}

.expense-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(280px, 0.9fr);
  gap: 18px;
  padding: 24px;
  border-radius: 30px;
}

.expense-hero::before,
.expense-surface::before {
  content: '';
  position: absolute;
  inset: auto auto -40% -10%;
  width: 220px;
  height: 220px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(72, 103, 183, 0.12), transparent 70%);
  pointer-events: none;
}

.expense-hero-copy,
.expense-status-copy,
.expense-meta-copy {
  display: grid;
  gap: 8px;
}

.expense-hero-copy h2 {
  margin: 0;
  font-size: clamp(28px, 2.3vw, 38px);
  line-height: 1.3;
  color: #203255;
}

.expense-hero-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  color: var(--muted);
  font-size: 13px;
}

.expense-type-pill {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(72, 103, 183, 0.1);
  color: var(--primary);
  font-weight: 800;
}

.expense-meta-divider {
  width: 5px;
  height: 5px;
  border-radius: 999px;
  background: rgba(82, 96, 126, 0.4);
}

.expense-status-panel {
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

.expense-status-icon,
.expense-meta-icon,
.expense-file-badge {
  display: grid;
  place-items: center;
}

.expense-status-icon {
  width: 64px;
  height: 64px;
  border-radius: 22px;
  font-size: 28px;
  color: #fff;
  background: linear-gradient(135deg, #4d67b2, #314783);
}

.expense-status-copy strong {
  font-size: 20px;
  color: #203255;
}

.expense-status-copy p,
.expense-status-copy small,
.expense-description-box p,
.expense-file-empty p {
  margin: 0;
  line-height: 1.9;
  color: var(--muted);
}

.expense-meta-board {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.expense-meta-card {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 14px;
  align-items: center;
  padding: 18px;
  border-radius: 24px;
}

.expense-meta-icon {
  width: 46px;
  height: 46px;
  border-radius: 16px;
  background: rgba(72, 103, 183, 0.08);
  color: var(--primary);
}

.expense-meta-copy span {
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
}

.expense-meta-copy strong {
  margin: 0;
  font-size: 16px;
  color: #203255;
  line-height: 1.55;
}

.expense-content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.02fr) minmax(320px, 0.98fr);
  gap: 18px;
}

.expense-side-stack {
  display: grid;
  gap: 18px;
  align-content: start;
}

.expense-surface {
  display: grid;
  gap: 18px;
  padding: 22px;
  border-radius: 28px;
}

.expense-surface-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.expense-surface-kicker {
  margin: 0 0 8px;
  color: var(--muted);
  font-size: 11px;
  letter-spacing: 0.12em;
  font-weight: 800;
}

.expense-surface-head h3 {
  margin: 0;
  font-size: 20px;
  color: #203255;
}

.expense-surface-head small {
  display: block;
  margin-top: 6px;
  line-height: 1.8;
  color: var(--muted);
}

.expense-description-box,
.expense-file-stage,
.expense-file-empty {
  min-height: 220px;
  padding: 20px;
  border-radius: 24px;
  border: 1px dashed rgba(72, 103, 183, 0.2);
  background: linear-gradient(180deg, rgba(248, 250, 254, 0.94), rgba(240, 244, 250, 0.96));
}

.expense-file-stage,
.expense-file-empty {
  display: grid;
  place-items: center;
  text-align: center;
  gap: 12px;
}

.expense-file-badge {
  width: 68px;
  height: 68px;
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(72, 103, 183, 0.14), rgba(225, 233, 255, 0.92));
  color: #3f58a2;
}

.expense-file-empty strong {
  font-size: 20px;
  color: #203255;
}

.expense-reject-note {
  display: grid;
  gap: 10px;
}

.expense-reject-note > span {
  font-size: 12px;
  font-weight: 800;
  color: var(--muted);
}

.expense-reject-textarea {
  min-height: 126px;
  background: rgba(255, 255, 255, 0.76);
}

.expense-action-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.expense-modal-shell.is-approved .expense-status-icon {
  background: linear-gradient(135deg, #23936d, #176f52);
}

.expense-modal-shell.is-rejected .expense-status-icon {
  background: linear-gradient(135deg, #d36363, #ab4343);
}

.expense-modal-shell.is-pending .expense-status-icon {
  background: linear-gradient(135deg, #d39d36, #ab7720);
}

@media (max-width: 1100px) {
  .expense-hero,
  .expense-content-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .expense-meta-board {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .expense-modal-shell {
    gap: 16px;
    padding: 0;
  }

  .expense-hero,
  .expense-surface {
    padding: 18px;
    border-radius: 22px;
  }

  .expense-meta-board {
    grid-template-columns: minmax(0, 1fr);
  }

  .expense-status-panel {
    grid-template-columns: minmax(0, 1fr);
  }

  .expense-action-row {
    flex-direction: column;
  }
}
</style>
