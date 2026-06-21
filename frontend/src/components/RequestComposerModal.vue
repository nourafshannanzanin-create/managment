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

const { state, setRequestFiles, removeAttachment, submitRequest } = useWorkflowHub()
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">درخواست جدید</p>
        <h2>ثبت درخواست سازمانی</h2>
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

        <label class="field-shell">
          <span>ارجاع به</span>
          <select v-model="form.manager">
            <option value="">انتخاب مدیر</option>
            <option v-for="item in state.directories.managers" :key="item.slug" :value="item.slug">{{ item.name }}</option>
          </select>
        </label>

        <label class="field-shell">
          <span>تاریخ</span>
          <ShamsiDatePicker v-model="form.deadline" model-type="jalali" placeholder="1405/04/01" />
        </label>
      </div>

      <label class="field-shell">
        <span>توضیحات</span>
        <textarea v-model="form.description" rows="5"></textarea>
      </label>

      <div class="segmented-row">
        <button :class="['priority-chip', form.priority === 'low' && 'is-active']" @click="form.priority = 'low'">پایین</button>
        <button :class="['priority-chip', form.priority === 'medium' && 'is-active']" @click="form.priority = 'medium'">متوسط</button>
        <button :class="['priority-chip', form.priority === 'high' && 'is-active']" @click="form.priority = 'high'">بالا</button>
        <button :class="['priority-chip', form.priority === 'critical' && 'is-active']" @click="form.priority = 'critical'">بحرانی</button>
      </div>

      <label class="upload-pad compact-upload">
        <input type="file" multiple @change="setRequestFiles($event.target.files)" />
        <span class="material-symbols-outlined">attach_file</span>
        <strong>افزودن پیوست</strong>
        <small>اختیاری</small>
      </label>

      <div v-if="form.attachments.length" class="file-list">
        <article v-for="(file, index) in form.attachments" :key="`${file.name}-${index}`" class="file-row">
          <div>
            <strong>{{ file.name }}</strong>
            <small>{{ Math.round(file.size / 1024) }} KB</small>
          </div>
          <button class="icon-btn" @click="removeAttachment(index)">
            <span class="material-symbols-outlined">delete</span>
          </button>
        </article>
      </div>

      <div class="action-group modal-actions">
        <button class="action-btn tone-soft" @click="$emit('close')">
          <span class="material-symbols-outlined">close</span>
          <span>بستن</span>
        </button>
        <button class="action-btn tone-primary" :disabled="submitting" @click="submitRequest">
          <span class="material-symbols-outlined">send</span>
          <span>{{ submitting ? 'در حال ثبت...' : 'ثبت درخواست' }}</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>
