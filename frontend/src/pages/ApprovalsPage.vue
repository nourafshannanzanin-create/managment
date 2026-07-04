<script setup>
import { computed } from 'vue'

import PageFilters from '../components/PageFilters.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const {
  approvalHistory,
  approvalInbox,
  approvalPeople,
  openApprovalDetail,
  openDocumentComposer,
  openSignatureComposer,
  resetPageFilters,
  state,
  updatePageFilter,
} = useWorkflowHub()

const approvalFilters = computed(() => state.filters.approvals)

function resetFilters() {
  resetPageFilters('approvals')
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
  <section v-if="state.currentUser.canAccessApprovals || state.currentUser.canApproveDocuments" class="page-shell enterprise-page">
    <PageHeader
      eyebrow="مرکز تایید اسناد"
      title="تاییدیه‌ها و گردش امضا"
    />

    <section class="quick-action-grid">
      <button class="quick-action-card" type="button" @click="openDocumentComposer">
        <span class="material-symbols-outlined">upload_file</span>
        <strong>ارسال سند</strong>
        <small>ثبت سند جدید برای گردش تایید</small>
      </button>
      <button v-if="state.currentUser.canApproveDocuments" class="quick-action-card is-dark" type="button" @click="openSignatureComposer">
        <span class="material-symbols-outlined">draw</span>
        <strong>ثبت امضا</strong>
        <small>مدیریت امضای دیجیتال مدیر تاییدکننده</small>
      </button>
    </section>

    <PageFilters
      :query="approvalFilters.query"
      :person="approvalFilters.person"
      :start-date="approvalFilters.startDate"
      :end-date="approvalFilters.endDate"
      :people="approvalPeople"
      @update:query="updatePageFilter('approvals', 'query', $event)"
      @update:person="updatePageFilter('approvals', 'person', $event)"
      @update:start-date="updatePageFilter('approvals', 'startDate', $event)"
      @update:end-date="updatePageFilter('approvals', 'endDate', $event)"
      @reset="resetFilters"
    />

    <section class="surface-block">
      <div class="section-label-row">
        <div>
          <h3>در انتظار بررسی</h3>
          <p>اسنادی که هنوز در جریان تایید هستند، در این بخش نمایش داده می‌شوند.</p>
        </div>
      </div>

      <div class="table-shell">
        <table class="data-table">
          <thead>
            <tr>
              <th>عنوان</th>
              <th>ثبت‌کننده</th>
              <th>بخش</th>
              <th>نوع</th>
              <th>وضعیت</th>
              <th>تاریخ</th>
              <th>عملیات</th>
            </tr>
          </thead>
          <tbody v-if="approvalInbox.length">
            <tr v-for="item in approvalInbox" :key="item.id">
              <td><strong>{{ item.title }}</strong></td>
              <td>{{ item.owner }}</td>
              <td>{{ item.department }}</td>
              <td>{{ item.type }}</td>
              <td><span :class="['status-badge', toneForStatus(item.status)]">{{ item.status }}</span></td>
              <td>{{ item.uploadedAt || '-' }}</td>
              <td><button class="table-link" type="button" @click="openApprovalDetail(item.id)">مشاهده</button></td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr>
              <td colspan="7" class="table-empty">در حال حاضر موردی در انتظار بررسی وجود ندارد.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="surface-block">
      <div class="section-label-row">
        <div>
          <h3>تاریخچه تاییدیه‌ها</h3>
          <p>موارد بررسی‌شده و نهایی‌شده در این بخش نمایش داده می‌شوند.</p>
        </div>
      </div>

      <div class="table-shell">
        <table class="data-table">
          <thead>
            <tr>
              <th>عنوان</th>
              <th>ثبت‌کننده</th>
              <th>بخش</th>
              <th>نوع</th>
              <th>وضعیت</th>
              <th>تاریخ</th>
              <th>عملیات</th>
            </tr>
          </thead>
          <tbody v-if="approvalHistory.length">
            <tr v-for="item in approvalHistory" :key="item.id">
              <td><strong>{{ item.title }}</strong></td>
              <td>{{ item.owner }}</td>
              <td>{{ item.department }}</td>
              <td>{{ item.type }}</td>
              <td><span :class="['status-badge', toneForStatus(item.status)]">{{ item.status }}</span></td>
              <td>{{ item.uploadedAt || '-' }}</td>
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
