<script setup>
import { reactive } from 'vue'

import { useWorkflowHub } from '../stores/workflowHub'

const form = reactive({
  email: 'admin@karomand.local',
  password: 'AdminSecret!',
  remember: false,
})

const { login, navigateTo, state } = useWorkflowHub()

async function handleLogin() {
  const ok = await login(form.email, form.password)
  if (ok) navigateTo('/dashboard')
}
</script>

<template>
  <section class="stitch-login-page">
    <div class="stitch-login-grid">
      <section class="stitch-brand-panel" aria-hidden="true">
        <div class="stitch-brand-copy">
          <div class="stitch-chip">
            <span class="stitch-chip-dot"></span>
            <span>Workflow Hub</span>
          </div>

          <h1>
            ورود به
            <br />
            <span>پنل سازمانی</span>
          </h1>

          <p>
            مدیریت هوشمند درخواست‌ها، پایش هزینه‌ها و تایید اسناد در یک پلتفرم پیشرفته و امن.
          </p>
        </div>

        <div class="stitch-brand-bottom">
          <div class="stitch-support-card">
            <div class="stitch-support-icon">
              <svg fill="none" viewBox="0 0 24 24">
                <path
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  stroke="currentColor"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                />
              </svg>
            </div>
            <span>پشتیبانی سیستم</span>
            <svg class="stitch-support-arrow" fill="none" viewBox="0 0 24 24">
              <path
                d="M15 19l-7-7 7-7"
                stroke="currentColor"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
              />
            </svg>
          </div>
        </div>

        <div class="stitch-brand-rings" aria-hidden="true">
          <svg fill="none" viewBox="0 0 400 400">
            <circle cx="200" cy="200" r="199.5" />
            <circle cx="200" cy="200" r="149.5" />
            <circle cx="200" cy="200" r="99.5" />
          </svg>
        </div>
      </section>

      <section class="stitch-form-panel">
        <div class="stitch-form-header">
          <span>System Access</span>
          <h2>حساب سازمانی</h2>
        </div>

        <form class="stitch-form" @submit.prevent="handleLogin">
          <label class="stitch-field-group" for="login-email">
            <span>ایمیل</span>
            <input
              id="login-email"
              v-model="form.email"
              autocomplete="username"
              dir="ltr"
              placeholder="email@example.com"
              type="email"
            />
          </label>

          <label class="stitch-field-group" for="login-password">
            <span>رمز عبور</span>
            <input
              id="login-password"
              v-model="form.password"
              autocomplete="current-password"
              dir="ltr"
              placeholder="••••••••"
              type="password"
            />
          </label>

          <p v-if="state.lastError" class="stitch-error">{{ state.lastError }}</p>

          <div class="stitch-form-meta">
            <a href="#" @click.prevent>فراموشی رمز عبور؟</a>

            <label class="stitch-checkbox-row">
              <span>مرا به خاطر بسپار</span>
              <input v-model="form.remember" type="checkbox" />
            </label>
          </div>

          <button class="stitch-submit-btn" :disabled="state.loginPending" type="submit">
            <span>{{ state.loginPending ? 'در حال ورود...' : 'ورود به سیستم' }}</span>
            <svg fill="none" viewBox="0 0 24 24">
              <path
                d="M17 8l4 4m0 0l-4 4m4-4H3"
                stroke="currentColor"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2.5"
              />
            </svg>
          </button>
        </form>

        <p class="stitch-footer-note">
          © 2024 کلیه حقوق متعلق به <span>کارنومند</span> می‌باشد
        </p>
      </section>
    </div>
  </section>
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
  position: relative;
  min-height: 100vh;
  padding: 24px;
  overflow: hidden;
  font-family: 'Vazirmatn', sans-serif;
  background-color: #f8fafc;
  background-image:
    radial-gradient(at 0% 0%, hsla(180, 47%, 85%, 0.4) 0px, transparent 50%),
    radial-gradient(at 100% 0%, hsla(210, 40%, 90%, 0.4) 0px, transparent 50%),
    radial-gradient(at 100% 100%, hsla(180, 47%, 85%, 0.4) 0px, transparent 50%),
    radial-gradient(at 0% 100%, hsla(210, 40%, 90%, 0.4) 0px, transparent 50%);
}

.stitch-login-page::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(15, 23, 42, 0.03) 1px, transparent 1px);
  background-size: 30px 30px;
}

.stitch-login-page::after {
  content: '';
  position: absolute;
  inset: auto 8% -18% auto;
  width: 38rem;
  height: 38rem;
  border-radius: 999px;
  filter: blur(80px);
  opacity: 0.18;
  background: #d6f5f0;
}

.stitch-login-grid {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1440px;
  min-height: calc(100vh - 48px);
  margin: 0 auto;
  display: flex;
  flex-direction: row-reverse;
  gap: 42px;
  align-items: center;
  justify-content: center;
}

.stitch-brand-panel,
.stitch-form-panel {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.7);
  box-shadow:
    0 20px 25px -5px rgba(0, 0, 0, 0.05),
    0 10px 10px -5px rgba(0, 0, 0, 0.02);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.stitch-brand-panel {
  flex: 1 1 auto;
  min-height: 750px;
  border-radius: 2.5rem;
  padding: 4.5rem 4.75rem;
  display: none;
  flex-direction: column;
  justify-content: space-between;
  border-right: 4px solid rgba(45, 122, 120, 0.2);
}

.stitch-brand-copy {
  position: relative;
  z-index: 1;
  display: grid;
  justify-items: end;
}

.stitch-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 2.25rem;
  padding: 0.625rem 1.15rem;
  border: 1px solid rgba(45, 122, 120, 0.1);
  border-radius: 999px;
  background: rgba(45, 122, 120, 0.05);
  color: #0f766e;
  font-size: 0.95rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.stitch-chip-dot {
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 999px;
  background: #14b8a6;
  box-shadow: 0 0 0 6px rgba(20, 184, 166, 0.12);
}

.stitch-brand-copy h1 {
  margin: 0;
  color: #0f172a;
  font-size: clamp(3rem, 5vw, 4.75rem);
  line-height: 1.08;
  font-weight: 900;
}

.stitch-brand-copy h1 span {
  color: #0f766e;
}

.stitch-brand-copy p {
  max-width: 36rem;
  margin: 1.75rem 0 0;
  color: rgba(15, 23, 42, 0.72);
  font-size: 1.15rem;
  line-height: 2.1rem;
  text-align: right;
}

.stitch-brand-bottom {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 1.5rem;
}

.stitch-support-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.1rem 1.35rem;
  border-radius: 1.35rem;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(15, 118, 110, 0.08);
  color: #0f172a;
  font-weight: 700;
}

.stitch-support-icon,
.stitch-support-arrow {
  width: 1.35rem;
  height: 1.35rem;
  color: #0f766e;
}

.stitch-support-arrow {
  margin-right: auto;
}

.stitch-brand-rings {
  position: absolute;
  inset: auto auto -24% -12%;
  width: 28rem;
  height: 28rem;
  opacity: 0.22;
  color: rgba(15, 118, 110, 0.45);
}

.stitch-brand-rings svg {
  width: 100%;
  height: 100%;
}

.stitch-brand-rings circle {
  stroke: currentColor;
}

.stitch-form-panel {
  width: min(100%, 33rem);
  border-radius: 2rem;
  padding: 2.25rem;
}

.stitch-form-header {
  display: grid;
  gap: 0.4rem;
  margin-bottom: 1.75rem;
  text-align: right;
}

.stitch-form-header span {
  color: #0f766e;
  font-size: 0.88rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.stitch-form-header h2 {
  margin: 0;
  color: #0f172a;
  font-size: 2rem;
  font-weight: 800;
}

.stitch-form {
  display: grid;
  gap: 1rem;
}

.stitch-field-group {
  display: grid;
  gap: 0.55rem;
  text-align: right;
}

.stitch-field-group span {
  color: rgba(15, 23, 42, 0.68);
  font-size: 0.94rem;
  font-weight: 700;
}

.stitch-field-group input {
  width: 100%;
  min-height: 3.6rem;
  padding: 0 1rem;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.76);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.45);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.stitch-field-group input:focus {
  border-color: rgba(15, 118, 110, 0.5);
  box-shadow: 0 0 0 4px rgba(20, 184, 166, 0.12);
}

.stitch-error {
  margin: 0;
  color: #b91c1c;
  font-size: 0.92rem;
  text-align: right;
}

.stitch-form-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  font-size: 0.9rem;
}

.stitch-form-meta a {
  color: #0f766e;
  font-weight: 700;
}

.stitch-checkbox-row {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  color: rgba(15, 23, 42, 0.7);
}

.stitch-checkbox-row input {
  accent-color: #0f766e;
}

.stitch-submit-btn {
  min-height: 3.85rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.85rem;
  border-radius: 1.1rem;
  background: linear-gradient(135deg, #0f766e, #14b8a6);
  color: #fff;
  font-size: 1rem;
  font-weight: 800;
  box-shadow: 0 16px 30px rgba(15, 118, 110, 0.22);
}

.stitch-submit-btn svg {
  width: 1.3rem;
  height: 1.3rem;
}

.stitch-submit-btn:disabled {
  opacity: 0.7;
}

.stitch-footer-note {
  margin: 1.6rem 0 0;
  color: rgba(15, 23, 42, 0.56);
  text-align: center;
  line-height: 1.9;
}

.stitch-footer-note span {
  color: #0f766e;
  font-weight: 800;
}

@media (min-width: 1100px) {
  .stitch-brand-panel {
    display: flex;
  }
}

@media (max-width: 1099px) {
  .stitch-login-grid {
    min-height: auto;
  }
}

@media (max-width: 767px) {
  .stitch-login-page {
    padding: 16px;
  }

  .stitch-form-panel {
    padding: 1.35rem;
    border-radius: 1.5rem;
  }

  .stitch-form-header h2 {
    font-size: 1.65rem;
  }

  .stitch-form-meta {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
