<script setup>
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const {
  state,
  filteredRequests,
  openRequestDetail,
  openComposer,
  toggleSidebar,
} = useWorkflowHub()
</script>

<template>
  <section class="page-shell">
    <PageHeader
      eyebrow="درخواست‌ها"
      title="همه درخواست‌ها"
      description="لیست فشرده درخواست‌ها با جست‌وجوی سریع و ورود مستقیم به جزئیات."
      :show-search="true"
      :search-value="state.searchQuery"
      search-placeholder="جست‌وجو در عنوان، واحد، مدیر یا کد درخواست"
      action-label="درخواست جدید"
      action-icon="add"
      @update:search-value="state.searchQuery = $event"
      @action="openComposer"
      @menu="toggleSidebar"
    />

    <section class="surface-block">
      <div class="section-label-row">
        <h2>{{ filteredRequests.length }} درخواست</h2>
        <small>برای دیدن جزئیات روی هر ردیف کلیک کنید</small>
      </div>

      <div class="stack-list">
        <button
          v-for="item in filteredRequests"
          :key="item.id"
          class="list-row interactive-row"
          @click="openRequestDetail(item.id)"
        >
          <div class="list-row-main">
            <strong>{{ item.title }}</strong>
            <p>{{ item.id }} · {{ item.owner }} · {{ item.department }}</p>
          </div>
          <div class="list-row-meta">
            <span class="meta-pill">{{ item.priority }}</span>
            <span>{{ item.status }}</span>
            <small>{{ item.deadline }}</small>
          </div>
        </button>
      </div>
    </section>
  </section>
</template>
