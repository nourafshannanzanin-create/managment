<script setup>
import BaseModal from './BaseModal.vue'
import { useWorkflowHub } from '../stores/workflowHub'

defineProps({
  open: { type: Boolean, default: false },
  form: { type: Object, required: true },
  submitting: { type: Boolean, default: false },
})

defineEmits(['close'])

const { state, submitUser } = useWorkflowHub()
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">کاربر جدید</p>
        <h2>افزودن کارمند</h2>
      </div>

      <div class="modal-grid two-col">
        <label class="field-shell">
          <span>نام کامل</span>
          <input v-model="form.fullName" type="text" />
        </label>

        <label class="field-shell">
          <span>ایمیل</span>
          <input v-model="form.email" type="email" />
        </label>

        <label class="field-shell">
          <span>رمز عبور</span>
          <input v-model="form.password" type="password" />
        </label>

        <label class="field-shell">
          <span>نوع دسترسی</span>
          <select v-model="form.accessRole">
            <option value="manager">مدیر</option>
            <option value="employee">کارمند</option>
          </select>
        </label>

        <label class="field-shell">
          <span>بخش</span>
          <select v-model="form.department">
            <option value="">انتخاب بخش</option>
            <option v-for="item in state.directories.departments" :key="item.code" :value="item.code">{{ item.name }}</option>
          </select>
        </label>

        <label class="field-shell">
          <span>مدیر مستقیم</span>
          <select v-model="form.managerId">
            <option value="">بدون مدیر</option>
            <option v-for="item in state.directories.managers" :key="item.id" :value="item.id">{{ item.name }}</option>
          </select>
        </label>
      </div>

      <label class="field-shell">
        <span>عنوان شغلی</span>
        <input v-model="form.jobTitle" type="text" />
      </label>

      <div class="action-group modal-actions">
        <button class="action-btn tone-soft" @click="$emit('close')">
          <span class="material-symbols-outlined">close</span>
          <span>بستن</span>
        </button>
        <button class="action-btn tone-primary" :disabled="submitting" @click="submitUser">
          <span class="material-symbols-outlined">person_add</span>
          <span>{{ submitting ? 'در حال ایجاد...' : 'ایجاد کاربر' }}</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>
