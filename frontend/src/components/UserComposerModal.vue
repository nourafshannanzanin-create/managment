<script setup>
import BaseModal from './BaseModal.vue'
import ErrorNotice from './ErrorNotice.vue'
import { useWorkflowHub } from '../stores/workflowHub'

defineProps({
  open: { type: Boolean, default: false },
  form: { type: Object, required: true },
  submitting: { type: Boolean, default: false },
})

defineEmits(['close'])

const { state, fieldHasError, submitUser } = useWorkflowHub()

const sectionAccessOptions = [
  { key: 'users', title: 'کاربران', description: 'دسترسی به فهرست و مدیریت کاربران' },
  { key: 'approvals', title: 'تاییدیه‌ها', description: 'مشاهده و بررسی اسناد و تاییدیه‌ها' },
  { key: 'expenses', title: 'هزینه‌ها', description: 'ثبت، مشاهده و پیگیری هزینه‌ها' },
  { key: 'reports', title: 'گزارشات', description: 'مشاهده گزارش‌های تحلیلی و مدیریتی' },
  { key: 'settings', title: 'تنظیمات', description: 'ورود به تنظیمات سازمان و دسترسی‌ها' },
]
</script>

<template>
  <BaseModal :open="open" size="detail" @close="$emit('close')">
    <div class="detail-layout">
      <div class="modal-headline">
        <p class="page-eyebrow">کاربر جدید</p>
        <h2>افزودن کارمند</h2>
      </div>

      <div class="modal-grid two-col">
        <label :class="['field-shell', fieldHasError('fullName') && 'has-error']">
          <span>نام کامل</span>
          <input v-model="form.fullName" type="text" />
        </label>

        <label :class="['field-shell', fieldHasError('email') && 'has-error']">
          <span>ایمیل</span>
          <input v-model="form.email" type="email" />
        </label>

        <label :class="['field-shell', fieldHasError('password') && 'has-error']">
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

      <section class="surface-inline user-access-panel">
        <div class="section-label-row compact">
          <div>
            <h3>دسترسی بخش‌ها</h3>
            <p>مشخص کنید این کاربر به کدام بخش‌های سایت دسترسی داشته باشد.</p>
          </div>
        </div>

        <div class="modal-grid access-check-grid">
          <label v-for="item in sectionAccessOptions" :key="item.key" class="check-tile">
            <input v-model="form.sectionAccess[item.key]" type="checkbox" />
            <div>
              <strong>{{ item.title }}</strong>
              <small>{{ item.description }}</small>
            </div>
          </label>
        </div>
      </section>

      <ErrorNotice :error="state.lastErrorDetails" compact />

      <div class="action-group modal-actions">
        <button class="action-btn tone-soft" type="button" @click="$emit('close')">
          <span class="material-symbols-outlined">close</span>
          <span>بستن</span>
        </button>
        <button class="action-btn tone-primary" type="button" :disabled="submitting" @click="submitUser">
          <span class="material-symbols-outlined">person_add</span>
          <span>{{ submitting ? 'در حال ایجاد...' : 'ایجاد کاربر' }}</span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
.user-access-panel {
  display: grid;
  gap: 14px;
}

.section-label-row.compact h3,
.section-label-row.compact p {
  margin: 0;
}

.access-check-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.check-tile {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px;
  align-items: start;
  padding: 14px;
  border-radius: 8px;
  border: 1px solid rgba(36, 59, 107, 0.1);
  background: rgba(255, 255, 255, 0.74);
}

.check-tile input {
  margin-top: 4px;
}

.check-tile strong,
.check-tile small {
  display: block;
}

.check-tile small {
  margin-top: 4px;
  color: var(--muted);
}

.inline-error {
  margin: 0;
  color: #b42318;
  font-size: 0.92rem;
}

@media (max-width: 760px) {
  .access-check-grid {
    grid-template-columns: 1fr;
  }
}
</style>
