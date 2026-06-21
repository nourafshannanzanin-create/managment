<script setup>
import { ref, watch } from 'vue'

import BaseModal from './BaseModal.vue'
import SignaturePad from './SignaturePad.vue'
import { useWorkflowHub } from '../stores/workflowHub'

defineProps({
  open: { type: Boolean, default: false },
})

defineEmits(['close'])

const signatureDraft = ref('')
const { signatureState, saveSignature } = useWorkflowHub()

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
        <h2>ثبت امضای دیجیتال</h2>
      </div>

      <SignaturePad v-model="signatureDraft" />

      <div class="action-group modal-actions">
        <button class="action-btn tone-soft" @click="$emit('close')">
          <span class="material-symbols-outlined">close</span>
          <span>بستن</span>
        </button>
        <button class="action-btn tone-primary" :disabled="signatureState.loading || !signatureDraft" @click="saveSignature(signatureDraft)">
          <span class="material-symbols-outlined">draw</span>
          <span>{{ signatureState.loading ? 'در حال ذخیره...' : 'ذخیره امضا' }}</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>
