<script setup>
import { ref } from 'vue'

import BaseModal from './BaseModal.vue'
import { useWorkflowHub } from '../stores/workflowHub'

defineProps({
  open: { type: Boolean, default: false },
  expense: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})

defineEmits(['close'])

const rejectReason = ref('')
const { canApproveSelectedExpense, approveSelectedExpense, rejectSelectedExpense } = useWorkflowHub()

async function handleReject() {
  await rejectSelectedExpense(rejectReason.value)
}
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div v-if="expense" class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">جزئیات هزینه</p>
        <h2>{{ expense.title }}</h2>
      </div>

      <section class="detail-meta-grid">
        <div class="detail-meta-item">
          <span>کد</span>
          <strong>{{ expense.id }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>ثبت‌کننده</span>
          <strong>{{ expense.owner }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>بخش</span>
          <strong>{{ expense.department }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>نوع</span>
          <strong>{{ expense.category || '-' }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>مبلغ</span>
          <strong>{{ expense.amount }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>وضعیت</span>
          <strong>{{ expense.status }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>تاریخ</span>
          <strong>{{ expense.submittedAt || '-' }}</strong>
        </div>
      </section>

      <section class="modal-section">
        <div class="section-label-row">
          <h3>شرح هزینه</h3>
          <small v-if="loading">در حال بارگذاری...</small>
        </div>
        <div class="detail-note-box">
          <p>{{ expense.description || 'توضیحی برای این هزینه ثبت نشده است.' }}</p>
        </div>
      </section>

      <section class="modal-section">
        <div class="section-label-row">
          <h3>فاکتور</h3>
        </div>
        <a
          v-if="expense.invoiceUrl"
          class="action-btn tone-soft"
          :href="expense.invoiceUrl"
          target="_blank"
          rel="noreferrer"
        >
          <span class="material-symbols-outlined">description</span>
          <span>مشاهده فاکتور</span>
        </a>
        <div v-else class="detail-note-box">
          <p>برای این هزینه فاکتوری بارگذاری نشده است.</p>
        </div>
      </section>

      <section v-if="canApproveSelectedExpense" class="modal-section">
        <div class="section-label-row">
          <h3>اقدام مدیر</h3>
        </div>
        <label class="field-shell">
          <span>علت رد</span>
          <textarea v-model="rejectReason" rows="3" placeholder="در صورت نیاز علت رد را وارد کنید"></textarea>
        </label>
        <div class="modal-actions">
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
      </section>
    </div>
  </BaseModal>
</template>
