<script setup>
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const { state, toggleSidebar } = useWorkflowHub()
</script>

<template>
  <section class="page-shell">
    <PageHeader
      eyebrow="کاربران"
      title="نمای فشرده کاربران"
      description="تمرکز روی نقش، واحد و شاخص عملکرد، بدون boxهای تزئینی اضافه."
      @menu="toggleSidebar"
    />

    <section class="surface-block">
      <div class="section-label-row">
        <h2>فهرست کاربران</h2>
        <small>{{ state.users.length }} نفر</small>
      </div>

      <div class="stack-list">
        <article v-for="item in state.users" :key="item.name" class="list-row">
          <div class="list-row-main user-inline">
            <div class="avatar-pill subtle">{{ item.name.slice(0, 1) }}</div>
            <div>
              <strong>{{ item.name }}</strong>
              <p>{{ item.role }} · {{ item.department }}</p>
            </div>
          </div>
          <div class="list-row-meta">
            <small>{{ item.kpi }}</small>
          </div>
        </article>
      </div>
    </section>
  </section>
</template>
