<script setup>
import { onMounted } from 'vue'

import PageFilters from '../components/PageFilters.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const { filteredReports, loadReports, reportPeople, resetPageFilters, state, toggleSidebar, updatePageFilter } = useWorkflowHub()

onMounted(() => {
  loadReports(true)
})
</script>

<template>
  <section v-if="state.currentUser.canViewReports" class="page-shell">
    <PageHeader eyebrow="گزارشات" title="گزارشات مدیریتی" description="این بخش فقط برای مدیرعامل فعال است." @menu="toggleSidebar" />

    <PageFilters
      :query="state.filters.reports.query"
      :person="state.filters.reports.person"
      :start-date="state.filters.reports.startDate"
      :end-date="state.filters.reports.endDate"
      :people="reportPeople"
      @update:query="updatePageFilter('reports', 'query', $event)"
      @update:person="updatePageFilter('reports', 'person', $event)"
      @update:start-date="updatePageFilter('reports', 'startDate', $event)"
      @update:end-date="updatePageFilter('reports', 'endDate', $event)"
      @reset="resetPageFilters('reports')"
    />

    <div class="metric-grid">
      <article class="metric-card">
        <span>کاربران</span>
        <strong>{{ state.reportSummary?.users || 0 }}</strong>
      </article>
      <article class="metric-card">
        <span>درخواست ها</span>
        <strong>{{ state.reportSummary?.requests || 0 }}</strong>
      </article>
      <article class="metric-card">
        <span>هزینه ها</span>
        <strong>{{ state.reportSummary?.expenses || 0 }}</strong>
      </article>
      <article class="metric-card">
        <span>جمع هزینه</span>
        <strong>{{ state.reportSummary?.expenseTotal || '0' }}</strong>
      </article>
    </div>

    <div class="dashboard-grid">
      <section class="surface-block">
        <div class="section-label-row">
          <h2>کارت های گزارش</h2>
        </div>
        <div class="reports-grid compact-reports">
          <article v-for="item in filteredReports" :key="item.title" class="report-card">
            <div class="section-label-row">
              <h3>{{ item.title }}</h3>
              <span class="meta-pill">{{ item.export }}</span>
            </div>
            <p>{{ item.description }}</p>
            <small>{{ item.generatedAt }}</small>
          </article>
        </div>
      </section>

      <section class="surface-block">
        <div class="section-label-row">
          <h2>بیشترین ثبت کننده هزینه</h2>
        </div>
        <div class="stack-list">
          <article v-for="item in state.topSubmitters" :key="item.name" class="list-row">
            <div class="list-row-main">
              <strong>{{ item.name }}</strong>
            </div>
            <div class="list-row-meta">
              <span class="meta-pill strong">{{ item.count }}</span>
            </div>
          </article>
        </div>
      </section>
    </div>
  </section>
  <section v-else class="page-shell">
    <PageHeader eyebrow="گزارشات" title="دسترسی محدود" description="این بخش فقط برای مدیرعامل فعال است." @menu="toggleSidebar" />
  </section>
</template>
