<script setup>
import { ref } from 'vue'

import BaseModal from './BaseModal.vue'
import { useWorkflowHub } from '../stores/workflowHub'

defineProps({
  open: { type: Boolean, default: false },
  approval: { type: Object, default: null },
})

defineEmits(['close'])

const rejectReason = ref('نیازمند بازبینی')
const { approveSelectedDocument, rejectSelectedDocument } = useWorkflowHub()

async function handleReject() {
  await rejectSelectedDocument(rejectReason.value)
}
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div v-if="approval" class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">جزئیات تأییدیه</p>
        <h2>{{ approval.title }}</h2>
        <p>{{ approval.summary }}</p>
      </div>

      <section class="detail-meta-grid">
        <div class="detail-meta-item">
          <span>کد</span>
          <strong>{{ approval.id }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>مالک</span>
          <strong>{{ approval.owner }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>نوع سند</span>
          <strong>{{ approval.type }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>واحد</span>
          <strong>{{ approval.department }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>وضعیت</span>
          <strong>{{ approval.status }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>ریسک</span>
          <strong>{{ approval.risk }}</strong>
        </div>
      </section>

      <section class="modal-section viewer-panel">
        <span class="material-symbols-outlined">description</span>
        <div>
          <h3>پیش‌نمایش سند</h3>
          <p>در این نسخه، نمایشگر سند به‌صورت خلاصه و سبک نگه داشته شده است.</p>
        </div>
      </section>

      <section class="modal-section">
        <div class="section-label-row">
          <h3>اقدام سریع</h3>
        </div>
        <textarea v-model="rejectReason" rows="3" placeholder="دلیل رد سند را وارد کنید"></textarea>
        <div class="action-group">
          <button class="action-btn tone-soft" @click="$emit('close')">
            <span class="material-symbols-outlined">visibility</span>
            <span>بستن</span>
          </button>
          <button class="action-btn tone-primary" @click="approveSelectedDocument">
            <span class="material-symbols-outlined">check_circle</span>
            <span>تأیید</span>
          </button>
          <button class="action-btn tone-danger" @click="handleReject">
            <span class="material-symbols-outlined">cancel</span>
            <span>رد</span>
          </button>
        </div>
      </section>
    </div>
  </BaseModal>
</template>
