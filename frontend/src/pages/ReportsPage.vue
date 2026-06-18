<script setup>
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const { state, toggleSidebar } = useWorkflowHub()
</script>

<template>
  <section class="page-shell">
    <PageHeader
      eyebrow="گزارشات"
      title="خروجی‌های مدیریتی"
      description="ساختار تمیز برای گزارش‌های کلیدی، بدون cardهای شلوغ و تکراری."
      @menu="toggleSidebar"
    />

    <section class="surface-block">
      <div class="section-label-row">
        <h2>لیست گزارش‌ها</h2>
        <small>{{ state.reports.length }} خروجی آماده</small>
      </div>

      <div class="stack-list">
        <article v-for="item in state.reports" :key="item.title" class="list-row">
          <div class="list-row-main">
            <strong>{{ item.title }}</strong>
            <p>{{ item.description }}</p>
          </div>
          <div class="list-row-meta">
            <span class="meta-pill">{{ item.export }}</span>
          </div>
        </article>
      </div>
    </section>
  </section>
</template>
