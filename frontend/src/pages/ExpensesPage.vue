<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import { computed } from 'vue'

import SectionHeading from '../components/SectionHeading.vue'
import WorkflowStatusFilter from '../components/WorkflowStatusFilter.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { rowToneForStatus, toneForStatus, workflowStatusBucket } from '../utils/status'

const { filteredExpenses, openExpenseDetail, openProtectedFile, state, updatePageFilter } = useWorkflowHub()

const activeStatus = computed(() => String(state.filters.expenses.status || ''))

const expenseStats = computed(() => {
  const rows = state.expenses
  return [
    { key: '', label: 'کل هزینه‌ها', value: rows.length, icon: 'receipt_long', tone: 'is-total' },
    { key: 'pending', label: 'در حال بررسی', value: rows.filter((item) => workflowStatusBucket(item, 'expense') === 'pending').length, icon: 'pending_actions', tone: 'is-pending' },
    { key: 'approved', label: 'تایید شده', value: rows.filter((item) => workflowStatusBucket(item, 'expense') === 'approved').length, icon: 'verified', tone: 'is-approved' },
    { key: 'rejected', label: 'رد شده', value: rows.filter((item) => workflowStatusBucket(item, 'expense') === 'rejected').length, icon: 'cancel', tone: 'is-rejected' },
  ]
})

function setStatusFilter(value) {
  updatePageFilter('expenses', 'status', value)
}

async function handleInvoiceOpen(item) {
  await openProtectedFile(item?.invoiceUrl, item?.id || 'expense-invoice')
}
</script>

<template>
  <section v-if="state.currentUser.canAccessExpenses !== false" class="page-shell enterprise-page">
    <section class="metric-grid metric-grid-4">
      <button
        v-for="item in expenseStats"
        :key="item.label"
        type="button"
        :class="['metric-card', 'approval-metric-card', 'is-filterable', item.tone, activeStatus === item.key && 'is-selected']"
        @click="setStatusFilter(item.key)"
      >
        <div class="metric-card-headline">
          <span class="metric-label">{{ item.label }}</span>
          <IconlyIcon :name="item.icon" class="approval-metric-icon" decorative />
        </div>
        <strong>{{ item.value }}</strong>
      </button>
    </section>

    <section class="surface-block">
      <div class="section-label-row">
        <SectionHeading
          title="فهرست هزینه‌ها"
          :description="`${filteredExpenses.length} مورد با فیلترهای انتخاب‌شده`"
        />
      </div>

      <WorkflowStatusFilter page="expenses" />

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
            <tr
              v-for="item in filteredExpenses"
              :key="item.id"
              :class="['table-click-row', rowToneForStatus(item.status)]"
              tabindex="0"
              @click="openExpenseDetail(item.id)"
              @keydown.enter.prevent="openExpenseDetail(item.id)"
              @keydown.space.prevent="openExpenseDetail(item.id)"
            >
              <td class="cell-mobile-primary">
                <strong>{{ item.title || item.description }}</strong>
                <small>{{ item.department }}</small>
              </td>
              <td data-label="مبلغ"><strong>{{ item.amount }}</strong></td>
              <td class="cell-mobile-hide">{{ item.category || '-' }}</td>
              <td class="cell-mobile-hide">{{ item.owner }}</td>
              <td data-label="تاریخ">{{ item.createdAt || '-' }}</td>
              <td data-label="وضعیت"><span :class="['status-badge', toneForStatus(item.status)]">{{ item.status }}</span></td>
              <td class="cell-mobile-hide">
                <button v-if="item.invoiceUrl" class="table-link" type="button" @click.stop="handleInvoiceOpen(item)">مشاهده</button>
                <span v-else class="table-muted">بدون فایل</span>
              </td>
              <td class="cell-mobile-hide"><button class="table-link" type="button" @click.stop="openExpenseDetail(item.id)">جزئیات</button></td>
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

<style scoped>
.metric-card.is-filterable {
  width: 100%;
  text-align: right;
  cursor: pointer;
  font: inherit;
}

.metric-card.is-filterable.is-selected {
  outline: 2px solid rgba(52, 144, 139, 0.45);
  outline-offset: 1px;
}
</style>
