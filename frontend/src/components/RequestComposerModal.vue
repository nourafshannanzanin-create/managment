<script setup>
import { computed } from 'vue'

import BaseModal from './BaseModal.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const props = defineProps({
  open: { type: Boolean, default: false },
  form: { type: Object, required: true },
  step: { type: Number, required: true },
  submitting: { type: Boolean, default: false },
})

defineEmits(['close'])

const {
  requestCompletion,
  nextComposerStep,
  prevComposerStep,
  setRequestFiles,
  removeAttachment,
  submitRequest,
  priorityLabel,
  departmentLabel,
  managerLabel,
} = useWorkflowHub()

const stepTitle = computed(() => {
  return {
    1: 'اطلاعات اصلی',
    2: 'مسیر تأیید',
    3: 'ضمیمه و جمع‌بندی',
  }[props.step]
})
</script>

<template>
  <BaseModal :open="open" size="composer" @close="$emit('close')">
    <div class="composer-layout">
      <div class="modal-headline compact">
        <p class="page-eyebrow">درخواست جدید</p>
        <h2>{{ stepTitle }}</h2>
        <p>{{ requestCompletion }}% از فرم تکمیل شده است.</p>
      </div>

      <div class="step-dots">
        <span :class="['step-dot', step >= 1 && 'is-active']"></span>
        <span :class="['step-dot', step >= 2 && 'is-active']"></span>
        <span :class="['step-dot', step >= 3 && 'is-active']"></span>
      </div>

      <div v-if="step === 1" class="form-stack">
        <label class="field-shell">
          <span>عنوان درخواست</span>
          <input v-model="form.title" type="text" placeholder="عنوان کوتاه و شفاف" />
        </label>
        <label class="field-shell">
          <span>واحد</span>
          <select v-model="form.department">
            <option value="">انتخاب کنید</option>
            <option value="it">فناوری اطلاعات</option>
            <option value="finance">امور مالی</option>
            <option value="hr">منابع انسانی</option>
            <option value="ops">عملیات</option>
            <option value="marketing">بازاریابی</option>
          </select>
        </label>
        <label class="field-shell">
          <span>توضیحات</span>
          <textarea v-model="form.description" rows="6" placeholder="شرح خلاصه، هدف و نیازمندی‌ها"></textarea>
        </label>
      </div>

      <div v-else-if="step === 2" class="form-stack">
        <label class="field-shell">
          <span>مدیر تأییدکننده</span>
          <select v-model="form.manager">
            <option value="">انتخاب مدیر</option>
            <option value="sara-ahmadi">سارا احمدی</option>
            <option value="hamid-rezaei">حمید رضایی</option>
            <option value="navid-farhadi">نوید فرهادی</option>
            <option value="niloufar-farahmand">نیلوفر فرهمند</option>
          </select>
        </label>
        <label class="field-shell">
          <span>مهلت انجام</span>
          <input v-model="form.deadline" type="date" />
        </label>

        <div class="priority-strip">
          <button :class="['priority-chip', form.priority === 'low' && 'is-active']" @click="form.priority = 'low'">پایین</button>
          <button :class="['priority-chip', form.priority === 'medium' && 'is-active']" @click="form.priority = 'medium'">متوسط</button>
          <button :class="['priority-chip', form.priority === 'high' && 'is-active']" @click="form.priority = 'high'">بالا</button>
          <button :class="['priority-chip', form.priority === 'critical' && 'is-active']" @click="form.priority = 'critical'">بحرانی</button>
        </div>
      </div>

      <div v-else class="form-stack">
        <label class="upload-pad">
          <input type="file" multiple @change="setRequestFiles($event.target.files)" />
          <span class="material-symbols-outlined">cloud_upload</span>
          <strong>فایل‌ها را انتخاب کنید</strong>
          <small>PDF, Word, Excel, JPG, PNG</small>
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

        <section class="summary-block">
          <div>
            <span>عنوان</span>
            <strong>{{ form.title || '---' }}</strong>
          </div>
          <div>
            <span>واحد</span>
            <strong>{{ departmentLabel(form.department) }}</strong>
          </div>
          <div>
            <span>مدیر</span>
            <strong>{{ managerLabel(form.manager) }}</strong>
          </div>
          <div>
            <span>اولویت</span>
            <strong>{{ priorityLabel(form.priority) }}</strong>
          </div>
        </section>
      </div>

      <div class="action-group split">
        <button v-if="step > 1" class="action-btn tone-soft" @click="prevComposerStep">
          <span class="material-symbols-outlined">arrow_forward</span>
          <span>مرحله قبل</span>
        </button>
        <button class="action-btn tone-soft" @click="$emit('close')">
          <span class="material-symbols-outlined">close</span>
          <span>انصراف</span>
        </button>
        <button v-if="step < 3" class="action-btn tone-primary" @click="nextComposerStep">
          <span class="material-symbols-outlined">arrow_back</span>
          <span>مرحله بعد</span>
        </button>
        <button v-else class="action-btn tone-primary" :disabled="submitting" @click="submitRequest">
          <span class="material-symbols-outlined">send</span>
          <span>{{ submitting ? 'در حال ارسال...' : 'ثبت و ارسال' }}</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>
