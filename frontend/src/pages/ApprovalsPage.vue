<script setup>
import { computed } from 'vue'

import PageFilters from '../components/PageFilters.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const {
  approvalPeople,
  state,
  filteredApprovals,
  openApprovalDetail,
  resetPageFilters,
  toggleSidebar,
  updatePageFilter,
} = useWorkflowHub()

const approvalColumns = computed(() => ({
  pending: filteredApprovals.value.filter((item) => item.status.includes('انتظار') || item.status.includes('بررسی')),
  approved: filteredApprovals.value.filter((item) => item.status.includes('تأیید') || item.status.includes('تایید')),
  flagged: filteredApprovals.value.filter((item) => item.risk === 'بالا' || item.status.includes('رد')),
}))
</script>

<template>
  <section class="page-shell">
    <PageHeader eyebrow="تأییدیه‌ها" title="تأیید اسناد" @menu="toggleSidebar" />

    <PageFilters
      :query="state.filters.approvals.query"
      :person="state.filters.approvals.person"
      :start-date="state.filters.approvals.startDate"
      :end-date="state.filters.approvals.endDate"
      :people="approvalPeople"
      @update:query="updatePageFilter('approvals', 'query', $event)"
      @update:person="updatePageFilter('approvals', 'person', $event)"
      @update:start-date="updatePageFilter('approvals', 'startDate', $event)"
      @update:end-date="updatePageFilter('approvals', 'endDate', $event)"
      @reset="resetPageFilters('approvals')"
    />

    <section class="surface-block signature-block">
      <div class="section-label-row">
        <h2>امضا</h2>
      </div>

      <div class="signature-grid">
        <article class="signature-card">
          <div class="signature-head">
            <strong>سارا احمدی</strong>
            <span class="meta-pill">فعال</span>
          </div>
          <div class="signature-actions">
            <button class="action-btn tone-primary">
              <span class="material-symbols-outlined">draw</span>
              <span>ثبت امضا</span>
            </button>
          </div>
        </article>

        <article class="signature-card">
          <div class="signature-head">
            <strong>حمید رضایی</strong>
            <span class="meta-pill">در انتظار</span>
          </div>
          <div class="signature-actions">
            <button class="action-btn tone-soft">
              <span class="material-symbols-outlined">shield_lock</span>
              <span>ارسال</span>
            </button>
          </div>
        </article>
      </div>
    </section>

    <section class="approval-columns">
      <div class="kanban-column">
        <div class="section-label-row">
          <h3>آماده اقدام</h3>
          <span class="kanban-tag">{{ approvalColumns.pending.length }}</span>
        </div>
        <article v-for="item in approvalColumns.pending" :key="item.id" class="kanban-card" @click="openApprovalDetail(item.id)">
          <strong>{{ item.title }}</strong>
          <p>{{ item.type }} · {{ item.department }}</p>
        </article>
      </div>

      <div class="kanban-column">
        <div class="section-label-row">
          <h3>تأییدشده</h3>
          <span class="kanban-tag">{{ approvalColumns.approved.length }}</span>
        </div>
        <article v-for="item in approvalColumns.approved" :key="item.id" class="kanban-card" @click="openApprovalDetail(item.id)">
          <strong>{{ item.title }}</strong>
          <p>{{ item.owner }} · {{ item.uploadedAt }}</p>
        </article>
      </div>

      <div class="kanban-column">
        <div class="section-label-row">
          <h3>حساس</h3>
          <span class="kanban-tag">{{ approvalColumns.flagged.length }}</span>
        </div>
        <article v-for="item in approvalColumns.flagged" :key="item.id" class="kanban-card" @click="openApprovalDetail(item.id)">
          <strong>{{ item.title }}</strong>
          <p>{{ item.risk }} · {{ item.status }}</p>
        </article>
      </div>
    </section>

    <section class="surface-block">
      <div class="section-label-row">
        <h2>اسناد</h2>
        <small>{{ filteredApprovals.length }}</small>
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
            <p>{{ item.id }} · {{ item.type }} · {{ item.department }} · {{ item.owner }}</p>
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
