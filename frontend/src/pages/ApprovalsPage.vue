<script setup>
import IconlyIcon from '../components/base/IconlyIcon.vue'
import { computed } from 'vue'

import SectionHeading from '../components/SectionHeading.vue'
import WorkflowStatusFilter from '../components/WorkflowStatusFilter.vue'
import { useWorkflowHub } from '../stores/workflowHub'
import { joinDisplayParts } from '../utils/text'
import { rowToneForStatus, toneForStatus, workflowStatusBucket } from '../utils/status'

const {
  downloadProtectedFile,
  filteredApprovals,
  openApprovalDetail,
  openSignatureComposer,
  state,
  updatePageFilter,
} = useWorkflowHub()

const activeStatus = computed(() => String(state.filters.approvals.status || ''))

const approvalStats = computed(() => {
  const rows = state.approvals
  return [
    { key: '', label: 'کل اسناد', value: rows.length, icon: 'folder_copy', tone: 'is-total' },
    { key: 'pending', label: 'در حال بررسی', value: rows.filter((item) => workflowStatusBucket(item, 'approval') === 'pending').length, icon: 'pending_actions', tone: 'is-pending' },
    { key: 'approved', label: 'تایید شده', value: rows.filter((item) => workflowStatusBucket(item, 'approval') === 'approved').length, icon: 'verified', tone: 'is-approved' },
    { key: 'rejected', label: 'رد شده', value: rows.filter((item) => workflowStatusBucket(item, 'approval') === 'rejected').length, icon: 'cancel', tone: 'is-rejected' },
  ]
})

function setStatusFilter(value) {
  updatePageFilter('approvals', 'status', value)
}

async function handleDownload(item) {
  await downloadProtectedFile(item?.downloadUrl, item?.id || 'approval-document')
}
</script>

<template>
  <section class="page-shell enterprise-page">
    <section class="metric-grid metric-grid-4">
      <button
        v-for="item in approvalStats"
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
          title="فهرست تاییدیه‌ها"
          :description="`${filteredApprovals.length} مورد با فیلترهای انتخاب‌شده`"
        />
        <button v-if="state.currentUser.canApproveDocuments" class="action-btn tone-soft" type="button" @click="openSignatureComposer">
          <IconlyIcon name="approval" decorative />
          <span>بارگذاری مهر</span>
        </button>
      </div>

      <WorkflowStatusFilter page="approvals" />

      <div class="table-shell">
        <table class="data-table">
          <thead>
            <tr>
              <th>عنوان</th>
              <th>نوع</th>
              <th>ثبت‌کننده</th>
              <th>بخش</th>
              <th>وضعیت</th>
              <th>دانلود</th>
              <th>عملیات</th>
            </tr>
          </thead>
          <tbody v-if="filteredApprovals.length">
            <tr
              v-for="item in filteredApprovals"
              :key="item.id"
              :class="['table-click-row', rowToneForStatus(item.status)]"
              tabindex="0"
              @click="openApprovalDetail(item.id)"
              @keydown.enter.prevent="openApprovalDetail(item.id)"
              @keydown.space.prevent="openApprovalDetail(item.id)"
            >
              <td class="cell-mobile-primary">
                <strong>{{ item.title }}</strong>
                <small>{{ joinDisplayParts([item.type, item.department]) }}</small>
              </td>
              <td class="cell-mobile-hide">{{ item.type || '-' }}</td>
              <td class="cell-mobile-hide">{{ item.owner }}</td>
              <td class="cell-mobile-hide">{{ item.department }}</td>
              <td data-label="وضعیت"><span :class="['status-badge', toneForStatus(item.status)]">{{ item.status }}</span></td>
              <td class="cell-mobile-hide">
                <button v-if="item.downloadUrl" class="table-link" type="button" @click.stop="handleDownload(item)">دانلود</button>
                <span v-else class="table-muted">بدون فایل</span>
              </td>
              <td class="cell-mobile-hide"><button class="table-link" type="button" @click.stop="openApprovalDetail(item.id)">مشاهده</button></td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr>
              <td colspan="7" class="table-empty">موردی با این فیلترها پیدا نشد.</td>
            </tr>
          </tbody>
        </table>
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
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.approval-metric-card.is-filterable {
  width: 100%;
  text-align: right;
  cursor: pointer;
  font: inherit;
}

.approval-metric-card.is-filterable.is-selected {
  outline: 2px solid rgba(52, 144, 139, 0.45);
  outline-offset: 1px;
}

.approval-metric-card:hover {
  transform: translateY(-3px);
  box-shadow: none;
}

.approval-metric-card::after {
  content: '';
  position: absolute;
  inset-inline: 20px;
  bottom: 0;
  height: 5px;
  border-radius: 999px 999px 0 0;
  background: rgba(36, 59, 107, 0.14);
}

.approval-metric-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.approval-metric-copy {
  display: grid;
  gap: 10px;
}

.approval-metric-label {
  font-size: 12px;
  letter-spacing: 0.02em;
}

.approval-metric-value {
  margin: 0;
  font-size: clamp(34px, 2.4vw, 44px);
  line-height: 1;
  font-weight: 800;
  color: #1f2f52;
}

.approval-metric-icon {
  flex: 0 0 auto;
  display: inline-grid;
  place-items: center;
  width: 54px;
  height: 54px;
  border-radius: 18px;
  background: rgba(36, 59, 107, 0.08);
  color: var(--primary);
  box-shadow: none;
  font-size: 24px;
}

.approval-metric-card.is-pending::after { background: #d9a441; }
.approval-metric-card.is-pending { border-color: rgba(217, 164, 65, 0.14); }
.approval-metric-card.is-pending .approval-metric-icon { background: var(--surface, #fff); color: #b57900; }

.approval-metric-card.is-approved::after { background: #22956d; }
.approval-metric-card.is-approved { border-color: rgba(34, 149, 109, 0.14); }
.approval-metric-card.is-approved .approval-metric-icon { background: var(--surface, #fff); color: #1b7a59; }

.approval-metric-card.is-rejected::after { background: #cd5c5c; }
.approval-metric-card.is-rejected { border-color: rgba(205, 92, 92, 0.14); }
.approval-metric-card.is-rejected .approval-metric-icon { background: var(--surface, #fff); color: #b44646; }

.approval-metric-card.is-total::after { background: #4867b7; }
.approval-metric-card.is-total { border-color: rgba(72, 103, 183, 0.14); }
.approval-metric-card.is-total .approval-metric-icon { background: var(--surface, #fff); color: #39549a; }
</style>
