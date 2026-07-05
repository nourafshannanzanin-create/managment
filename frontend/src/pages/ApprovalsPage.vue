<script setup>
import { computed } from 'vue'

import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const {
  approvalHistory,
  approvalInbox,
  openApprovalDetail,
  openDocumentComposer,
  openSignatureComposer,
  state,
} = useWorkflowHub()

const approvalStats = computed(() => [
  { label: 'در انتظار بررسی', value: approvalInbox.value.length },
  { label: 'تایید شده', value: approvalHistory.value.filter((item) => String(item.status || '').includes('تایید')).length },
  { label: 'رد شده', value: approvalHistory.value.filter((item) => String(item.status || '').includes('رد')).length },
  { label: 'کل اسناد', value: state.approvals.length },
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
    <PageHeader
      eyebrow="تاییدها"
      title="تاییدیه‌ها و گردش امضا"
      description="وضعیت هر ارجاع با تفکیک بصری قوی‌تر نمایش داده می‌شود و دانلود فایل نهایی از همان مسیر در دسترس است."
      action-label="ثبت سند"
      action-icon="upload_file"
      @action="openDocumentComposer"
    />

    <section class="metric-grid metric-grid-4">
      <article v-for="item in approvalStats" :key="item.label" class="metric-card">
        <span class="metric-label">{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </article>
    </section>

    <section class="surface-block">
      <div class="banner-card surface-inline">
        <div class="banner-copy">
          <strong>امضای دیجیتال و ارجاع سند</strong>
          <p>ثبت سند جدید، انتخاب ارجاع‌گیرنده و دریافت نسخه نهایی امضاشده از یک جریان یکپارچه.</p>
        </div>

        <div class="list-card-actions">
          <button v-if="state.currentUser.canApproveDocuments" class="action-btn tone-soft" type="button" @click="openSignatureComposer">
            <span class="material-symbols-outlined">draw</span>
            <span>ثبت امضا</span>
          </button>
          <button class="action-btn tone-primary" type="button" @click="openDocumentComposer">
            <span class="material-symbols-outlined">upload_file</span>
            <span>سند جدید</span>
          </button>
        </div>
      </div>
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

          <div class="approval-card-grid">
            <div><span>ثبت‌کننده</span><strong>{{ item.owner }}</strong></div>
            <div><span>تاریخ</span><strong>{{ item.uploadedAt || '-' }}</strong></div>
            <div><span>سطح ریسک</span><strong>{{ item.risk }}</strong></div>
            <div><span>ارجاع به</span><strong>{{ (item.assignees || []).join('، ') || '-' }}</strong></div>
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
