<script setup>
import BaseModal from './BaseModal.vue'
import ShamsiDatePicker from './ShamsiDatePicker.vue'
import { useWorkflowHub } from '../stores/workflowHub'

defineProps({
  open: { type: Boolean, default: false },
  form: { type: Object, required: true },
  submitting: { type: Boolean, default: false },
})

defineEmits(['close'])

const { state, setExpenseInvoice, submitExpense } = useWorkflowHub()
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">هزینه جدید</p>
        <h2>ثبت هزینه</h2>
      </div>

      <label class="field-shell">
        <span>شرح</span>
        <textarea v-model="form.description" rows="4"></textarea>
      </label>

      <div class="modal-grid three-col">
        <label class="field-shell">
          <span>مبلغ</span>
          <input v-model="form.amount" type="number" min="0" />
        </label>

        <label class="field-shell">
          <span>تاریخ</span>
          <ShamsiDatePicker v-model="form.expenseDate" model-type="jalali" placeholder="1405/04/01" />
        </label>

        <label class="field-shell">
          <span>بخش</span>
          <select v-model="form.department">
            <option value="">انتخاب بخش</option>
            <option v-for="item in state.directories.departments" :key="item.code" :value="item.code">{{ item.name }}</option>
          </select>
        </label>
      </div>

      <label class="upload-pad compact-upload">
        <input type="file" accept="image/*,.pdf" @change="setExpenseInvoice($event.target.files?.[0])" />
        <span class="material-symbols-outlined">receipt_long</span>
        <strong>{{ form.invoice?.name || 'افزودن فاکتور' }}</strong>
        <small>اختیاری</small>
      </label>

      <div class="action-group modal-actions">
        <button class="action-btn tone-soft" @click="$emit('close')">
          <span class="material-symbols-outlined">close</span>
          <span>بستن</span>
        </button>
        <button class="action-btn tone-primary" :disabled="submitting" @click="submitExpense">
          <span class="material-symbols-outlined">payments</span>
          <span>{{ submitting ? 'در حال ثبت...' : 'ثبت هزینه' }}</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>
