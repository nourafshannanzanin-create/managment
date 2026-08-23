<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import { computed } from 'vue'

import SectionHeading from '../components/SectionHeading.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { rowToneForStatus, toneForStatus, workflowStatusBucket } from '../utils/status'

const { filteredRequests, openRequestDetail, state } = useWorkflowHub()

const requestStats = computed(() => {
  const rows = state.requests
  return [
    { label: 'کل درخواست‌ها', value: rows.length, icon: 'assignment', tone: 'is-total' },
    { label: 'در حال بررسی', value: rows.filter((item) => workflowStatusBucket(item, 'request') === 'pending').length, icon: 'pending_actions', tone: 'is-pending' },
    { label: 'تایید شده', value: rows.filter((item) => workflowStatusBucket(item, 'request') === 'approved').length, icon: 'verified', tone: 'is-approved' },
    { label: 'رد شده', value: rows.filter((item) => workflowStatusBucket(item, 'request') === 'rejected').length, icon: 'cancel', tone: 'is-rejected' },
  ]
})

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
      </article>
    </section>

    <section class="surface-block">
      <div class="section-label-row">
        <SectionHeading
          title="فهرست درخواست‌ها"
          :description="`${filteredRequests.length} مورد با فیلترهای انتخاب‌شده`"
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
              :class="['table-click-row', rowToneForStatus(item.status)]"
              tabindex="0"
              @click="openRequestDetail(item.id)"
              @keydown.enter.prevent="openRequestDetail(item.id)"
              @keydown.space.prevent="openRequestDetail(item.id)"
            >
              <td class="cell-mobile-hide"><strong>{{ item.id }}</strong></td>
              <td class="cell-mobile-primary">
                <strong>{{ item.title }}</strong>
                <small>{{ item.department }}</small>
              </td>
              <td class="cell-mobile-hide">{{ item.owner }}</td>
              <td class="cell-mobile-hide">{{ item.manager }}</td>
              <td class="cell-mobile-hide">{{ (item.employeeAssignees || []).join('، ') || '-' }}</td>
              <td data-label="وضعیت"><span :class="['status-badge', toneForStatus(item.status)]">{{ item.status }}</span></td>
              <td class="cell-mobile-hide">{{ priorityLabel(item.priority) }}</td>
              <td data-label="تاریخ">{{ item.createdAt || item.deadline || '-' }}</td>
              <td class="cell-mobile-hide"><button class="table-link" type="button" @click.stop="openRequestDetail(item.id)">مشاهده جزئیات</button></td>
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
