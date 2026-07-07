<script setup>
import { reactive, ref } from 'vue'

import BaseModal from '../components/BaseModal.vue'
import ErrorNotice from '../components/ErrorNotice.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const form = reactive({
  email: 'milad_dhs',
  password: 'milad_dhs@123',
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
:global(.app-shell.is-auth-route .shell-content) { max-width: none; padding: 0; }
:global(.app-shell.is-auth-route .shell-main) { min-width: 0; }
.stitch-login-page { position: relative; min-height: 100vh; padding: 24px; overflow: hidden; font-family: 'Vazirmatn', sans-serif; background-color: #f7f1eb; background-image: radial-gradient(at 0% 0%, rgba(229, 195, 166, 0.34) 0px, transparent 50%), radial-gradient(at 100% 0%, rgba(124, 129, 173, 0.22) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(229, 195, 166, 0.3) 0px, transparent 50%), radial-gradient(at 0% 100%, rgba(75, 82, 126, 0.2) 0px, transparent 50%); }
.stitch-login-page::before { content: ''; position: absolute; inset: 0; background-image: radial-gradient(rgba(46, 67, 116, 0.06) 1px, transparent 1px); background-size: 30px 30px; }
.stitch-login-grid { position: relative; z-index: 1; width: 100%; max-width: 1440px; min-height: calc(100vh - 48px); margin: 0 auto; display: flex; flex-direction: row-reverse; gap: 42px; align-items: center; justify-content: center; }
.stitch-brand-panel, .stitch-form-panel { position: relative; overflow: hidden; border: 1px solid rgba(255,255,255,.5); background: rgba(255,255,255,.7); box-shadow: 0 20px 25px -5px rgba(0,0,0,.05), 0 10px 10px -5px rgba(0,0,0,.02); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); }
.stitch-brand-panel { flex: 1 1 auto; min-height: 750px; border-radius: 2.5rem; padding: 4.5rem 4.75rem; display: none; flex-direction: column; justify-content: space-between; border-right: 4px solid rgba(46,67,116,.18); }
.stitch-form-panel { width: min(100%, 560px); border-radius: 2rem; padding: 2rem; }
.stitch-brand-copy { position: relative; z-index: 1; display: grid; justify-items: end; }
.stitch-chip { display: inline-flex; align-items: center; gap: .75rem; margin-bottom: 2.25rem; padding: .625rem 1.15rem; border: 1px solid rgba(46,67,116,.12); border-radius: 999px; background: rgba(229,195,166,.24); color: #4B527E; font-size: .95rem; font-weight: 800; }
.stitch-chip-dot { width: .55rem; height: .55rem; border-radius: 999px; background: #E5C3A6; box-shadow: 0 0 0 6px rgba(229,195,166,.26); }
.stitch-brand-copy h1 { margin: 0; color: #2E4374; font-size: clamp(3rem, 5vw, 4.75rem); line-height: 1.08; font-weight: 900; }
.stitch-brand-copy h1 span { color: #4B527E; }
.stitch-brand-copy p { max-width: 36rem; margin: 1.75rem 0 0; color: rgba(46,67,116,.74); font-size: 1.05rem; line-height: 2rem; text-align: right; }
.stitch-stat-row { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.stitch-stat-row article { padding: 18px; border-radius: 20px; background: rgba(255,255,255,.72); border: 1px solid rgba(46,67,116,.1); display: grid; gap: 6px; }
.stitch-stat-row strong { color: #2E4374; }
.stitch-stat-row small { color: #697890; }
.stitch-brand-rings { position: absolute; inset: auto auto -24% -12%; width: 28rem; height: 28rem; opacity: .22; color: rgba(75,82,126,.38); }
.stitch-brand-rings svg, .stitch-brand-rings circle { width: 100%; height: 100%; stroke: currentColor; }
.stitch-form-header span { color: #7d8798; font-size: 13px; font-weight: 800; }
.stitch-form-header h2 { margin: 6px 0 0; color: #24345b; font-size: 32px; }
.stitch-form { display: grid; gap: 16px; margin-top: 28px; }
.stitch-field-group { display: grid; gap: 8px; }
.stitch-field-group span { color: #5f6f89; font-weight: 700; }
.stitch-field-group input { min-height: 52px; border-radius: 16px; border: 1px solid rgba(36,59,107,.12); background: rgba(255,255,255,.9); padding: 0 16px; }
.stitch-form-meta { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.stitch-checkbox-row { display: inline-flex; align-items: center; gap: 10px; color: #5f6f89; }
.link-btn { border: 0; background: transparent; color: #2E4374; font-weight: 800; cursor: pointer; }
.stitch-submit-btn { min-height: 56px; border: 0; border-radius: 18px; background: linear-gradient(135deg, #2E4374, #4B527E); color: #fff; display: inline-flex; align-items: center; justify-content: center; gap: 10px; font-weight: 900; cursor: pointer; }
.stitch-submit-btn svg { width: 22px; height: 22px; }
.stitch-footer-note { margin: 22px 0 0; color: #7d8798; text-align: center; }
.stitch-footer-note span { color: #2E4374; font-weight: 900; }
.registration-documents small { color: #70809a; font-size: 12px; }
.registration-success { margin: 0; padding: 12px 14px; border: 1px solid rgba(32, 132, 94, .2); border-radius: 14px; background: rgba(32, 132, 94, .08); color: #176946; font-size: 13px; font-weight: 800; line-height: 1.8; }
@media (min-width: 980px) { .stitch-brand-panel { display: flex; } }
</style>
