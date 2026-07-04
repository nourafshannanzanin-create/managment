<script setup>
import { computed } from 'vue'

import PageFilters from '../components/PageFilters.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const {
  expensePeople,
  filteredExpenses,
  openExpenseDetail,
  openExpenseComposer,
  resetPageFilters,
  state,
  updatePageFilter,
} = useWorkflowHub()

const expenseFilters = computed(() => state.filters.expenses)

const expenseStats = computed(() => {
  const summary = state.expenseSummary || []
  return [
    { label: 'هزینه امروز', value: summary[0]?.value || '0' },
    { label: 'هزینه هفته', value: summary[1]?.value || '0' },
    { label: 'هزینه ماه', value: summary[2]?.value || '0' },
    { label: 'هزینه سال', value: summary[3]?.value || '0' },
  ]
})

function resetFilters() {
  resetPageFilters('expenses')
}

function toneForStatus(status) {
  const label = String(status || '')
  if (label.includes('رد')) return 'is-danger'
  if (label.includes('تایید')) return 'is-success'
  if (label.includes('بررسی') || label.includes('انتظار')) return 'is-warning'
  return ''
}
</script>

<template>
  <section v-if="state.currentUser.canAccessExpenses !== false" class="page-shell enterprise-page">
    <PageHeader
      eyebrow="مدیریت مالی"
      title="هزینه‌ها و فاکتورها"
      action-label="ثبت هزینه"
      action-icon="receipt_long"
      @action="openExpenseComposer"
    />

    <section class="metric-grid metric-grid-4">
      <article v-for="item in expenseStats" :key="item.label" class="metric-card">
        <span class="metric-label">{{ item.label }}</span>
      </article>
    </section>

    <PageFilters
      :query="expenseFilters.query"
      :person="expenseFilters.person"
      :start-date="expenseFilters.startDate"
      :end-date="expenseFilters.endDate"
      :people="expensePeople"
      @update:query="updatePageFilter('expenses', 'query', $event)"
      @update:person="updatePageFilter('expenses', 'person', $event)"
      @update:start-date="updatePageFilter('expenses', 'startDate', $event)"
      @update:end-date="updatePageFilter('expenses', 'endDate', $event)"
      @reset="resetFilters"
    />

    <section class="surface-block">
      <div class="section-label-row">
        <div>
          <h3>فهرست هزینه‌ها</h3>
          <p>{{ filteredExpenses.length }} ردیف در این نما موجود است.</p>
        </div>
      </div>

      <div class="table-shell">
        <table class="data-table">
          <thead>
            <tr>
              <th>عنوان</th>
              <th>مبلغ</th>
              <th>نوع</th>
              <th>ثبت‌کننده</th>
              <th>تاریخ</th>
              <th>وضعیت</th>
              <th>فاکتور</th>
              <th>عملیات</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredExpenses" :key="item.id">
              <td>
                <strong>{{ item.title || item.description }}</strong>
                <small>{{ item.department }}</small>
              </td>
              <td><strong>{{ item.amount }}</strong></td>
              <td>{{ item.category || '-' }}</td>
              <td>{{ item.owner }}</td>
              <td>{{ item.createdAt || '-' }}</td>
              <td><span :class="['status-badge', toneForStatus(item.status)]">{{ item.status }}</span></td>
              <td>
                <a v-if="item.invoiceUrl" class="table-link" :href="item.invoiceUrl" target="_blank" rel="noreferrer">مشاهده</a>
                <span v-else class="table-muted">بدون فایل</span>
              </td>
              <td><button class="table-link" type="button" @click="openExpenseDetail(item.id)">مشاهده جزئیات</button></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="mobile-card-list">
        <article v-for="item in filteredExpenses" :key="`${item.id}-mobile`" class="list-card">
          <div class="list-card-head">
            <div>
              <strong>{{ item.title || item.description }}</strong>
              <small>{{ item.category || 'هزینه سازمانی' }}</small>
            </div>
            <span :class="['status-badge', toneForStatus(item.status)]">{{ item.status }}</span>
          </div>

          <div class="list-card-grid">
            <div><span>مبلغ</span><strong>{{ item.amount }}</strong></div>
            <div><span>ثبت‌کننده</span><strong>{{ item.owner }}</strong></div>
            <div><span>بخش</span><strong>{{ item.department }}</strong></div>
            <div><span>تاریخ</span><strong>{{ item.createdAt || '-' }}</strong></div>
          </div>

          <div class="list-card-actions">
            <button class="action-btn tone-soft" type="button" @click="openExpenseDetail(item.id)">
              <span class="material-symbols-outlined">visibility</span>
              <span>جزئیات</span>
            </button>
            <a v-if="item.invoiceUrl" class="action-btn tone-soft" :href="item.invoiceUrl" target="_blank" rel="noreferrer">
              <span class="material-symbols-outlined">description</span>
              <span>فاکتور</span>
            </a>
          </div>
        </article>
      </div>
    </section>
  </section>

  <section v-else class="page-shell">
    <article class="access-denied-card">
      <h2>دسترسی به ماژول هزینه‌ها فعال نیست</h2>
      <p>این بخش فقط برای نقش‌هایی که مجوز مالی دارند نمایش داده می‌شود.</p>
    </article>
  </section>
</template>
