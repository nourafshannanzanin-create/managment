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
const approvalStatusClass = computed(() => {
  const status = String(props.approval?.status || '')
  if (status.includes('تایید')) return 'bg-emerald-50 border border-emerald-200'
  if (status.includes('رد')) return 'bg-rose-50 border border-rose-200'
  return 'bg-white border border-outline/20'
})
const approvalStatusMessage = computed(() => {
  const status = String(props.approval?.status || '')
  if (status.includes('تایید')) return 'این سند تایید شده و نسخه امضاشده آن روی خود فایل ذخیره شده است.'
  if (status.includes('رد')) return 'این سند رد شده است و در این مرحله قابل تایید نیست.'
  return 'برای این سند می‌توانید تایید یا رد ثبت کنید.'
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
          <strong>{{ approval.risk }}</strong>
        </div>
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
            <small>پیش نمایش موجود نیست</small>
          </div>
        </div>
      </section>

      <section v-if="approval.signedSignature" class="modal-section">
        <div class="section-label-row">
          <h3>امضای ثبت شده</h3>
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
        <div :class="approvalStatusClass" class="rounded-xl p-4">
          <p class="m-0 mb-3 text-sm text-on-surface-variant">{{ approvalStatusMessage }}</p>
          <textarea v-if="approval.canApprove" v-model="rejectReason" rows="3" placeholder="علت رد"></textarea>
          <div class="action-group modal-actions">
            <button class="action-btn tone-soft" @click="$emit('close')">
              <span class="material-symbols-outlined">close</span>
              <span>بستن</span>
            </button>
            <button v-if="approval.canApprove" class="action-btn tone-primary" @click="approveSelectedDocument">
              <span class="material-symbols-outlined">check_circle</span>
              <span>تایید</span>
            </button>
            <button v-if="approval.canApprove" class="action-btn tone-danger" @click="handleReject">
              <span class="material-symbols-outlined">cancel</span>
              <span>رد</span>
            </button>
          </div>
        </div>
      </section>
    </div>
  </BaseModal>
</template>
