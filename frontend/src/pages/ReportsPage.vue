<script setup>
import PageFilters from '../components/PageFilters.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const { filteredReports, reportPeople, resetPageFilters, state, toggleSidebar, updatePageFilter } = useWorkflowHub()
</script>

<template>
  <section class="page-shell">
    <PageHeader eyebrow="گزارشات" title="گزارشات" @menu="toggleSidebar" />

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

    <div class="reports-grid">
      <article v-for="item in filteredReports" :key="item.title" class="report-card">
        <div class="section-label-row">
          <h3>{{ item.title }}</h3>
          <span class="meta-pill">{{ item.export }}</span>
        </div>
        <div class="report-actions">
          <span class="filter-chip">{{ item.owner }}</span>
          <span class="filter-chip">{{ item.generatedAt }}</span>
        </div>
      </article>
    </div>

    <section class="surface-block report-hero">
      <div class="section-label-row">
        <h2>خروجی‌ها</h2>
      </div>
    </section>
  </section>
</template>
