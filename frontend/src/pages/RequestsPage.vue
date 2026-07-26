<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import { computed } from 'vue'

import SectionHeading from '../components/SectionHeading.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const { filteredRequests, openRequestDetail } = useWorkflowHub()

const requestStats = computed(() => [
  { label: 'کل درخواست‌ها', value: filteredRequests.value.length, icon: 'assignment', note: 'در این نما', tone: 'is-total' },
  { label: 'در حال بررسی', value: filteredRequests.value.filter((item) => String(item.status || '').includes('بررسی')).length, icon: 'pending_actions', note: 'نیازمند اقدام', tone: 'is-pending' },
  { label: 'تایید شده', value: filteredRequests.value.filter((item) => String(item.status || '').includes('تایید')).length, icon: 'verified', note: 'گردش کامل شده', tone: 'is-approved' },
  { label: 'فوری و بحرانی', value: filteredRequests.value.filter((item) => ['high', 'critical'].includes(item.priority)).length, icon: 'warning', note: 'اولویت بالا', tone: 'is-rejected' },
])

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
    <section class="metric-grid metric-grid-4">
      <article v-for="item in requestStats" :key="item.label" :class="['metric-card', 'approval-metric-card', item.tone]">
        <div class="metric-card-headline">
          <span class="metric-label">{{ item.label }}</span>
          <IconlyIcon :name="item.icon" class="approval-metric-icon" decorative />
        </div>
        <strong>{{ item.value }}</strong>
        <small class="approval-metric-note">{{ item.note }}</small>
      </article>
    </section>

    <section class="surface-block">
      <div class="section-label-row">
        <SectionHeading
          title="فهرست درخواست‌ها"
          :description="`${filteredRequests.length} ردیف مطابق فیلترهای هدر پیدا شد.`"
        />
      </div>

      <div class="table-shell">
        <table class="data-table">
          <thead>
            <tr>
              <th>شماره</th>
              <th>عنوان</th>
              <th>ثبت‌کننده</th>
              <th>مدیر مسئول</th>
              <th>کارمندان ارجاعی</th>
              <th>وضعیت</th>
              <th>اولویت</th>
              <th>تاریخ</th>
              <th>عملیات</th>
            </tr>
          </thead>
          <tbody v-if="filteredRequests.length">
            <tr
              v-for="item in filteredRequests"
              :key="item.id"
              class="table-click-row"
              tabindex="0"
              @click="openRequestDetail(item.id)"
              @keydown.enter.prevent="openRequestDetail(item.id)"
              @keydown.space.prevent="openRequestDetail(item.id)"
            >
              <td><strong>{{ item.id }}</strong></td>
              <td>
                <strong>{{ item.title }}</strong>
                <small>{{ item.department }}</small>
              </td>
              <td>{{ item.owner }}</td>
              <td>{{ item.manager }}</td>
              <td>{{ (item.employeeAssignees || []).join('، ') || '-' }}</td>
              <td><span :class="['status-badge', toneForStatus(item.status)]">{{ item.status }}</span></td>
              <td>{{ priorityLabel(item.priority) }}</td>
              <td>{{ item.createdAt || item.deadline || '-' }}</td>
              <td><button class="table-link" type="button" @click.stop="openRequestDetail(item.id)">مشاهده جزئیات</button></td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr>
              <td colspan="9" class="table-empty">در این بازه موردی برای نمایش وجود ندارد.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>
</template>
