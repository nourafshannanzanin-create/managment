<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import { computed } from 'vue'

import InfiniteScrollSentinel from '../components/InfiniteScrollSentinel.vue'
import SectionHeading from '../components/SectionHeading.vue'
import { useInfiniteList } from '../composables/useInfiniteList'
import { useWorkflowHub } from '../stores/workflowHub'
import { rowToneForStatus, toneForStatus, workflowStatusBucket } from '../utils/status'

const {
  filteredRequests,
  openRequestDetail,
  state,
  updatePageFilter,
  loadMoreBootstrapCollection,
} = useWorkflowHub()

const activeStatus = computed(() => String(state.filters.requests.status || ''))
const requestsPaging = computed(() => state.collectionPaging?.requests || { total: 0, hasMore: false, loading: false })

const {
  items: visibleRequests,
  hasMore: hasMoreRequests,
  loadingMore: loadingMoreRequests,
  loadMore: loadMoreRequests,
} = useInfiniteList(filteredRequests, {
  resetKey: computed(() => JSON.stringify(state.filters.requests || {})),
  hasMoreRemote: computed(() => Boolean(requestsPaging.value.hasMore)),
  onLoadMore: () => loadMoreBootstrapCollection('requests'),
})

const requestStats = computed(() => {
  const rows = state.requests
  const total = Number(requestsPaging.value.total || rows.length)
  return [
    { key: '', label: 'کل درخواست‌ها', value: total, icon: 'assignment', tone: 'is-total' },
    { key: 'pending', label: 'در حال بررسی', value: rows.filter((item) => workflowStatusBucket(item, 'request') === 'pending').length, icon: 'pending_actions', tone: 'is-pending' },
    { key: 'approved', label: 'تایید شده', value: rows.filter((item) => workflowStatusBucket(item, 'request') === 'approved').length, icon: 'verified', tone: 'is-approved' },
    { key: 'rejected', label: 'رد شده', value: rows.filter((item) => workflowStatusBucket(item, 'request') === 'rejected').length, icon: 'cancel', tone: 'is-rejected' },
  ]
})

function setStatusFilter(value) {
  updatePageFilter('requests', 'status', value)
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
      <button
        v-for="item in requestStats"
        :key="item.label"
        type="button"
        :class="['metric-card', 'approval-metric-card', 'is-filterable', item.tone, activeStatus === item.key && 'is-selected']"
        @click="setStatusFilter(item.key)"
      >
        <div class="approval-metric-top">
          <div class="approval-metric-copy">
            <span class="metric-label approval-metric-label">{{ item.label }}</span>
            <strong class="approval-metric-value">{{ item.value }}</strong>
          </div>
          <IconlyIcon :name="item.icon" class="approval-metric-icon" decorative />
        </div>
      </button>
    </section>

    <section class="surface-block">
      <div class="section-label-row">
        <SectionHeading
          title="فهرست درخواست‌ها"
          :description="`${visibleRequests.length} از ${requestsPaging.total || filteredRequests.length} مورد`"
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
          <tbody v-if="visibleRequests.length">
            <tr
              v-for="item in visibleRequests"
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
                <small>{{ item.owner || '—' }} · {{ item.department || 'بدون بخش' }}</small>
              </td>
              <td class="cell-mobile-hide">{{ item.owner }}</td>
              <td class="cell-mobile-hide">{{ item.manager }}</td>
              <td class="cell-mobile-hide">{{ (item.employeeAssignees || []).join('، ') || '-' }}</td>
              <td data-label="وضعیت"><span :class="['status-badge', toneForStatus(item.status)]">{{ item.status }}</span></td>
              <td class="cell-mobile-hide">{{ priorityLabel(item.priority) }}</td>
              <td data-label="تاریخ">{{ item.createdAt || item.deadline || '-' }}</td>
              <td class="cell-mobile-hide">
                <button class="table-link" type="button" @click.stop="openRequestDetail(item.id)">مشاهده جزئیات</button>
              </td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr>
              <td colspan="9" class="table-empty">در این بازه موردی برای نمایش وجود ندارد.</td>
            </tr>
          </tbody>
        </table>
        <InfiniteScrollSentinel
          :disabled="!hasMoreRequests || loadingMoreRequests"
          @reach-end="loadMoreRequests"
        >
          <small v-if="loadingMoreRequests" class="list-loading-more">در حال بارگذاری...</small>
          <small v-else-if="hasMoreRequests" class="list-loading-more">برای ادامه اسکرول کنید</small>
        </InfiniteScrollSentinel>
      </div>
    </section>
  </section>
</template>

<style scoped>
.approval-metric-card {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 18px;
  overflow: hidden;
  min-height: 108px;
  padding: 20px 20px 18px;
  border: 1px solid rgba(36, 59, 107, 0.08);
  border-radius: 12px;
  background: var(--surface, #fff);
  box-shadow: none;
}

.metric-card.is-filterable,
.approval-metric-card.is-filterable {
  width: 100%;
  text-align: right;
  cursor: pointer;
  font: inherit;
}

.metric-card.is-filterable.is-selected,
.approval-metric-card.is-selected {
  border-color: rgba(52, 144, 139, 0.35);
  box-shadow: inset 0 0 0 1px rgba(52, 144, 139, 0.18);
}

.list-loading-more {
  color: #6b8581;
  font-size: 0.78rem;
  font-weight: 650;
}
</style>
