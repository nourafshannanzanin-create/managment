<script setup>
import PageHeader from '../components/PageHeader.vue'
import ShamsiDatePicker from '../components/ShamsiDatePicker.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const {
  state,
  priorityLabel,
  departmentLabel,
  managerLabel,
  setRequestFiles,
  removeAttachment,
  submitRequest,
  toggleSidebar,
} = useWorkflowHub()
</script>

<template>
  <section class="page-shell">
    <PageHeader eyebrow="درخواست جدید" title="ثبت درخواست" description="" @menu="toggleSidebar" />

    <div class="request-create-grid">
      <section class="surface-block">
        <div class="section-label-row">
          <h2>اطلاعات اصلی</h2>
        </div>

        <div class="form-stack">
          <label class="field-shell">
            <span>عنوان</span>
            <input v-model="state.requestForm.title" type="text" placeholder="" />
          </label>

          <label class="field-shell">
            <span>واحد</span>
            <select v-model="state.requestForm.department">
              <option value="">انتخاب</option>
              <option value="it">فناوری اطلاعات</option>
              <option value="finance">امور مالی</option>
              <option value="hr">منابع انسانی</option>
              <option value="ops">عملیات</option>
              <option value="marketing">بازاریابی</option>
            </select>
          </label>

          <label class="field-shell">
            <span>توضیحات</span>
            <textarea v-model="state.requestForm.description" rows="7" placeholder=""></textarea>
          </label>
        </div>
      </section>

      <section class="surface-block">
        <div class="section-label-row">
          <h2>تأیید</h2>
        </div>

        <div class="form-stack">
          <label class="field-shell">
            <span>مدیر</span>
            <select v-model="state.requestForm.manager">
              <option value="">انتخاب</option>
              <option value="sara-ahmadi">سارا احمدی</option>
              <option value="hamid-rezaei">حمید رضایی</option>
              <option value="navid-farhadi">نوید فرهادی</option>
              <option value="niloufar-farahmand">نیلوفر فرهمند</option>
            </select>
          </label>

          <label class="field-shell">
            <span>تاریخ</span>
            <ShamsiDatePicker v-model="state.requestForm.deadline" model-type="jalali" placeholder="" />
          </label>

          <div class="priority-strip">
            <button :class="['priority-chip', state.requestForm.priority === 'low' && 'is-active']" @click="state.requestForm.priority = 'low'">پایین</button>
            <button :class="['priority-chip', state.requestForm.priority === 'medium' && 'is-active']" @click="state.requestForm.priority = 'medium'">متوسط</button>
            <button :class="['priority-chip', state.requestForm.priority === 'high' && 'is-active']" @click="state.requestForm.priority = 'high'">بالا</button>
            <button :class="['priority-chip', state.requestForm.priority === 'critical' && 'is-active']" @click="state.requestForm.priority = 'critical'">بحرانی</button>
          </div>
        </div>
      </section>

      <section class="surface-block">
        <div class="section-label-row">
          <h2>ضمیمه</h2>
        </div>

        <label class="upload-pad">
          <input type="file" multiple @change="setRequestFiles($event.target.files)" />
          <span class="material-symbols-outlined">cloud_upload</span>
          <strong>افزودن فایل</strong>
          <small>PDF, Excel, Word, PNG, JPG</small>
        </label>

        <div v-if="state.requestForm.attachments.length" class="file-list">
          <article v-for="(file, index) in state.requestForm.attachments" :key="`${file.name}-${index}`" class="file-row">
            <div>
              <strong>{{ file.name }}</strong>
              <small>{{ Math.round(file.size / 1024) }} KB</small>
            </div>
            <button class="icon-btn" @click="removeAttachment(index)">
              <span class="material-symbols-outlined">delete</span>
            </button>
          </article>
        </div>
      </section>

      <section class="surface-block request-summary-card">
        <div class="section-label-row">
          <h2>خلاصه</h2>
        </div>

        <div class="summary-block request-summary">
          <div>
            <span>عنوان</span>
            <strong>{{ state.requestForm.title || '' }}</strong>
          </div>
          <div>
            <span>واحد</span>
            <strong>{{ departmentLabel(state.requestForm.department) }}</strong>
          </div>
          <div>
            <span>مدیر</span>
            <strong>{{ managerLabel(state.requestForm.manager) }}</strong>
          </div>
          <div>
            <span>اولویت</span>
            <strong>{{ priorityLabel(state.requestForm.priority) }}</strong>
          </div>
        </div>

        <button class="action-btn tone-primary request-submit-btn" @click="submitRequest">
          <span class="material-symbols-outlined">send</span>
          <span>ثبت</span>
        </button>
      </section>
    </div>
  </section>
</template>
