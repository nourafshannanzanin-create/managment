<script setup>
import PageHeader from '../components/PageHeader.vue'
import ShamsiDatePicker from '../components/ShamsiDatePicker.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const {
  state,
  priorityLabel,
  departmentLabel,
  managerLabel,
  requestManagerAssigneeNames,
  requestManagerAssigneeOptions,
  setRequestManager,
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
              <option v-for="item in state.directories.departments" :key="item.code" :value="item.code">{{ item.name }}</option>
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
            <span>ارجاع به مدیر</span>
            <select :value="state.requestForm.manager" required @change="setRequestManager($event.target.value)">
              <option value="" disabled>انتخاب مدیر</option>
              <option v-for="item in state.directories.managers" :key="item.slug" :value="item.slug">{{ item.name }}</option>
            </select>
          </label>

          <label class="field-shell">
            <span>ارجاع به ...</span>
            <select v-model="state.requestForm.managerAssigneeIds" multiple :disabled="!state.requestForm.manager">
              <option value="">هیچکدام</option>
              <option v-for="item in requestManagerAssigneeOptions" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
          </label>

          <label class="field-shell">
            <span>تاریخ</span>
            <ShamsiDatePicker v-model="state.requestForm.deadline" model-type="jalali" placeholder="" />
          </label>

          <div class="priority-strip">
            <button :class="['priority-chip', state.requestForm.priority === 'low' && 'is-active']" type="button" @click="state.requestForm.priority = 'low'">پایین</button>
            <button :class="['priority-chip', state.requestForm.priority === 'medium' && 'is-active']" type="button" @click="state.requestForm.priority = 'medium'">متوسط</button>
            <button :class="['priority-chip', state.requestForm.priority === 'high' && 'is-active']" type="button" @click="state.requestForm.priority = 'high'">بالا</button>
            <button :class="['priority-chip', state.requestForm.priority === 'critical' && 'is-active']" type="button" @click="state.requestForm.priority = 'critical'">بحرانی</button>
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
            <button class="icon-btn" type="button" @click="removeAttachment(index)">
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
            <span>مدیران</span>
            <strong>{{ requestManagerAssigneeNames() }}</strong>
          </div>
          <div>
            <span>اولویت</span>
            <strong>{{ priorityLabel(state.requestForm.priority) }}</strong>
          </div>
        </div>

        <button class="action-btn tone-primary request-submit-btn" type="button" @click="submitRequest">
          <span class="material-symbols-outlined">send</span>
          <span>ثبت</span>
        </button>
      </section>
    </div>
  </section>
</template>
