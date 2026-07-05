<script setup>
import { computed } from 'vue'

import { useWorkflowHub } from '../stores/workflowHub'

const {
  approvalHistory,
  approvalInbox,
  openApprovalDetail,
  openSignatureComposer,
  state,
} = useWorkflowHub()

const approvalStats = computed(() => [
  {
    label: 'در انتظار بررسی',
    value: approvalInbox.value.length,
    icon: 'pending_actions',
    note: 'نیازمند اقدام',
    tone: 'is-pending',
  },
  {
    label: 'تایید شده',
    value: approvalHistory.value.filter((item) => String(item.status || '').includes('تایید')).length,
    icon: 'verified',
    note: 'گردش کامل شده',
    tone: 'is-approved',
  },
  {
    label: 'رد شده',
    value: approvalHistory.value.filter((item) => String(item.status || '').includes('رد')).length,
    icon: 'cancel',
    note: 'نیازمند بازبینی',
    tone: 'is-rejected',
  },
  {
    label: 'کل اسناد',
    value: state.approvals.length,
    icon: 'folder_copy',
    note: 'نمای کلی پرونده‌ها',
    tone: 'is-total',
  },
])

function toneForStatus(status) {
  const label = String(status || '')
  if (label.includes('رد')) return 'is-danger'
  if (label.includes('تایید')) return 'is-success'
  if (label.includes('بررسی') || label.includes('انتظار')) return 'is-warning'
  return ''
}

function bucketTone(item) {
  if (String(item.status || '').includes('رد')) return 'approval-state-rejected'
  if (String(item.status || '').includes('تایید')) return 'approval-state-approved'
  return 'approval-state-pending'
}
</script>

<template>
  <section v-if="state.currentUser.canAccessApprovals || state.currentUser.canApproveDocuments" class="page-shell enterprise-page">
    <section class="metric-grid metric-grid-4">
      <article v-for="item in approvalStats" :key="item.label" :class="['metric-card', 'approval-metric-card', item.tone]">
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
          <h3>صف بررسی</h3>
          <p>اسنادی که هنوز در جریان تایید هستند و نیاز به اقدام دارند.</p>
        </div>
      </div>

      <div class="approval-board">
        <article v-for="item in approvalInbox" :key="item.id" :class="['approval-card', 'approval-card-strong', bucketTone(item)]">
          <div class="approval-card-head">
            <div>
              <strong>{{ item.title }}</strong>
              <small>{{ item.type }} - {{ item.department }}</small>
            </div>
            <span :class="['status-badge', toneForStatus(item.status)]">{{ item.status }}</span>
          </div>

          <div class="list-card-actions">
            <a v-if="item.downloadUrl" class="action-btn tone-soft" :href="item.downloadUrl" target="_blank" rel="noreferrer">
              <span class="material-symbols-outlined">download</span>
              <span>دانلود فایل</span>
            </a>
            <button class="action-btn tone-primary" type="button" @click="openApprovalDetail(item.id)">
              <span class="material-symbols-outlined">visibility</span>
              <span>جزئیات و اقدام</span>
            </button>
          </div>
        </article>
      </div>
    </section>

    <section class="surface-block">
      <div class="section-label-row">
        <div>
          <h3>تاریخچه تاییدها</h3>
          <p>نسخه‌های بررسی‌شده با تفکیک واضح بین تایید و رد.</p>
        </div>
      </div>

      <div class="table-shell">
        <table class="data-table">
          <thead>
            <tr>
              <th>عنوان</th>
              <th>ثبت‌کننده</th>
              <th>بخش</th>
              <th>ارجاع‌گیرندگان</th>
              <th>وضعیت</th>
              <th>دانلود</th>
              <th>عملیات</th>
            </tr>
          </thead>
          <tbody v-if="approvalHistory.length">
            <tr v-for="item in approvalHistory" :key="item.id">
              <td><strong>{{ item.title }}</strong></td>
              <td>{{ item.owner }}</td>
              <td>{{ item.department }}</td>
              <td>{{ (item.assignees || []).join('، ') || '-' }}</td>
              <td><span :class="['status-badge', toneForStatus(item.status)]">{{ item.status }}</span></td>
              <td>
                <a v-if="item.downloadUrl" class="table-link" :href="item.downloadUrl" target="_blank" rel="noreferrer">دانلود</a>
                <span v-else class="table-muted">بدون فایل</span>
              </td>
              <td><button class="table-link" type="button" @click="openApprovalDetail(item.id)">مشاهده</button></td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr>
              <td colspan="7" class="table-empty">هنوز هیچ تاییدیه نهایی‌شده‌ای ثبت نشده است.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>

  <section v-else class="page-shell">
    <article class="access-denied-card">
      <h2>دسترسی به ماژول تاییدیه‌ها فعال نیست</h2>
      <p>برای مشاهده این بخش باید دسترسی تاییدیه‌ها برای حساب شما فعال شده باشد.</p>
    </article>
  </section>
</template>

<style scoped>
.approval-metric-card {
  position: relative;
  display: grid;
  gap: 14px;
  overflow: hidden;
  border: 1px solid rgba(36, 59, 107, 0.08);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 248, 252, 0.94)),
    var(--surface);
  box-shadow: 0 18px 40px rgba(36, 59, 107, 0.08);
}

.approval-metric-card::after {
  content: '';
  position: absolute;
  inset-inline: 18px;
  bottom: 0;
  height: 4px;
  border-radius: 999px 999px 0 0;
  background: rgba(36, 59, 107, 0.14);
}

.approval-metric-icon {
  display: inline-grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 14px;
  background: rgba(36, 59, 107, 0.08);
  color: var(--primary);
  font-size: 20px;
}

.approval-metric-note {
  color: var(--muted);
  font-size: 13px;
}

.approval-metric-card.is-pending::after {
  background: #d9a441;
}

.approval-metric-card.is-pending .approval-metric-icon {
  background: rgba(217, 164, 65, 0.14);
  color: #b57900;
}

.approval-metric-card.is-approved::after {
  background: #22956d;
}

.approval-metric-card.is-approved .approval-metric-icon {
  background: rgba(34, 149, 109, 0.12);
  color: #1b7a59;
}

.approval-metric-card.is-rejected::after {
  background: #cd5c5c;
}

.approval-metric-card.is-rejected .approval-metric-icon {
  background: rgba(205, 92, 92, 0.12);
  color: #b44646;
}

.approval-metric-card.is-total::after {
  background: #4867b7;
}

.approval-metric-card.is-total .approval-metric-icon {
  background: rgba(72, 103, 183, 0.12);
  color: #39549a;
}
</style>
