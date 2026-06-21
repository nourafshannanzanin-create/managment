<script setup>
import PageFilters from '../components/PageFilters.vue'
import PageHeader from '../components/PageHeader.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const {
  approvalHistory,
  approvalInbox,
  approvalPeople,
  canApproveDocuments,
  openApprovalDetail,
  openDocumentComposer,
  openSignatureComposer,
  resetPageFilters,
  signatureState,
  state,
  toggleSidebar,
  updatePageFilter,
} = useWorkflowHub()
</script>

<template>
  <section v-if="state.currentUser.canApproveDocuments" class="page-shell">
    <PageHeader
      eyebrow="تاییدها"
      title="گردش تایید اسناد"
      description="هر مدیر فقط سندهای ارجاع شده به خودش را بررسی می کند و امضا به صورت دیجیتال روی سند ذخیره می شود."
      :action-label="state.currentUser.accessRole === 'admin' ? 'ثبت سند' : ''"
      action-icon="note_add"
      @action="openDocumentComposer"
      @menu="toggleSidebar"
    />

    <PageFilters
      :query="state.filters.approvals.query"
      :person="state.filters.approvals.person"
      :start-date="state.filters.approvals.startDate"
      :end-date="state.filters.approvals.endDate"
      :people="approvalPeople"
      @update:query="updatePageFilter('approvals', 'query', $event)"
      @update:person="updatePageFilter('approvals', 'person', $event)"
      @update:start-date="updatePageFilter('approvals', 'startDate', $event)"
      @update:end-date="updatePageFilter('approvals', 'endDate', $event)"
      @reset="resetPageFilters('approvals')"
    />

    <section class="surface-block">
      <div class="signature-banner">
        <div>
          <strong>امضای دیجیتال</strong>
          <p>{{ signatureState.hasSignature ? 'امضای شما ذخیره شده است.' : 'برای تایید اسناد ابتدا امضای خود را ثبت کنید.' }}</p>
        </div>
        <button class="action-btn tone-primary" @click="openSignatureComposer">
          <span class="material-symbols-outlined">draw</span>
          <span>{{ signatureState.hasSignature ? 'ویرایش امضا' : 'ثبت امضا' }}</span>
        </button>
      </div>
    </section>

    <div class="dashboard-grid">
      <section class="surface-block">
        <div class="section-label-row">
          <h2>در انتظار اقدام</h2>
          <small>{{ approvalInbox.length }}</small>
        </div>
        <div class="table-shell">
          <table class="data-table">
            <thead>
              <tr>
                <th>کد</th>
                <th>عنوان</th>
                <th>ثبت کننده</th>
                <th>نوع</th>
                <th>تاریخ</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in approvalInbox" :key="item.id" class="clickable-row" @click="openApprovalDetail(item.id)">
                <td>{{ item.id }}</td>
                <td>
                  <strong>{{ item.title }}</strong>
                  <small>{{ item.summary }}</small>
                </td>
                <td>{{ item.owner }}</td>
                <td>{{ item.type }}</td>
                <td>{{ item.uploadedAt }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="surface-block">
        <div class="section-label-row">
          <h2>تاریخچه</h2>
          <small>{{ approvalHistory.length }}</small>
        </div>
        <div class="table-shell">
          <table class="data-table">
            <thead>
              <tr>
                <th>کد</th>
                <th>عنوان</th>
                <th>وضعیت</th>
                <th>ریسک</th>
                <th>تاریخ</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in approvalHistory" :key="item.id" class="clickable-row" @click="openApprovalDetail(item.id)">
                <td>{{ item.id }}</td>
                <td>{{ item.title }}</td>
                <td><span class="meta-pill">{{ item.status }}</span></td>
                <td>{{ item.risk }}</td>
                <td>{{ item.uploadedAt }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </section>
  <section v-else class="page-shell">
    <PageHeader eyebrow="تاییدها" title="دسترسی محدود" description="این بخش فقط برای مدیرها فعال است." @menu="toggleSidebar" />
  </section>
</template>
