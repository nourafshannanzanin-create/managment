<script setup>
import { computed, ref, watch } from 'vue'

import BaseModal from './BaseModal.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const props = defineProps({
  open: { type: Boolean, default: false },
  approval: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})

defineEmits(['close'])

const rejectReason = ref('')
const rejectOpen = ref(false)
const previewObjectUrl = ref('')
const previewLoading = ref(false)

const {
  approveSelectedDocument,
  rejectSelectedDocument,
  loadSignature,
  openSignatureComposer,
  signatureState,
  state,
  openProtectedFile,
  downloadProtectedFile,
  createProtectedObjectUrl,
} = useWorkflowHub()

const previewKind = computed(() => props.approval?.previewKind || 'file')
const isImage = computed(() => previewKind.value === 'image')
const isPdf = computed(() => previewKind.value === 'pdf')
const previewUrl = computed(() => props.approval?.previewUrl || '')
const downloadUrl = computed(() => props.approval?.downloadUrl || '')
const hasStandalonePreview = computed(() => Boolean(previewUrl.value) && previewUrl.value !== downloadUrl.value)
const isApproved = computed(() => String(props.approval?.status || '').includes('تایید'))
const isRejected = computed(() => String(props.approval?.status || '').includes('رد'))
const canSubmitApproval = computed(() => Boolean(props.approval?.canApprove) && signatureState.hasSignature)

const statusTone = computed(() => {
  if (isApproved.value) return 'is-approved'
  if (isRejected.value) return 'is-rejected'
  return 'is-pending'
})

const statusIcon = computed(() => {
  if (isApproved.value) return 'verified'
  if (isRejected.value) return 'cancel'
  return 'schedule'
})

const statusMessage = computed(() => {
  if (isApproved.value) return 'سند تایید شده و نسخه نهایی از همین مسیر در دسترس است.'
  if (isRejected.value) return 'این سند رد شده است و برای ادامه نیاز به بازبینی یا ثبت مجدد دارد.'
  return 'سند هنوز در گردش تایید است و تصمیم نهایی از همین پنجره ثبت می‌شود.'
})

const previewTitle = computed(() => {
  if (isImage.value) return 'پیش نمایش مستقیم سند'
  if (isPdf.value) return 'پیش نمایش PDF'
  return 'پیش نمایش داخلی برای این فایل موجود نیست'
})

const previewHint = computed(() => {
  if (isImage.value) return 'نسخه فعلی سند در همین پنجره نمایش داده می‌شود.'
  if (isPdf.value) return 'فایل PDF داخل همین مودال بارگذاری می‌شود و در صورت نیاز می‌توانید آن را جداگانه هم باز یا دانلود کنید.'
  return 'برای بررسی محتوا، فایل را در زبانه جدا باز کنید یا مستقیما دانلود بگیرید.'
})

const metaItems = computed(() => {
  if (!props.approval) return []
  return [
    { label: 'کد سند', value: props.approval.id, icon: 'badge' },
    { label: 'ثبت کننده', value: props.approval.owner, icon: 'person' },
    { label: 'بخش', value: props.approval.department, icon: 'apartment' },
    { label: 'نوع', value: props.approval.type, icon: 'description' },
    { label: 'وضعیت', value: props.approval.status, icon: statusIcon.value },
    { label: 'ریسک', value: props.approval.risk || '-', icon: 'flag' },
  ]
})

function revokePreviewObjectUrl() {
  if (!previewObjectUrl.value) return
  URL.revokeObjectURL(previewObjectUrl.value)
  previewObjectUrl.value = ''
}

async function loadInlinePreview() {
  revokePreviewObjectUrl()
  if (!props.open || !previewUrl.value || (!isImage.value && !isPdf.value)) return
  previewLoading.value = true
  try {
    previewObjectUrl.value = await createProtectedObjectUrl(previewUrl.value)
  } catch (error) {
    state.lastError = error.message || 'بارگذاری پیش نمایش انجام نشد.'
  } finally {
    previewLoading.value = false
  }
}

async function handleReject() {
  await rejectSelectedDocument(rejectReason.value)
  rejectOpen.value = false
}

async function handleApprove() {
  await approveSelectedDocument()
}

async function handlePreviewOpen() {
  await openProtectedFile(previewUrl.value, props.approval?.id || 'document-preview')
}

async function handleDownload() {
  await downloadProtectedFile(downloadUrl.value, props.approval?.id || 'document')
}

watch(
  () => [props.open, props.approval?.id, props.approval?.canApprove, previewUrl.value, previewKind.value],
  async ([open, _, canApprove]) => {
    rejectReason.value = ''
    rejectOpen.value = false
    revokePreviewObjectUrl()
    if (!open) return
    state.lastError = ''
    await loadInlinePreview()
    if (canApprove) {
      await loadSignature()
    }
  },
  { immediate: true },
)
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div v-if="approval" class="approval-modal-shell" :class="statusTone">
      <section class="approval-hero">
        <div class="approval-hero-copy">
          <p class="page-eyebrow">جزئیات تاییدیه</p>
          <h2>{{ approval.title }}</h2>
          <div class="approval-hero-meta">
            <span class="approval-type-pill">{{ approval.type }}</span>
            <span class="approval-meta-divider"></span>
            <span>{{ approval.department }}</span>
            <span class="approval-meta-divider"></span>
            <span>{{ approval.owner }}</span>
          </div>
        </div>

        <div class="approval-status-panel">
          <div class="approval-status-icon">
            <span class="material-symbols-outlined">{{ statusIcon }}</span>
          </div>
          <div class="approval-status-copy">
            <strong>{{ approval.status }}</strong>
            <p>{{ statusMessage }}</p>
            <small v-if="approval.decisionNote">{{ approval.decisionNote }}</small>
          </div>
        </div>
      </section>

      <section class="approval-meta-board">
        <article v-for="item in metaItems" :key="item.label" class="approval-meta-card">
          <div class="approval-meta-icon">
            <span class="material-symbols-outlined">{{ item.icon }}</span>
          </div>
          <div class="approval-meta-copy">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </article>
      </section>

      <section class="approval-content-grid">
        <article class="approval-surface approval-document-surface">
          <div class="approval-surface-head">
            <div>
              <p class="approval-surface-kicker">سند</p>
              <h3>فایل و پیش نمایش</h3>
              <small>{{ previewHint }}</small>
            </div>
            <div class="approval-file-actions">
              <button
                v-if="hasStandalonePreview"
                class="action-btn tone-soft"
                type="button"
                @click="handlePreviewOpen"
              >
                <span class="material-symbols-outlined">open_in_new</span>
                <span>باز کردن فایل</span>
              </button>
              <button
                v-if="downloadUrl"
                class="action-btn tone-primary"
                type="button"
                @click="handleDownload"
              >
                <span class="material-symbols-outlined">download</span>
                <span>{{ isApproved ? 'دانلود نسخه نهایی' : 'دانلود سند' }}</span>
              </button>
            </div>
          </div>

          <div class="approval-preview-stage">
            <div v-if="previewLoading" class="approval-preview-empty">
              <div class="approval-preview-badge">
                <span class="material-symbols-outlined">progress_activity</span>
              </div>
              <strong>در حال بارگذاری پیش نمایش</strong>
              <p>چند لحظه صبر کنید تا فایل برای نمایش داخل مودال آماده شود.</p>
            </div>
            <img v-else-if="isImage && previewObjectUrl" :src="previewObjectUrl" alt="" class="approval-preview-image" />
            <iframe
              v-else-if="isPdf && previewObjectUrl"
              :src="previewObjectUrl"
              class="approval-preview-frame"
              title="PDF preview"
            ></iframe>
            <div v-else-if="previewUrl" class="approval-preview-empty">
              <div class="approval-preview-badge">
                <span class="material-symbols-outlined">{{ isPdf ? 'picture_as_pdf' : 'attach_file' }}</span>
              </div>
              <strong>{{ previewTitle }}</strong>
              <p>{{ previewHint }}</p>
            </div>
            <div v-else class="approval-preview-empty">
              <div class="approval-preview-badge">
                <span class="material-symbols-outlined">description</span>
              </div>
              <strong>فایل قابل نمایش موجود نیست</strong>
              <p>برای این سند فایل یا پیش نمایش معتبری ثبت نشده است.</p>
            </div>
          </div>
        </article>

        <div class="approval-side-stack">
          <article v-if="approval.signedSignature" class="approval-surface approval-signature-surface">
            <div class="approval-surface-head">
              <div>
                <p class="approval-surface-kicker">امضا</p>
                <h3>امضای ثبت شده</h3>
              </div>
            </div>
            <div class="approval-signature-frame">
              <img :src="approval.signedSignature" alt="signature" />
            </div>
          </article>

          <article class="approval-surface approval-action-surface">
            <div class="approval-surface-head">
              <div>
                <p class="approval-surface-kicker">اقدام</p>
                <h3>تصمیم نهایی روی سند</h3>
                <small v-if="loading">در حال بارگذاری...</small>
              </div>
            </div>

            <div v-if="approval.canApprove" class="signature-readiness-card" :class="{ 'is-ready': signatureState.hasSignature }">
              <div class="signature-readiness-icon">
                <span class="material-symbols-outlined">{{ signatureState.hasSignature ? 'gesture' : 'draw' }}</span>
              </div>
              <div class="signature-readiness-copy">
                <strong>{{ signatureState.hasSignature ? 'امضای دیجیتال آماده است' : 'پیش از تایید، امضا لازم است' }}</strong>
                <p>
                  {{ signatureState.hasSignature
                    ? 'امضای فعلی شما هنگام تایید روی نسخه نهایی سند اعمال می‌شود.'
                    : 'ابتدا امضای خود را ثبت یا ویرایش کنید، سپس تایید را انجام دهید.' }}
                </p>
              </div>
              <button class="action-btn tone-soft" type="button" @click="openSignatureComposer">
                <span class="material-symbols-outlined">draw</span>
                <span>{{ signatureState.hasSignature ? 'ویرایش امضا' : 'ثبت امضا' }}</span>
              </button>
            </div>

            <p v-if="state.lastError" class="inline-error">{{ state.lastError }}</p>

            <div class="approval-action-row">
              <button class="action-btn tone-soft" type="button" @click="$emit('close')">
                <span class="material-symbols-outlined">close</span>
                <span>بستن</span>
              </button>
              <button
                v-if="approval.canApprove"
                class="action-btn tone-danger"
                type="button"
                :disabled="loading"
                @click="rejectOpen = true"
              >
                <span class="material-symbols-outlined">cancel</span>
                <span>رد</span>
              </button>
              <button
                v-if="approval.canApprove"
                class="action-btn tone-primary"
                type="button"
                :disabled="loading || signatureState.loading || !canSubmitApproval"
                @click="handleApprove"
              >
                <span class="material-symbols-outlined">check_circle</span>
                <span>تایید</span>
              </button>
            </div>
          </article>
        </div>
      </section>
    </div>
  </BaseModal>

  <BaseModal :open="rejectOpen" size="sm" @close="rejectOpen = false">
    <div class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">علت رد</p>
        <h2>توضیح رد تاییدیه</h2>
      </div>

      <label class="field-shell approval-reject-note">
        <span>علت رد</span>
        <textarea
          v-model.trim="rejectReason"
          class="approval-reject-textarea"
          rows="4"
          placeholder="دلیل رد این سند را بنویسید."
        ></textarea>
      </label>

      <div class="modal-actions">
        <button class="action-btn tone-soft" type="button" @click="rejectOpen = false">
          <span class="material-symbols-outlined">close</span>
          <span>بستن</span>
        </button>
        <button
          class="action-btn tone-danger"
          type="button"
          :disabled="loading || !rejectReason.trim()"
          @click="handleReject"
        >
          <span class="material-symbols-outlined">cancel</span>
          <span>ثبت رد</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
.approval-modal-shell {
  display: grid;
  gap: 22px;
  padding: 8px 4px 4px;
}

.approval-hero,
.approval-surface,
.approval-meta-card {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(38, 56, 92, 0.08);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 248, 252, 0.96)),
    var(--surface);
  box-shadow: 0 22px 50px rgba(28, 42, 76, 0.08);
}

.approval-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(280px, 0.9fr);
  gap: 18px;
  padding: 24px;
  border-radius: 30px;
}

.approval-hero::before,
.approval-surface::before {
  content: '';
  position: absolute;
  inset: auto auto -40% -10%;
  width: 220px;
  height: 220px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(72, 103, 183, 0.12), transparent 70%);
  pointer-events: none;
}

.approval-hero-copy,
.approval-status-copy,
.approval-meta-copy,
.signature-readiness-copy {
  display: grid;
  gap: 8px;
}

.approval-hero-copy h2 {
  margin: 0;
  font-size: clamp(28px, 2.3vw, 38px);
  line-height: 1.3;
  color: #203255;
}

.approval-hero-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  color: var(--muted);
  font-size: 13px;
}

.approval-type-pill {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(72, 103, 183, 0.1);
  color: var(--primary);
  font-weight: 800;
}

.approval-meta-divider {
  width: 5px;
  height: 5px;
  border-radius: 999px;
  background: rgba(82, 96, 126, 0.4);
}

.approval-status-panel {
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

.approval-status-icon,
.approval-meta-icon,
.approval-preview-badge,
.signature-readiness-icon {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
}

.approval-status-icon {
  width: 64px;
  height: 64px;
  border-radius: 22px;
  font-size: 28px;
  color: #fff;
  background: linear-gradient(135deg, #4d67b2, #314783);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.28);
}

.approval-status-icon .material-symbols-outlined {
  font-size: 28px;
}

.approval-status-copy strong {
  font-size: 20px;
  color: #203255;
}

.approval-status-copy p,
.approval-status-copy small {
  margin: 0;
  line-height: 1.9;
  color: var(--muted);
}

.approval-meta-board {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.approval-meta-card {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 14px;
  align-items: center;
  padding: 18px;
  border-radius: 24px;
}

.approval-meta-icon {
  width: 46px;
  height: 46px;
  border-radius: 16px;
  background: rgba(72, 103, 183, 0.08);
  color: var(--primary);
}

.approval-meta-icon .material-symbols-outlined {
  font-size: 22px;
}

.approval-meta-copy span {
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
}

.approval-meta-copy strong {
  margin: 0;
  font-size: 16px;
  color: #203255;
  line-height: 1.55;
}

.approval-content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.28fr) minmax(320px, 0.88fr);
  gap: 18px;
}

.approval-side-stack {
  display: grid;
  gap: 18px;
  align-content: start;
}

.approval-surface {
  display: grid;
  gap: 18px;
  padding: 22px;
  border-radius: 28px;
}

.approval-surface-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.approval-surface-kicker {
  margin: 0 0 8px;
  color: var(--muted);
  font-size: 11px;
  letter-spacing: 0.12em;
  font-weight: 800;
}

.approval-surface-head h3 {
  margin: 0;
  font-size: 20px;
  color: #203255;
}

.approval-surface-head small {
  display: block;
  margin-top: 6px;
  line-height: 1.8;
  color: var(--muted);
}

.approval-file-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.approval-preview-stage {
  min-height: 320px;
  border-radius: 24px;
  border: 1px dashed rgba(72, 103, 183, 0.2);
  background:
    linear-gradient(180deg, rgba(248, 250, 254, 0.94), rgba(240, 244, 250, 0.96)),
    var(--surface);
  display: grid;
  place-items: center;
  padding: 22px;
}

.approval-preview-image,
.approval-preview-frame {
  width: 100%;
  border: 0;
  border-radius: 18px;
  box-shadow: 0 16px 40px rgba(29, 44, 79, 0.12);
  background: #fff;
}

.approval-preview-image {
  max-height: 520px;
  object-fit: contain;
}

.approval-preview-frame {
  min-height: 560px;
}

.approval-preview-empty {
  display: grid;
  justify-items: center;
  gap: 12px;
  text-align: center;
  max-width: 420px;
}

.approval-preview-badge {
  width: 68px;
  height: 68px;
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(72, 103, 183, 0.14), rgba(225, 233, 255, 0.92));
  color: #3f58a2;
}

.approval-preview-badge .material-symbols-outlined {
  font-size: 34px;
}

.approval-preview-empty strong {
  font-size: 20px;
  color: #203255;
}

.approval-preview-empty p {
  margin: 0;
  color: var(--muted);
  line-height: 1.9;
}

.approval-signature-frame {
  min-height: 150px;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(253, 253, 255, 0.96), rgba(242, 245, 250, 0.94));
  border: 1px solid rgba(72, 103, 183, 0.1);
  display: grid;
  place-items: center;
  padding: 18px;
}

.approval-signature-frame img {
  max-width: 100%;
  max-height: 100px;
  object-fit: contain;
}

.signature-readiness-card {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 14px;
  align-items: center;
  padding: 16px;
  border-radius: 22px;
  border: 1px solid rgba(215, 158, 52, 0.16);
  background: linear-gradient(180deg, rgba(255, 249, 236, 0.95), rgba(255, 245, 221, 0.9));
}

.signature-readiness-card.is-ready {
  border-color: rgba(35, 147, 107, 0.16);
  background: linear-gradient(180deg, rgba(238, 251, 246, 0.94), rgba(229, 247, 239, 0.92));
}

.signature-readiness-icon {
  width: 50px;
  height: 50px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.7);
  color: #b57900;
}

.signature-readiness-card.is-ready .signature-readiness-icon {
  color: #1f815e;
}

.signature-readiness-copy strong {
  color: #203255;
}

.signature-readiness-copy p {
  margin: 0;
  line-height: 1.8;
  color: var(--muted);
}

.approval-reject-note {
  display: grid;
  gap: 10px;
}

.approval-reject-note > span {
  font-size: 12px;
  font-weight: 800;
  color: var(--muted);
}

.approval-reject-textarea {
  min-height: 126px;
  background: rgba(255, 255, 255, 0.76);
}

.approval-action-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.inline-error {
  margin: 0;
}

.approval-modal-shell.is-approved .approval-status-icon {
  background: linear-gradient(135deg, #23936d, #176f52);
}

.approval-modal-shell.is-rejected .approval-status-icon {
  background: linear-gradient(135deg, #d36363, #ab4343);
}

.approval-modal-shell.is-pending .approval-status-icon {
  background: linear-gradient(135deg, #d39d36, #ab7720);
}

@media (max-width: 1100px) {
  .approval-hero,
  .approval-content-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .approval-meta-board {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .approval-modal-shell {
    gap: 16px;
    padding: 0;
  }

  .approval-hero,
  .approval-surface {
    padding: 18px;
    border-radius: 22px;
  }

  .approval-meta-board {
    grid-template-columns: minmax(0, 1fr);
  }

  .approval-status-panel,
  .signature-readiness-card {
    grid-template-columns: minmax(0, 1fr);
  }

  .approval-preview-frame {
    min-height: 420px;
  }

  .approval-surface-head,
  .approval-file-actions,
  .approval-action-row {
    justify-content: stretch;
  }

  .approval-file-actions,
  .approval-action-row {
    flex-direction: column;
  }
}
</style>
