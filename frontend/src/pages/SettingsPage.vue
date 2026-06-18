<script setup>
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const { state, toggleSidebar } = useWorkflowHub()
</script>

<template>
  <section class="page-shell">
    <PageHeader
      eyebrow="تنظیمات"
      title="تنظیمات سازمان"
      description="آیتم‌های اصلی به‌صورت سبک، خوانا و یکپارچه با بقیه تجربه."
      @menu="toggleSidebar"
    />

    <section class="surface-block">
      <div class="section-label-row">
        <h2>ماژول‌های تنظیمات</h2>
        <small>{{ state.settingsCards.length }} بخش</small>
      </div>

      <div class="stack-list">
        <article v-for="item in state.settingsCards" :key="item.title" class="list-row">
          <div class="list-row-main">
            <strong>{{ item.title }}</strong>
            <p>{{ item.description }}</p>
          </div>
        </article>
      </div>
    </section>
  </section>
</template>
