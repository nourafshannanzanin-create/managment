<script setup>
import { computed, ref } from 'vue'

import BaseModal from './BaseModal.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const props = defineProps({
  open: { type: Boolean, default: false },
  approval: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})

defineEmits(['close'])

const rejectReason = ref('')
const { approveSelectedDocument, rejectSelectedDocument } = useWorkflowHub()

const previewKind = computed(() => props.approval?.previewKind || 'file')
const isImage = computed(() => previewKind.value === 'image')
const isPdf = computed(() => previewKind.value === 'pdf')
const previewUrl = computed(() => props.approval?.previewUrl || '')
const downloadUrl = computed(() => props.approval?.downloadUrl || previewUrl.value)
const isApproved = computed(() => String(props.approval?.status || '').includes('تایید'))
const isRejected = computed(() => String(props.approval?.status || '').includes('رد'))

const statusToneClass = computed(() => {
  if (isApproved.value) return 'detail-status-card is-approved'
  if (isRejected.value) return 'detail-status-card is-rejected'
  return 'detail-status-card is-pending'
})

const statusMessage = computed(() => {
  if (isApproved.value) return 'این سند تایید شده و در صورت وجود نسخه امضاشده، دانلود همین فایل نسخه نهایی را در اختیار شما می‌گذارد.'
  if (isRejected.value) return 'این سند رد شده است و برای ادامه نیاز به بازبینی یا ثبت مجدد دارد.'
  return 'این سند هنوز در گردش تایید است و می‌توانید از همین پنجره برای آن تصمیم ثبت کنید.'
})

async function handleReject() {
  await rejectSelectedDocument(rejectReason.value)
}
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div v-if="approval" class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">جزئیات تاییدیه</p>
        <h2>{{ approval.title }}</h2>
      </div>

      <section class="detail-meta-grid">
        <div class="detail-meta-item">
          <span>کد</span>
          <strong>{{ approval.id }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>ثبت‌کننده</span>
          <strong>{{ approval.owner }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>بخش</span>
          <strong>{{ approval.department }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>نوع</span>
          <strong>{{ approval.type }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>وضعیت</span>
          <strong>{{ approval.status }}</strong>
        </div>
        <div class="detail-meta-item">
          <span>ریسک</span>
          <strong>{{ approval.risk || '-' }}</strong>
        </div>
      </section>

      <section :class="statusToneClass">
        <div>
          <strong>{{ approval.status }}</strong>
          <p>{{ statusMessage }}</p>
          <small v-if="approval.decisionNote">{{ approval.decisionNote }}</small>
        </div>
        <a v-if="downloadUrl" class="action-btn tone-primary" :href="downloadUrl" target="_blank" rel="noreferrer">
          <span class="material-symbols-outlined">download</span>
          <span>{{ isApproved ? 'دانلود نسخه نهایی' : 'دانلود سند' }}</span>
        </a>
      </section>

      <section class="modal-section viewer-panel">
        <div class="preview-frame">
          <img v-if="isImage" :src="previewUrl" alt="" />
          <object v-else-if="isPdf && previewUrl" :data="previewUrl" type="application/pdf" class="document-object">
            <div class="preview-empty">
              <span class="material-symbols-outlined">picture_as_pdf</span>
              <a :href="downloadUrl" class="table-link">دانلود فایل PDF</a>
            </div>
          </object>
          <div v-else-if="previewUrl" class="preview-empty">
            <span class="material-symbols-outlined">attach_file</span>
            <a :href="downloadUrl" class="table-link">دانلود فایل</a>
          </div>
          <div v-else class="preview-empty">
            <span class="material-symbols-outlined">description</span>
            <small>پیش‌نمایش موجود نیست</small>
          </div>
        </div>
      </section>

      <section v-if="approval.signedSignature" class="modal-section">
        <div class="section-label-row">
          <h3>امضای ثبت‌شده</h3>
        </div>
        <div class="signed-preview">
          <img :src="approval.signedSignature" alt="signature" />
        </div>
      </section>

      <section class="modal-section">
        <div class="section-label-row">
          <h3>اقدام</h3>
          <small v-if="loading">در حال بارگذاری...</small>
        </div>
        <textarea v-if="approval.canApprove" v-model="rejectReason" class="field-shell" rows="3" placeholder="علت رد"></textarea>
        <div class="action-group modal-actions">
          <button class="action-btn tone-soft" type="button" @click="$emit('close')">
            <span class="material-symbols-outlined">close</span>
            <span>بستن</span>
          </button>
          <button v-if="approval.canApprove" class="action-btn tone-primary" type="button" @click="approveSelectedDocument">
            <span class="material-symbols-outlined">check_circle</span>
            <span>تایید</span>
          </button>
          <button v-if="approval.canApprove" class="action-btn tone-danger" type="button" @click="handleReject">
            <span class="material-symbols-outlined">cancel</span>
            <span>رد</span>
          </button>
        </div>
      </section>
    </div>
  </BaseModal>
</template>
