<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function enterHub() {
  router.push('/dashboard')
}
</script>

<template>
  <section class="login-page">
    <div class="login-hero">
      <p class="page-eyebrow">کارومند</p>
      <h1>ورود به کارومند</h1>
    </div>

    <div class="login-card">
      <div class="modal-headline compact">
        <p class="page-eyebrow">ورود</p>
        <h2>حساب سازمانی</h2>
      </div>

      <label class="field-shell">
        <span>ایمیل</span>
        <input type="email" placeholder="" />
      </label>

      <label class="field-shell">
        <span>رمز عبور</span>
        <input type="password" placeholder="" />
      </label>

      <div class="login-actions">
        <button class="action-btn tone-primary" @click="enterHub">
          <span class="material-symbols-outlined">login</span>
          <span>ورود</span>
        </button>
        <button class="action-btn tone-soft" @click="router.push('/requests/new')">
          <span class="material-symbols-outlined">edit_square</span>
          <span>درخواست جدید</span>
        </button>
      </div>
    </div>
  </section>
</template>
