<script setup>
import { computed } from 'vue'

import { useWorkflowHub } from '../stores/workflowHub'

const { filteredExpenses, openExpenseDetail, state } = useWorkflowHub()

const expenseStats = computed(() => {
  const summary = state.expenseSummary || []
  return [
    { label: 'هزینه امروز', value: summary[0]?.value || '0', icon: 'today', note: 'ثبت روز جاری', tone: 'is-pending' },
    { label: 'هزینه هفته', value: summary[1]?.value || '0', icon: 'date_range', note: 'هفتگی', tone: 'is-approved' },
    { label: 'هزینه ماه', value: summary[2]?.value || '0', icon: 'calendar_month', note: 'جمع ماهانه', tone: 'is-total' },
    { label: 'هزینه سال', value: summary[3]?.value || '0', icon: 'payments', note: 'جمع سالانه', tone: 'is-rejected' },
  ]
})

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
    <section class="metric-grid metric-grid-4">
      <article v-for="item in expenseStats" :key="item.label" :class="['metric-card', 'approval-metric-card', item.tone]">
        <div class="metric-card-headline">
          <span class="metric-label">{{ item.label }}</span>
          <span class="material-symbols-outlined approval-metric-icon">{{ item.icon }}</span>
        </div>
        <strong>{{ item.value }}</strong>
        <small class="approval-metric-note">{{ item.note }}</small>
      </article>
    </section>

    <section class="surface-block">
      <div class="section-label-row">
        <div>
          <h3>فهرست هزینه‌ها</h3>
          <p>{{ filteredExpenses.length }} ردیف مطابق فیلترهای هدر موجود است.</p>
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
          <tbody v-if="filteredExpenses.length">
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
              <td><button class="table-link" type="button" @click="openExpenseDetail(item.id)">جزئیات</button></td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr>
              <td colspan="8" class="table-empty">برای این فیلترها موردی پیدا نشد.</td>
            </tr>
          </tbody>
        </table>
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
