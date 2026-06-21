<script setup>
import { reactive } from 'vue'

import { useWorkflowHub } from '../stores/workflowHub'

const form = reactive({
  email: 'admin@karomand.local',
  password: 'AdminSecret!',
})

const { login, navigateTo, state } = useWorkflowHub()

async function handleLogin() {
  const ok = await login(form.email, form.password)
  if (ok) navigateTo('/dashboard')
}
</script>

<template>
  <section class="login-page">
    <div class="login-hero">
      <div class="hero-copy">
        <p class="page-eyebrow">Workflow Hub</p>
        <h1>ورود به پنل سازمانی</h1>
        <p>مدیریت درخواست ها، هزینه ها، کاربران و تایید اسناد در یک جریان یکپارچه.</p>
      </div>
      <div class="login-metrics">
        <article>
          <span>جریان ها</span>
          <strong>۳</strong>
        </article>
        <article>
          <span>ماژول ها</span>
          <strong>۵</strong>
        </article>
      </div>
    </div>

    <div class="login-card">
      <div class="modal-headline compact">
        <p class="page-eyebrow">ورود</p>
        <h2>حساب سازمانی</h2>
      </div>

      <label class="field-shell">
        <span>ایمیل</span>
        <input v-model="form.email" type="email" />
      </label>

      <label class="field-shell">
        <span>رمز عبور</span>
        <input v-model="form.password" type="password" />
      </label>

      <p v-if="state.lastError" class="inline-error">{{ state.lastError }}</p>

      <div class="login-actions">
        <button class="action-btn tone-primary login-submit" :disabled="state.loginPending" @click="handleLogin">
          <span class="material-symbols-outlined">login</span>
          <span>{{ state.loginPending ? 'در حال ورود...' : 'ورود' }}</span>
        </button>
      </div>
    </div>
  </section>
</template>
