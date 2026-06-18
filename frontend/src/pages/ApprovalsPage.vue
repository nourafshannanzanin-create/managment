<script setup>
import CompactStatRow from '../components/CompactStatRow.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const {
  state,
  filteredApprovals,
  approvalMetricCards,
  openApprovalDetail,
  toggleSidebar,
} = useWorkflowHub()
</script>

<template>
  <section class="page-shell">
    <PageHeader
      eyebrow="تأییدیه‌ها"
      title="صف تأیید اسناد"
      description="ردیف‌های فشرده و تمرکز بر تصمیم‌گیری سریع، بدون پنل‌های اضافی."
      :show-search="true"
      :search-value="state.searchQuery"
      search-placeholder="جست‌وجو در عنوان، نوع، مالک یا کد سند"
      @update:search-value="state.searchQuery = $event"
      @menu="toggleSidebar"
    />

    <CompactStatRow :items="approvalMetricCards" />

    <section class="surface-block">
      <div class="section-label-row">
        <h2>اسناد جاری</h2>
        <small>{{ filteredApprovals.length }} سند</small>
      </div>

      <div class="stack-list">
        <button
          v-for="item in filteredApprovals"
          :key="item.id"
          class="list-row interactive-row"
          @click="openApprovalDetail(item.id)"
        >
          <div class="list-row-main">
            <strong>{{ item.title }}</strong>
            <p>{{ item.id }} · {{ item.type }} · {{ item.department }}</p>
          </div>
          <div class="list-row-meta">
            <span class="meta-pill">{{ item.status }}</span>
            <span>{{ item.risk }}</span>
            <small>{{ item.uploadedAt }}</small>
          </div>
        </button>
      </div>
    </section>
  </section>
</template>
