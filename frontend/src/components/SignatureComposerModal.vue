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
const { signatureState, saveSignature, state } = useWorkflowHub()
const isEditing = computed(() => signatureState.hasSignature && Boolean(signatureState.signatureData))

watch(
  () => signatureState.signatureData,
  (value) => {
    signatureDraft.value = value || ''
  },
  { immediate: true },
)
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">امضای مدیر</p>
        <h2>{{ isEditing ? 'ویرایش امضای دیجیتال' : 'ثبت امضای دیجیتال' }}</h2>
      </div>

      <section v-if="isEditing" class="modal-section">
        <div class="section-label-row">
          <h3>امضای فعلی</h3>
        </div>
        <div class="signed-preview">
          <img :src="signatureState.signatureData" alt="signature" />
        </div>
      </section>

      <section class="modal-section">
        <div class="section-label-row">
          <h3>{{ isEditing ? 'ویرایش امضا' : 'ثبت امضا' }}</h3>
          <small>{{ isEditing ? 'برای تغییر امضا، روی همان کادر دوباره امضا کنید.' : 'امضای خود را داخل کادر زیر ثبت کنید.' }}</small>
        </div>
        <SignaturePad v-model="signatureDraft" />
      </section>

      <p v-if="state.lastError" class="inline-error">{{ state.lastError }}</p>

      <div class="action-group modal-actions">
        <button class="action-btn tone-soft" type="button" @click="$emit('close')">
          <span class="material-symbols-outlined">close</span>
          <span>بستن</span>
        </button>
        <button class="action-btn tone-primary" type="button" :disabled="signatureState.loading || !signatureDraft" @click="saveSignature(signatureDraft)">
          <span class="material-symbols-outlined">draw</span>
          <span>{{ signatureState.loading ? 'در حال ذخیره...' : (isEditing ? 'ذخیره ویرایش' : 'ذخیره امضا') }}</span>
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
</style>
