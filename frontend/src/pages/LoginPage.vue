<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import BaseModal from '../components/BaseModal.vue'
import ErrorNotice from '../components/ErrorNotice.vue'
import { getCitiesByProvinceId, provinces } from '../data/iranLocations'
import { useWorkflowHub } from '../stores/workflowHub'

const REMEMBER_KEY = 'workflow-hub-remember-login'

const route = useRoute()

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
  provinceId: 0,
  cityId: 0,
  documents: [],
})

const signupCities = computed(() => (signup.provinceId ? getCitiesByProvinceId(signup.provinceId) : []))
const signupProvinceName = computed(() => provinces.find((item) => item.id === Number(signup.provinceId))?.name || '')
const signupCityName = computed(() => signupCities.value.find((item) => item.id === Number(signup.cityId))?.name || '')

const { login, navigateTo, registerOrganization, setLastError, state } = useWorkflowHub()

function loadRememberedLogin() {
  try {
    const raw = localStorage.getItem(REMEMBER_KEY)
    if (!raw) return
    const saved = JSON.parse(raw)
    if (!saved || typeof saved !== 'object') return
    form.email = String(saved.email || saved.username || '')
    form.password = String(saved.password || '')
    form.remember = Boolean(saved.email || saved.username)
  } catch {
    localStorage.removeItem(REMEMBER_KEY)
  }
}

function persistRememberedLogin() {
  if (form.remember) {
    localStorage.setItem(
      REMEMBER_KEY,
      JSON.stringify({
        email: form.email.trim(),
        password: form.password,
      }),
    )
    return
  }
  localStorage.removeItem(REMEMBER_KEY)
}

function syncSignupQuery() {
  if (route.query.signup === '1' || route.query.register === '1') {
    signupOpen.value = true
  }
}

async function handleLogin() {
  const ok = await login(form.email, form.password)
  if (!ok) return
  persistRememberedLogin()
  navigateTo(state.currentUser.isHq ? '/hq' : '/dashboard')
}

async function handleSignup() {
  registrationSent.value = false
  if (!signup.provinceId || !signup.cityId) {
    setLastError(
      Object.assign(new Error('استان و شهر مجموعه را انتخاب کنید.'), {
        suggestion: 'از فهرست استان و شهر، موقعیت مجموعه را مشخص کنید.',
      }),
      'استان و شهر مجموعه را انتخاب کنید.',
    )
    return
  }
  const ok = await registerOrganization({
    ...signup,
    provinceId: signup.provinceId,
    provinceName: signupProvinceName.value,
    cityId: signup.cityId,
    cityName: signupCityName.value,
    documents: [...signup.documents],
  })
  if (!ok) return
  signupOpen.value = false
  registrationSent.value = true
}

function setRegistrationDocuments(event) {
  signup.documents = Array.from(event.target.files || [])
}

watch(
  () => signup.provinceId,
  () => {
    if (!signupCities.value.some((city) => city.id === Number(signup.cityId))) {
      signup.cityId = 0
    }
  },
)

onMounted(() => {
  loadRememberedLogin()
  syncSignupQuery()
})
watch(() => route.query.signup, syncSignupQuery)
watch(() => route.query.register, syncSignupQuery)
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
          <RouterLink class="stitch-back-home" to="/">بازگشت به صفحه اصلی</RouterLink>
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
            <label class="remember-switch" :class="{ 'is-on': form.remember }">
              <input v-model="form.remember" type="checkbox" class="remember-switch-input" />
              <span class="remember-switch-track" aria-hidden="true">
                <span class="remember-switch-thumb" />
              </span>
              <span class="remember-switch-copy">
                <strong>به‌خاطر سپردن رمز</strong>
                <small>ورود سریع در دفعات بعد</small>
              </span>
            </label>
          </div>

          <button class="stitch-submit-btn" :disabled="state.loginPending" type="submit">
            <span>{{ state.loginPending ? 'در حال ورود...' : 'ورود به سیستم' }}</span>
            <svg fill="none" viewBox="0 0 24 24"><path d="M17 8l4 4m0 0l-4 4m4-4H3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" /></svg>
          </button>
        </form>

        <p class="stitch-footer-note" dir="ltr">Designed By DHS Development Team</p>
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
        <label class="field-shell">
          <span>استان مجموعه</span>
          <select v-model.number="signup.provinceId" required>
            <option :value="0">انتخاب استان</option>
            <option v-for="province in provinces" :key="province.id" :value="province.id">{{ province.name }}</option>
          </select>
        </label>
        <label class="field-shell">
          <span>شهر مجموعه</span>
          <select v-model.number="signup.cityId" :disabled="!signup.provinceId" required>
            <option :value="0">انتخاب شهر</option>
            <option v-for="city in signupCities" :key="city.id" :value="city.id">{{ city.name }}</option>
          </select>
        </label>
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
.stitch-login-page { position: relative; min-height: 100vh; padding: 24px; overflow: hidden; font-family: 'Vazirmatn', sans-serif; background: #18130f url('/images (21).webp') center / cover no-repeat fixed; }
.stitch-login-page::before { content: ''; position: absolute; inset: 0; background: linear-gradient(90deg, rgba(10, 12, 16, 0.42), rgba(10, 12, 16, 0.18) 45%, rgba(255, 255, 255, 0.08)), radial-gradient(circle at 76% 20%, rgba(255, 255, 255, 0.3), transparent 34%); backdrop-filter: blur(3px) saturate(150%); -webkit-backdrop-filter: blur(3px) saturate(150%); }
.stitch-login-page::after { content: ''; position: absolute; inset: 0; background-image: linear-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px); background-size: 42px 42px; opacity: .28; pointer-events: none; }
.stitch-login-grid { position: relative; z-index: 1; width: 100%; max-width: 1280px; min-height: calc(100vh - 48px); margin: 0 auto; display: flex; flex-direction: row-reverse; gap: 28px; align-items: center; justify-content: center; }
.stitch-brand-panel, .stitch-form-panel { position: relative; overflow: hidden; border: 0; box-shadow: 0 30px 90px rgba(0, 0, 0, .28); backdrop-filter: blur(30px) saturate(175%); -webkit-backdrop-filter: blur(30px) saturate(175%); }
.stitch-brand-panel { flex: 1 1 auto; min-height: 680px; border-radius: 28px; padding: 4rem; display: none; flex-direction: column; justify-content: space-between; color: #fff; background: linear-gradient(145deg, rgba(255, 255, 255, .14), rgba(255, 255, 255, .04)); }
.stitch-form-panel { width: min(100%, 500px); border-radius: 28px; padding: 2rem; background: linear-gradient(145deg, rgba(255, 255, 255, 0.38), rgba(255, 255, 255, 0.12)); }
.stitch-brand-copy { position: relative; z-index: 1; display: grid; justify-items: end; }
.stitch-chip { display: inline-flex; align-items: center; gap: .75rem; margin-bottom: 2.25rem; padding: .625rem 1.15rem; border: 0; border-radius: 999px; background: rgba(255,255,255,.18); color: rgba(255,255,255,.9); font-size: .95rem; font-weight: 800; backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); }
.stitch-chip-dot { width: .55rem; height: .55rem; border-radius: 999px; background: #f4d3b4; box-shadow: 0 0 0 6px rgba(244, 211, 180, .22); }
.stitch-brand-copy h1 { margin: 0; color: #fff; font-size: clamp(3rem, 5vw, 4.75rem); line-height: 1.08; font-weight: 900; text-shadow: 0 18px 48px rgba(0,0,0,.38); }
.stitch-brand-copy h1 span { color: #f3d7bd; }
.stitch-brand-copy p { max-width: 36rem; margin: 1.75rem 0 0; color: rgba(255,255,255,.82); font-size: 1.05rem; line-height: 2rem; text-align: right; }
.stitch-stat-row { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.stitch-stat-row article { padding: 18px; border-radius: 18px; background: rgba(255,255,255,.16); border: 0; display: grid; gap: 6px; backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); }
.stitch-stat-row strong { color: #fff; }
.stitch-stat-row small { color: rgba(255,255,255,.72); }
.stitch-brand-rings { position: absolute; inset: auto auto -24% -12%; width: 28rem; height: 28rem; opacity: .18; color: rgba(255,255,255,.6); }
.stitch-brand-rings svg, .stitch-brand-rings circle { width: 100%; height: 100%; stroke: currentColor; }
.stitch-form-header span { color: rgba(255,255,255,.82); font-size: 13px; font-weight: 800; }
.stitch-back-home {
  display: inline-flex;
  align-items: center;
  margin-bottom: 10px;
  color: rgba(255, 255, 255, 0.78);
  font-size: 0.82rem;
  font-weight: 700;
  text-decoration: none;
}
.stitch-back-home:hover { color: #fff; }
.stitch-form-header h2 { margin: 6px 0 0; color: #fff; font-size: 32px; text-shadow: 0 10px 34px rgba(0,0,0,.26); }
.stitch-form { display: grid; gap: 16px; margin-top: 28px; }
.stitch-field-group { display: grid; gap: 8px; }
.stitch-field-group span { color: rgba(255,255,255,.86); font-weight: 800; }
.stitch-field-group input { min-height: 54px; border-radius: 16px; border: 0; background: rgba(255,255,255,.2); color: #fff; padding: 0 16px; box-shadow: inset 0 1px 0 rgba(255,255,255,.2), 0 14px 30px rgba(0,0,0,.08); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); }
.stitch-field-group input::placeholder { color: rgba(255,255,255,.66); }
.stitch-field-group input:focus { background: rgba(255,255,255,.28); outline: 2px solid rgba(255,255,255,.22); outline-offset: 2px; }
.stitch-form-meta { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.remember-switch {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  max-width: 100%;
  padding: 8px 10px 8px 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.14);
  cursor: pointer;
  user-select: none;
  transition: background 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
}
.remember-switch.is-on {
  background: rgba(243, 215, 189, 0.22);
  border-color: rgba(243, 215, 189, 0.42);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.12);
}
.remember-switch-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}
.remember-switch-track {
  position: relative;
  width: 44px;
  height: 26px;
  flex: 0 0 auto;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.22);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.18);
  transition: background 180ms ease;
}
.remember-switch.is-on .remember-switch-track {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(243, 215, 189, 0.92));
}
.remember-switch-thumb {
  position: absolute;
  top: 3px;
  right: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
  transition: transform 200ms cubic-bezier(0.22, 1, 0.36, 1), background 180ms ease;
}
.remember-switch.is-on .remember-switch-thumb {
  transform: translateX(-18px);
  background: #2d241f;
}
.remember-switch-copy {
  display: grid;
  gap: 2px;
  min-width: 0;
  text-align: right;
}
.remember-switch-copy strong {
  color: #fff;
  font-size: 0.88rem;
  font-weight: 800;
  line-height: 1.3;
}
.remember-switch-copy small {
  color: rgba(255, 255, 255, 0.72);
  font-size: 0.72rem;
  font-weight: 600;
  line-height: 1.4;
}
.link-btn { border: 0; background: transparent; color: #fff; font-weight: 900; cursor: pointer; text-shadow: 0 8px 24px rgba(0,0,0,.24); }
.stitch-submit-btn { min-height: 56px; border: 0; border-radius: 18px; background: linear-gradient(135deg, rgba(255,255,255,.96), rgba(243, 215, 189, .88)); color: #2d241f; display: inline-flex; align-items: center; justify-content: center; gap: 10px; font-weight: 900; cursor: pointer; box-shadow: 0 18px 42px rgba(0,0,0,.22); }
.stitch-submit-btn:disabled { opacity: .7; cursor: wait; }
.stitch-submit-btn svg { width: 22px; height: 22px; }
.stitch-footer-note { margin: 22px 0 0; color: rgba(255,255,255,.78); text-align: center; font-size: 0.82rem; font-weight: 600; letter-spacing: 0.01em; }
.registration-documents small { color: #70809a; font-size: 12px; }
.registration-success { margin: 0; padding: 12px 14px; border: 0; border-radius: 14px; background: rgba(32, 132, 94, .18); color: #e8fff4; font-size: 13px; font-weight: 800; line-height: 1.8; }
@media (min-width: 980px) { .stitch-brand-panel { display: flex; } }
@media (max-width: 720px) {
  .stitch-login-page { padding: 16px; background-position: center; }
  .stitch-login-grid { min-height: calc(100vh - 32px); }
  .stitch-form-panel { padding: 1.25rem; border-radius: 22px; }
  .stitch-form-meta { flex-direction: column-reverse; align-items: stretch; }
  .remember-switch { width: 100%; justify-content: flex-start; }
}

:global(#app .app-shell.is-auth-route),
:global(#app .app-shell.is-auth-route .shell-main),
:global(#app .app-shell.is-auth-route .auth-main),
:global(#app .app-shell.is-auth-route .shell-content) {
  padding: 0 !important;
  background: transparent !important;
  background-image: none !important;
}

:global(#app .app-shell.is-auth-route .shell-main::before),
:global(#app .app-shell.is-auth-route .auth-main::before),
:global(#app .app-shell.is-auth-route .shell-content::before),
:global(#app .app-shell.is-auth-route .shell-content::after) {
  content: none !important;
  display: none !important;
  background: none !important;
  background-image: none !important;
}

:global(#app .app-shell.is-auth-route .stitch-login-page) {
  min-height: 100vh !important;
  background: #101010 url('/images (1).webp') center / cover no-repeat fixed !important;
  background-image: url('/images (1).webp') !important;
}

:global(#app .app-shell.is-auth-route .stitch-login-page::before) {
  content: '' !important;
  display: block !important;
  background:
    linear-gradient(90deg, rgba(8, 10, 12, .42), rgba(8, 10, 12, .12) 48%, rgba(255, 255, 255, .06)),
    radial-gradient(circle at 74% 20%, rgba(255, 255, 255, .24), transparent 36%) !important;
  backdrop-filter: blur(4px) saturate(155%) !important;
  -webkit-backdrop-filter: blur(4px) saturate(155%) !important;
}

:global(#app .app-shell.is-auth-route .stitch-login-page::after) {
  content: '' !important;
  display: block !important;
  background-image:
    linear-gradient(rgba(255, 255, 255, .08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, .05) 1px, transparent 1px) !important;
}

:global(#app .app-shell.is-auth-route .stitch-brand-panel),
:global(#app .app-shell.is-auth-route .stitch-form-panel) {
  border: 0 !important;
  background:
    radial-gradient(circle at 18% 0%, rgba(255, 255, 255, .46), transparent 34%),
    linear-gradient(145deg, rgba(255, 255, 255, .32), rgba(255, 255, 255, .08)) !important;
  box-shadow: 0 30px 90px rgba(0, 0, 0, .32), inset 0 1px 0 rgba(255, 255, 255, .28) !important;
  backdrop-filter: blur(34px) saturate(180%) !important;
  -webkit-backdrop-filter: blur(34px) saturate(180%) !important;
}

:global(#app .app-shell.is-auth-route .stitch-form-panel) {
  background:
    radial-gradient(circle at 18% 0%, rgba(255, 255, 255, .58), transparent 36%),
    linear-gradient(145deg, rgba(255, 255, 255, .4), rgba(255, 255, 255, .12)) !important;
}

:global(#app .app-shell.is-auth-route .stitch-field-group input),
:global(#app .app-shell.is-auth-route .stitch-chip),
:global(#app .app-shell.is-auth-route .stitch-stat-row article),
:global(#app .app-shell.is-auth-route .registration-success),
:global(#app .app-shell.is-auth-route .remember-switch) {
  border: 0 !important;
  background: rgba(255, 255, 255, .18) !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .24), 0 14px 34px rgba(0, 0, 0, .08) !important;
  backdrop-filter: blur(20px) saturate(165%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(165%) !important;
}

:global(#app .app-shell.is-auth-route .remember-switch.is-on) {
  background: rgba(243, 215, 189, 0.28) !important;
}

:global(#app .app-shell.is-auth-route .stitch-form-header span),
:global(#app .app-shell.is-auth-route .stitch-form-header h2),
:global(#app .app-shell.is-auth-route .stitch-brand-copy h1),
:global(#app .app-shell.is-auth-route .stitch-brand-copy h1 span),
:global(#app .app-shell.is-auth-route .stitch-brand-copy p),
:global(#app .app-shell.is-auth-route .stitch-field-group span),
:global(#app .app-shell.is-auth-route .remember-switch-copy strong),
:global(#app .app-shell.is-auth-route .link-btn),
:global(#app .app-shell.is-auth-route .stitch-footer-note),
:global(#app .app-shell.is-auth-route .stitch-footer-note span) {
  color: #fff !important;
  text-shadow: 0 10px 30px rgba(0, 0, 0, .28) !important;
}

:global(#app .app-shell.is-auth-route .remember-switch-copy small) {
  color: rgba(255, 255, 255, 0.72) !important;
}

:global(#app .app-shell.is-auth-route .stitch-field-group input) {
  color: #fff !important;
}

:global(#app .app-shell.is-auth-route .stitch-submit-btn) {
  border: 0 !important;
  color: #2d241f !important;
  background: linear-gradient(135deg, rgba(255,255,255,.96), rgba(243,215,189,.88)) !important;
  box-shadow: 0 18px 42px rgba(0,0,0,.22) !important;
}

@media (max-width: 720px) {
  :global(#app .app-shell.is-auth-route .stitch-login-page) {
    background: #101010 url('/images (21).webp') center / cover no-repeat fixed !important;
    background-image: url('/images (21).webp') !important;
  }
}
</style>
