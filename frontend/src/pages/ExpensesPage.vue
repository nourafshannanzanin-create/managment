<script setup>
import PageFilters from '../components/PageFilters.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const { state, expensePeople, filteredExpenses, resetPageFilters, toggleSidebar, updatePageFilter } = useWorkflowHub()
</script>

<template>
  <section class="page-shell expenses-page">
    <PageHeader eyebrow="هزینه‌ها" title="مدیریت هزینه‌ها" @menu="toggleSidebar" />

    <PageFilters
      :query="state.filters.expenses.query"
      :person="state.filters.expenses.person"
      :start-date="state.filters.expenses.startDate"
      :end-date="state.filters.expenses.endDate"
      :people="expensePeople"
      @update:query="updatePageFilter('expenses', 'query', $event)"
      @update:person="updatePageFilter('expenses', 'person', $event)"
      @update:start-date="updatePageFilter('expenses', 'startDate', $event)"
      @update:end-date="updatePageFilter('expenses', 'endDate', $event)"
      @reset="resetPageFilters('expenses')"
    />

    <div class="content-grid expense-chart-grid">
      <section class="surface-block expense-chart-block">
        <div class="section-label-row">
          <h2>هزینه‌ها</h2>
        </div>
        <div class="mini-chart">
          <div v-for="bar in state.chartData" :key="bar.day" class="mini-chart-column">
            <span :style="{ height: `${bar.value}%` }"></span>
            <small>{{ bar.day }}</small>
          </div>
        </div>
      </section>
    </div>

    <section class="surface-block">
      <div class="section-label-row">
        <h2>فهرست</h2>
        <small>{{ filteredExpenses.length }}</small>
      </div>

      <div class="stack-list">
        <article v-for="item in filteredExpenses" :key="item.id" class="list-row expense-row">
          <div class="list-row-main">
            <strong>{{ item.title }}</strong>
            <p>{{ item.category }} · {{ item.owner }} · {{ item.id }}</p>
            <div class="progress-shell">
              <span :style="{ width: `${item.progress}%` }"></span>
            </div>
          </div>
          <div class="list-row-meta">
            <span class="meta-pill strong">{{ item.amount }}</span>
            <span>{{ item.status }}</span>
          </div>
        </article>
      </div>
    </section>

    <section class="spotlight-card expense-summary-card">
      <div class="section-label-row">
        <h3>جمع</h3>
      </div>
      <div class="spotlight-metrics">
        <article v-for="item in state.expenseSummary" :key="item.label">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </article>
      </div>
    </section>
  </section>
</template>
