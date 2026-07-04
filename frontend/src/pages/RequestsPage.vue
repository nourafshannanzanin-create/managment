<script setup>
import { computed } from 'vue'

import PageFilters from '../components/PageFilters.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const {
  filteredRequests,
  openRequestComposer,
  openRequestDetail,
  requestPeople,
  resetPageFilters,
  state,
  updatePageFilter,
} = useWorkflowHub()

const requestFilters = computed(() => state.filters.requests)

const requestStats = computed(() => [
  { label: 'کل درخواست‌های فیلترشده', value: filteredRequests.value.length },
  { label: 'در حال بررسی', value: filteredRequests.value.filter((item) => String(item.status || '').includes('بررسی')).length },
  { label: 'تایید شده', value: filteredRequests.value.filter((item) => String(item.status || '').includes('تایید')).length },
  { label: 'فوری و بحرانی', value: filteredRequests.value.filter((item) => ['high', 'critical'].includes(item.priority)).length },
])

function resetFilters() {
  resetPageFilters('requests')
}

function toneForStatus(status) {
  const label = String(status || '')
  if (label.includes('رد')) return 'is-danger'
  if (label.includes('تایید')) return 'is-success'
  if (label.includes('بررسی') || label.includes('انتظار')) return 'is-warning'
  return ''
}

function priorityLabel(priority) {
  return {
    low: 'پایین',
    medium: 'متوسط',
    high: 'بالا',
    critical: 'بحرانی',
  }[priority] || priority || '-'
}
</script>

<template>
  <section class="page-shell enterprise-page">
    <PageHeader
      eyebrow="مدیریت فرآیند"
      title="درخواست‌های سازمانی"
      action-label="درخواست جدید"
      action-icon="add_circle"
      @action="openRequestComposer"
    />

    <PageFilters
      :query="requestFilters.query"
      :person="requestFilters.person"
      :start-date="requestFilters.startDate"
      :end-date="requestFilters.endDate"
      :people="requestPeople"
      @update:query="updatePageFilter('requests', 'query', $event)"
      @update:person="updatePageFilter('requests', 'person', $event)"
      @update:start-date="updatePageFilter('requests', 'startDate', $event)"
      @update:end-date="updatePageFilter('requests', 'endDate', $event)"
      @reset="resetFilters"
    />

    <section class="surface-block">
      <div class="section-label-row">
        <div>
          <h3>فهرست درخواست‌ها</h3>
          <p>{{ filteredRequests.length }} ردیف در این نما نمایش داده شده است.</p>
        </div>
      </div>

      <div class="table-shell">
        <table class="data-table">
          <thead>
            <tr>
              <th>شماره</th>
              <th>عنوان</th>
              <th>ثبت‌کننده</th>
              <th>مدیر مسئول</th>
              <th>وضعیت</th>
              <th>اولویت</th>
              <th>تاریخ</th>
              <th>عملیات</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredRequests" :key="item.id">
              <td><strong>{{ item.id }}</strong></td>
              <td>
                <strong>{{ item.title }}</strong>
                <small>{{ item.department }}</small>
              </td>
              <td>{{ item.owner }}</td>
              <td>{{ item.manager }}</td>
              <td>
                <span :class="['status-badge', toneForStatus(item.status)]">{{ item.status }}</span>
              </td>
              <td>{{ priorityLabel(item.priority) }}</td>
              <td>{{ item.createdAt || item.deadline || '-' }}</td>
              <td>
                <button class="table-link" type="button" @click="openRequestDetail(item.id)">مشاهده جزئیات</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="mobile-card-list">
        <article v-for="item in filteredRequests" :key="`${item.id}-mobile`" class="list-card">
          <div class="list-card-head">
            <div>
              <strong>{{ item.title }}</strong>
              <small>{{ item.id }}</small>
            </div>
            <span :class="['status-badge', toneForStatus(item.status)]">{{ item.status }}</span>
          </div>

          <div class="list-card-grid">
            <div><span>ثبت‌کننده</span><strong>{{ item.owner }}</strong></div>
            <div><span>مدیر</span><strong>{{ item.manager }}</strong></div>
            <div><span>اولویت</span><strong>{{ priorityLabel(item.priority) }}</strong></div>
            <div><span>تاریخ</span><strong>{{ item.createdAt || item.deadline || '-' }}</strong></div>
          </div>

          <button class="action-btn tone-soft" type="button" @click="openRequestDetail(item.id)">
            <span class="material-symbols-outlined">visibility</span>
            <span>مشاهده جزئیات</span>
          </button>
        </article>
      </div>
    </section>
  </section>
</template>
