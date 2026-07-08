<script setup>
import { computed, ref, watch } from 'vue'

import BaseModal from './BaseModal.vue'
import SignaturePad from './SignaturePad.vue'
import { useWorkflowHub } from '../stores/workflowHub'

defineProps({
  open: { type: Boolean, default: false },
})

defineEmits(['close'])

const signatureDraft = ref('')
const stampDraft = ref('')
const stampFileName = ref('')
const readingStamp = ref(false)
const { signatureState, saveSignature, state } = useWorkflowHub()

const isEditing = computed(() => signatureState.hasSignature && Boolean(signatureState.signatureData))
const hasStamp = computed(() => Boolean(stampDraft.value))

watch(
  () => signatureState.signatureData,
  (value) => {
    signatureDraft.value = value || ''
  },
  { immediate: true },
)

watch(
  () => signatureState.stampData,
  (value) => {
    stampDraft.value = value || ''
    if (!value) stampFileName.value = ''
  },
  { immediate: true },
)

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error('خواندن فایل مهر انجام نشد.'))
    reader.readAsDataURL(file)
  })
}

async function handleStampChange(event) {
  const [file] = Array.from(event.target.files || [])
  if (!file) return
  readingStamp.value = true
  state.lastError = ''
  try {
    stampDraft.value = await readFileAsDataUrl(file)
    stampFileName.value = file.name || 'stamp'
  } catch (error) {
    state.lastError = error.message || 'بارگذاری فایل مهر انجام نشد.'
  } finally {
    readingStamp.value = false
    event.target.value = ''
  }
}

function clearStamp() {
  stampDraft.value = ''
  stampFileName.value = ''
}
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">امضا و مهر مدیر</p>
        <h2>{{ isEditing || signatureState.hasStamp ? 'ویرایش امضا و مهر' : 'ثبت امضا و بارگذاری مهر' }}</h2>
      </div>

      <section v-if="isEditing" class="modal-section">
        <div class="section-label-row">
          <h3>امضای فعلی</h3>
        </div>
        <div class="signed-preview">
          <img :src="signatureState.signatureData" alt="signature" />
        </div>
      </section>

      <section v-if="signatureState.hasStamp" class="modal-section">
        <div class="section-label-row">
          <h3>مهر فعلی</h3>
          <small>بک‌گراند سفید بعد از ذخیره حذف می‌شود.</small>
        </div>
        <div class="stamp-preview-frame">
          <img :src="signatureState.stampData" alt="stamp" class="stamp-preview-image" />
        </div>
      </section>

      <section class="modal-section">
        <div class="section-label-row">
          <h3>{{ isEditing ? 'ویرایش امضا' : 'ثبت امضا' }}</h3>
          <small>امضای خود را داخل کادر زیر ثبت کنید.</small>
        </div>
        <SignaturePad v-model="signatureDraft" />
      </section>

      <section class="modal-section">
        <div class="section-label-row">
          <h3>بارگذاری مهر</h3>
          <small>اختیاری. تصویر مهر را از روی برگه سفید انتخاب کنید تا نسخه شفاف ذخیره شود.</small>
        </div>

        <label class="stamp-upload-shell">
          <input accept="image/*" class="stamp-upload-input" type="file" @change="handleStampChange" />
          <span class="material-symbols-outlined">upload_file</span>
          <strong>{{ readingStamp ? 'در حال خواندن فایل...' : 'انتخاب فایل مهر' }}</strong>
          <small>{{ stampFileName || 'PNG, JPG, WEBP' }}</small>
        </label>

        <div v-if="hasStamp" class="stamp-preview-frame is-draft">
          <img :src="stampDraft" alt="stamp draft" class="stamp-preview-image" />
        </div>

        <div v-if="hasStamp" class="modal-actions stamp-actions">
          <button class="action-btn tone-soft" type="button" @click="clearStamp">
            <span class="material-symbols-outlined">delete</span>
            <span>حذف مهر</span>
          </button>
        </div>
      </section>

      <p v-if="state.lastError" class="inline-error">{{ state.lastError }}</p>

      <div class="action-group modal-actions">
        <button class="action-btn tone-soft" type="button" @click="$emit('close')">
          <span class="material-symbols-outlined">close</span>
          <span>بستن</span>
        </button>
        <button
          class="action-btn tone-primary"
          type="button"
          :disabled="signatureState.loading || readingStamp || !signatureDraft"
          @click="saveSignature(signatureDraft, stampDraft)"
        >
          <span class="material-symbols-outlined">draw</span>
          <span>{{ signatureState.loading ? 'در حال ذخیره...' : 'ذخیره امضا' }}</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
.inline-error {
  margin: 0;
  color: #b42318;
  font-size: 0.92rem;
}

.stamp-upload-shell,
.stamp-preview-frame {
  border: 1px solid rgba(72, 103, 183, 0.14);
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(243, 246, 252, 0.96));
}

.stamp-upload-shell {
  position: relative;
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 22px;
  text-align: center;
  cursor: pointer;
}

.stamp-upload-input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.stamp-upload-shell .material-symbols-outlined {
  font-size: 32px;
  color: #3b5aa8;
}

.stamp-upload-shell strong {
  color: #203255;
}

.stamp-upload-shell small {
  color: var(--muted);
}

.stamp-preview-frame {
  display: grid;
  place-items: center;
  min-height: 170px;
  padding: 18px;
}

.stamp-preview-frame.is-draft {
  background-image:
    linear-gradient(45deg, rgba(82, 96, 126, 0.08) 25%, transparent 25%),
    linear-gradient(-45deg, rgba(82, 96, 126, 0.08) 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, rgba(82, 96, 126, 0.08) 75%),
    linear-gradient(-45deg, transparent 75%, rgba(82, 96, 126, 0.08) 75%);
  background-size: 18px 18px;
  background-position: 0 0, 0 9px, 9px -9px, -9px 0;
}

.stamp-preview-image {
  max-width: 100%;
  max-height: 140px;
  object-fit: contain;
}

.stamp-actions {
  justify-content: flex-start;
}
</style>
