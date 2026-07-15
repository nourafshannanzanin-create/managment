<script setup>
import { reactive, ref } from 'vue'

import BaseModal from '../components/BaseModal.vue'
import ErrorNotice from '../components/ErrorNotice.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const form = reactive({
  email: '',
  password: '',
  remember: false,
})

const signupOpen = ref(false)
const registrationSent = ref(false)
const signup = reactive({
  organizationName: '',
  managerName: '',
  managerUsername: '',
  managerEmail: '',
  managerPhone: '',
  managerPassword: '',
  documents: [],
})

const { login, navigateTo, registerOrganization, state } = useWorkflowHub()

async function handleLogin() {
  const ok = await login(form.email, form.password)
  if (ok) navigateTo('/dashboard')
}

async function handleSignup() {
  registrationSent.value = false
  const ok = await registerOrganization({ ...signup, documents: [...signup.documents] })
  if (!ok) return
  signupOpen.value = false
  registrationSent.value = true
}

function setRegistrationDocuments(event) {
  signup.documents = Array.from(event.target.files || [])
}
</script>

<template>
  <section class="stitch-login-page">
    <div class="stitch-login-grid">
      <section class="stitch-brand-panel" aria-hidden="true">
        <div class="stitch-brand-copy">
          <div class="stitch-chip">
            <span class="stitch-chip-dot"></span>
            <span>سامانه کارنومند</span>
          </div>
          <h1>ورود به<br /><span>پنل سازمانی</span></h1>
          <p>ورود و ثبت نام مجموعه به صورت داینامیک به بک‌اند متصل است و اطلاعات مستقیم در دیتابیس ثبت می‌شود.</p>
        </div>
        <div class="stitch-brand-bottom">
          <div class="stitch-stat-row">
            <article><strong>ورود</strong><small>با نام کاربری یا ایمیل</small></article>
            <article><strong>ثبت نام</strong><small>ایجاد مجموعه و مدیر اصلی</small></article>
          </div>
        </div>
        <div class="stitch-brand-rings" aria-hidden="true">
          <svg fill="none" viewBox="0 0 400 400"><circle cx="200" cy="200" r="199.5" /><circle cx="200" cy="200" r="149.5" /><circle cx="200" cy="200" r="99.5" /></svg>
        </div>
      </section>

      <section class="stitch-form-panel">
        <div class="stitch-form-header">
          <span>دسترسی سامانه</span>
          <h2>حساب سازمانی</h2>
        </div>

        <form class="stitch-form" @submit.prevent="handleLogin">
          <label class="stitch-field-group" for="login-email">
            <span>نام کاربری / ایمیل</span>
            <input id="login-email" v-model="form.email" autocomplete="username" dir="ltr" placeholder="username" type="text" />
          </label>

          <label class="stitch-field-group" for="login-password">
            <span>رمز عبور</span>
            <input id="login-password" v-model="form.password" autocomplete="current-password" dir="ltr" placeholder="••••••••" type="password" />
          </label>

          <ErrorNotice :error="state.lastErrorDetails" compact />
          <p v-if="registrationSent" class="registration-success">درخواست ثبت‌نام و مدارک شما ارسال شد. پس از بررسی پشتیبانی، حساب مجموعه فعال می‌شود.</p>

          <div class="stitch-form-meta">
            <button class="link-btn" type="button" @click="signupOpen = true">ثبت نام مجموعه</button>
            <label class="stitch-checkbox-row"><span>مرا به خاطر بسپار</span><input v-model="form.remember" type="checkbox" /></label>
          </div>

          <button class="stitch-submit-btn" :disabled="state.loginPending" type="submit">
            <span>{{ state.loginPending ? 'در حال ورود...' : 'ورود به سیستم' }}</span>
            <svg fill="none" viewBox="0 0 24 24"><path d="M17 8l4 4m0 0l-4 4m4-4H3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" /></svg>
          </button>
        </form>

        <p class="stitch-footer-note">© 2026 تمامی حقوق متعلق به <span>کارنومند</span> است</p>
      </section>
    </div>
  </section>

  <BaseModal :open="signupOpen" size="detail" @close="signupOpen = false">
    <div class="detail-layout">
      <div class="modal-headline"><p class="page-eyebrow">ثبت نام</p><h2>درخواست ایجاد مجموعه</h2></div>
      <div class="modal-grid two-col">
        <label class="field-shell"><span>نام مجموعه</span><input v-model.trim="signup.organizationName" required /></label>
        <label class="field-shell"><span>نام مدیر</span><input v-model.trim="signup.managerName" required /></label>
        <label class="field-shell"><span>نام کاربری مدیر</span><input v-model.trim="signup.managerUsername" dir="ltr" required /></label>
        <label class="field-shell"><span>ایمیل مدیر</span><input v-model.trim="signup.managerEmail" dir="ltr" type="email" placeholder="اختیاری" /></label>
        <label class="field-shell"><span>تلفن مدیر</span><input v-model.trim="signup.managerPhone" dir="ltr" required /></label>
      </div>
      <label class="field-shell"><span>رمز عبور مدیر</span><input v-model="signup.managerPassword" dir="ltr" type="password" minlength="6" required /></label>
      <label class="field-shell registration-documents">
        <span>تصویر جواز و مدارک مجموعه</span>
        <input type="file" accept="image/*,.pdf" multiple required @change="setRegistrationDocuments" />
        <small>{{ signup.documents.length ? `${signup.documents.length} فایل انتخاب شد` : 'حداقل یک فایل الزامی است' }}</small>
      </label>
      <ErrorNotice :error="state.lastErrorDetails" compact />
      <div class="modal-actions"><button class="action-btn tone-soft" type="button" @click="signupOpen = false">بستن</button><button class="action-btn tone-primary" type="button" :disabled="state.loginPending || !signup.documents.length" @click="handleSignup">{{ state.loginPending ? 'در حال ارسال...' : 'ارسال درخواست ثبت نام' }}</button></div>
    </div>
  </BaseModal>
</template>

<style scoped>
:global(.app-shell.is-auth-route .shell-content) {
  max-width: none;
  padding: 0;
}

:global(.app-shell.is-auth-route .shell-main) {
  min-width: 0;
}

.stitch-login-page {
  min-height: 100vh;
  padding: 24px;
  overflow: hidden;
  color: #344054;
  background: #f6f7f9;
}

.stitch-login-grid {
  width: min(1120px, 100%);
  min-height: calc(100vh - 48px);
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 480px);
  gap: 24px;
  align-items: center;
}

.stitch-brand-panel,
.stitch-form-panel {
  border: 1px solid #e4e7ec;
  border-radius: 12px;
  background: #fff;
}

.stitch-brand-panel {
  min-height: 560px;
  padding: 32px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.stitch-form-panel {
  padding: 32px;
}

.stitch-brand-copy {
  display: grid;
  justify-items: start;
  gap: 16px;
}

.stitch-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border: 1px solid #e4e7ec;
  border-radius: 999px;
  background: #f9fafb;
  color: #667085;
  font-size: 12px;
  font-weight: 600;
}

.stitch-chip-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #2563eb;
}

.stitch-brand-copy h1 {
  margin: 0;
  color: #111827;
  font-size: clamp(2rem, 4vw, 3.75rem);
  line-height: 1.15;
  font-weight: 650;
}

.stitch-brand-copy h1 span {
  color: #111827;
}

.stitch-brand-copy p {
  max-width: 42rem;
  margin: 0;
  color: #667085;
  font-size: 15px;
  line-height: 2;
  text-align: right;
}

.stitch-stat-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.stitch-stat-row article {
  padding: 16px;
  border-radius: 10px;
  background: #f9fafb;
  border: 1px solid #e4e7ec;
  display: grid;
  gap: 6px;
}

.stitch-stat-row strong,
.stitch-form-header h2,
.stitch-footer-note span {
  color: #111827;
  font-weight: 650;
}

.stitch-stat-row small,
.stitch-form-header span,
.stitch-footer-note {
  color: #667085;
}

.stitch-brand-rings {
  display: none;
}

.stitch-form-header h2 {
  margin: 6px 0 0;
  font-size: 28px;
}

.stitch-form {
  display: grid;
  gap: 16px;
  margin-top: 28px;
}

.stitch-field-group {
  display: grid;
  gap: 8px;
}

.stitch-field-group span {
  color: #344054;
  font-weight: 600;
}

.stitch-field-group input {
  min-height: 44px;
  border-radius: 8px;
  border: 1px solid #d0d5dd;
  background: #fff;
  color: #111827;
  padding: 0 12px;
}

.stitch-field-group input::placeholder {
  color: #98a2b3;
}

.stitch-field-group input:focus {
  border-color: #2563eb;
  outline: 2px solid rgba(37, 99, 235, 0.16);
  outline-offset: 1px;
}

.stitch-form-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.stitch-checkbox-row {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #667085;
}

.link-btn {
  border: 0;
  background: transparent;
  color: #2563eb;
  font-weight: 650;
  cursor: pointer;
}

.stitch-submit-btn {
  min-height: 44px;
  border: 1px solid #2563eb;
  border-radius: 8px;
  background: #2563eb;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-weight: 650;
  cursor: pointer;
}

.stitch-submit-btn:disabled {
  opacity: .7;
  cursor: wait;
}

.stitch-submit-btn svg {
  width: 20px;
  height: 20px;
}

.stitch-footer-note {
  margin: 22px 0 0;
  text-align: center;
}

.registration-documents small {
  color: #667085;
  font-size: 12px;
}

.registration-success {
  margin: 0;
  padding: 12px 14px;
  border: 1px solid #abefc6;
  border-radius: 8px;
  background: #ecfdf3;
  color: #067647;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.8;
}

@media (max-width: 920px) {
  .stitch-login-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .stitch-brand-panel {
    min-height: auto;
  }
}

@media (max-width: 720px) {
  .stitch-login-page {
    padding: 12px;
  }

  .stitch-login-grid {
    min-height: calc(100vh - 24px);
  }

  .stitch-brand-panel,
  .stitch-form-panel {
    padding: 20px;
  }
}
</style>
