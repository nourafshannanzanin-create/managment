<script setup>
import BaseModal from './BaseModal.vue'
import { useWorkflowHub } from '../stores/workflowHub'

defineProps({
  open: { type: Boolean, default: false },
  form: { type: Object, required: true },
  submitting: { type: Boolean, default: false },
})

defineEmits(['close'])

const { state, setDocumentFile, submitDocument } = useWorkflowHub()

function toggleAssignee(id) {
  const current = new Set(state.documentForm.assigneeIds)
  if (current.has(id)) current.delete(id)
  else current.add(id)
  state.documentForm.assigneeIds = [...current]
}
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">سند جدید</p>
        <h2>ارسال برای تایید</h2>
      </div>

      <div class="modal-grid two-col">
        <label class="field-shell">
          <span>عنوان</span>
          <input v-model="form.title" type="text" />
        </label>

        <label class="field-shell">
          <span>بخش</span>
          <select v-model="form.department">
            <option value="">انتخاب بخش</option>
            <option v-for="item in state.directories.departments" :key="item.code" :value="item.code">{{ item.name }}</option>
          </select>
        </label>
      </div>

      <label class="field-shell">
        <span>توضیحات</span>
        <textarea v-model="form.description" rows="4"></textarea>
      </label>

      <div class="modal-grid two-col">
        <label class="field-shell">
          <span>نوع سند</span>
          <input v-model="form.documentType" type="text" />
        </label>

        <label class="field-shell">
          <span>ریسک</span>
          <select v-model="form.risk">
            <option value="low">پایین</option>
            <option value="medium">متوسط</option>
            <option value="high">بالا</option>
          </select>
        </label>
      </div>

      <label class="upload-pad compact-upload">
        <input type="file" accept="image/*,.pdf" @change="setDocumentFile($event.target.files?.[0])" />
        <span class="material-symbols-outlined">upload_file</span>
        <strong>{{ form.file?.name || 'افزودن فایل' }}</strong>
        <small>الزامی</small>
      </label>

      <section class="surface-inline">
        <div class="section-label-row">
          <h3>مدیرهای دریافت کننده</h3>
        </div>
        <div class="checkbox-grid">
          <label v-for="item in state.directories.managers" :key="item.id" class="checkbox-card">
            <input
              type="checkbox"
              :checked="form.assigneeIds.includes(item.id)"
              @change="toggleAssignee(item.id)"
            />
            <span>{{ item.name }}</span>
          </label>
        </div>
      </section>

      <div class="action-group modal-actions">
        <button class="action-btn tone-soft" @click="$emit('close')">
          <span class="material-symbols-outlined">close</span>
          <span>بستن</span>
        </button>
        <button class="action-btn tone-primary" :disabled="submitting" @click="submitDocument">
          <span class="material-symbols-outlined">send</span>
          <span>{{ submitting ? 'در حال ارسال...' : 'ثبت سند' }}</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>
