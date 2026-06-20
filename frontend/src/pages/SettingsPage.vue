<script setup>
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const { state, toggleSidebar } = useWorkflowHub()
</script>

<template>
  <section class="page-shell">
    <PageHeader eyebrow="تنظیمات" title="تنظیمات سیستم" description="" @menu="toggleSidebar" />

    <div class="settings-grid">
      <section class="surface-block">
        <div class="section-label-row">
          <h2>هویت سازمان</h2>
        </div>
        <label class="field-shell">
          <span>نام سازمان</span>
          <input type="text" value="کارومند" />
        </label>
      </section>

      <section class="surface-block">
        <div class="section-label-row">
          <h2>امنیت</h2>
        </div>
        <div class="toggle-row">
          <div>
            <strong>احراز هویت دومرحله‌ای</strong>
            <p></p>
          </div>
          <div class="toggle-pill"><span></span></div>
        </div>
        <div class="toggle-row">
          <div>
            <strong>تاریخچه نشست‌ها</strong>
            <p></p>
          </div>
          <span class="material-symbols-outlined">chevron_left</span>
        </div>
      </section>

      <section class="surface-block">
        <div class="section-label-row">
          <h2>بخش‌ها</h2>
        </div>
        <div class="stack-list">
          <article v-for="item in state.settingsCards" :key="item.title" class="list-row">
            <div class="list-row-main">
              <strong>{{ item.title }}</strong>
            </div>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>
