<script setup>
import { computed, onMounted, reactive } from 'vue'

import { useWorkflowHub } from '../stores/workflowHub'

const { state, createHqOrganization, loadHqPanel, selectHqOrganization } = useWorkflowHub()

const organizationForm = reactive({
  organizationName: '',
  organizationCode: '',
  managerName: '',
  managerUsername: '',
  managerEmail: '',
  managerPhone: '',
  managerPassword: '',
})

const summaryCards = computed(() => [
  { label: 'مجموعه', value: state.hq.summary.organizations || 0, icon: 'domain' },
  { label: 'کاربر', value: state.hq.summary.users || 0, icon: 'groups' },
  { label: 'فعال', value: state.hq.summary.activeUsers || 0, icon: 'verified_user' },
  { label: 'پرداخت', value: state.hq.summary.paymentTotal || '0', icon: 'payments' },
  { label: 'در انتظار', value: state.hq.summary.pendingPaymentTotal || '0', icon: 'pending_actions' },
  { label: 'درخواست باز', value: state.hq.summary.openRequests || 0, icon: 'assignment_late' },
  { label: 'سند باز', value: state.hq.summary.pendingDocuments || 0, icon: 'edit_document' },
  { label: 'تیکت', value: state.hq.summary.tickets || 0, icon: 'support_agent' },
])

const reportRows = computed(() => state.hq.organizations || [])

function paymentTicketRank(ticket) {
  return ticket?.category === 'financial' && ticket?.priority === 'urgent' && ticket?.subject === 'پرداخت کیف پول' ? 0 : 1
}

const ticketRows = computed(() => [...(state.hq.tickets || [])].sort((a, b) => {
  const rankDiff = paymentTicketRank(a) - paymentTicketRank(b)
  if (rankDiff !== 0) return rankDiff
  return new Date(b.updatedAt) - new Date(a.updatedAt)
}))

function openOrganization(organizationId) {
  void selectHqOrganization(organizationId)
}

function resetOrganizationForm() {
  Object.assign(organizationForm, {
    organizationName: '',
    organizationCode: '',
    managerName: '',
    managerUsername: '',
    managerEmail: '',
    managerPhone: '',
    managerPassword: '',
  })
}

async function submitOrganization() {
  await createHqOrganization({ ...organizationForm })
  resetOrganizationForm()
}

onMounted(() => {
  void loadHqPanel(true)
})
</script>

<template>
  <section class="page-shell hq-report-page">
    <section v-if="!state.currentUser.canUseHq" class="surface-block hq-locked">
      <span class="material-symbols-outlined">lock</span>
      <strong>HQ</strong>
    </section>

    <template v-else>
      <section class="hq-report-grid">
        <article v-for="item in summaryCards" :key="item.label" class="hq-report-card">
          <span class="material-symbols-outlined">{{ item.icon }}</span>
          <strong>{{ item.value }}</strong>
          <small>{{ item.label }}</small>
        </article>
      </section>

      <section class="surface-block hq-report-surface">
        <div class="section-label-row">
          <h3>مجموعه‌ها</h3>
          <button class="icon-btn" type="button" :disabled="state.hq.loading" @click="loadHqPanel(true)">
            <span class="material-symbols-outlined">sync</span>
          </button>
        </div>

        <div class="table-shell">
          <table class="data-table">
            <thead>
              <tr>
                <th>مجموعه</th>
                <th>کد</th>
                <th>کاربر</th>
                <th>پرداخت</th>
                <th>درخواست</th>
                <th>سند</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="organization in reportRows" :key="organization.id">
                <td>
                  <strong>{{ organization.name }}</strong>
                  <small class="table-muted">{{ organization.createdAt }}</small>
                </td>
                <td>{{ organization.code }}</td>
                <td>{{ organization.activeUsers }} / {{ organization.users }}</td>
                <td>{{ organization.paymentTotal }}</td>
                <td>{{ organization.requests }}</td>
                <td>{{ organization.documents }}</td>
                <td>
                  <button class="action-btn tone-soft" type="button" @click="openOrganization(organization.id)">
                    <span class="material-symbols-outlined">input</span>
                    <span>انتخاب</span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="surface-block hq-create-surface">
        <div class="section-label-row">
          <h3>اضافه کردن مجموعه</h3>
        </div>

        <form class="hq-create-form" @submit.prevent="submitOrganization">
          <label>
            <span>نام مجموعه</span>
            <input v-model="organizationForm.organizationName" required />
          </label>
          <label>
            <span>کد مجموعه</span>
            <input v-model="organizationForm.organizationCode" dir="ltr" placeholder="business-code" />
          </label>
          <label>
            <span>نام مدیر</span>
            <input v-model="organizationForm.managerName" required />
          </label>
          <label>
            <span>نام کاربری مدیر</span>
            <input v-model="organizationForm.managerUsername" dir="ltr" required />
          </label>
          <label>
            <span>ایمیل مدیر</span>
            <input v-model="organizationForm.managerEmail" dir="ltr" type="email" placeholder="optional@email.com" />
          </label>
          <label>
            <span>تلفن مدیر</span>
            <input v-model="organizationForm.managerPhone" dir="ltr" />
          </label>
          <label>
            <span>رمز عبور مدیر</span>
            <input v-model="organizationForm.managerPassword" dir="ltr" required type="password" />
          </label>
          <button class="action-btn tone-primary hq-create-submit" type="submit" :disabled="state.hq.saving">
            <span class="material-symbols-outlined">domain_add</span>
            <span>{{ state.hq.saving ? 'در حال ثبت' : 'ثبت مجموعه' }}</span>
          </button>
        </form>
      </section>

      <section class="surface-block hq-report-surface">
        <div class="section-label-row">
          <h3>تیکت‌های HQ</h3>
        </div>

        <div class="table-shell">
          <table class="data-table">
            <thead>
              <tr>
                <th>عنوان</th>
                <th>مجموعه</th>
                <th>ثبت‌کننده</th>
                <th>دسته</th>
                <th>وضعیت</th>
                <th>آخرین به‌روزرسانی</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ticket in ticketRows" :key="ticket.id">
                <td>
                  <strong>{{ ticket.subject }}</strong>
                  <small class="table-muted">{{ ticket.lastMessagePreview }}</small>
                </td>
                <td>{{ ticket.organization }}</td>
                <td>{{ ticket.requester || '-' }}</td>
                <td>{{ ticket.categoryLabel }}</td>
                <td>{{ ticket.statusLabel }}</td>
                <td>{{ ticket.updatedAtIso }}</td>
              </tr>
              <tr v-if="!ticketRows.length">
                <td colspan="6" class="table-empty">تیکتی ثبت نشده است.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="hq-report-lower">
        <article class="surface-block">
          <div class="section-label-row">
            <h3>نقش‌ها</h3>
          </div>
          <div class="hq-segment-list">
            <div v-for="item in state.hq.segments.roles" :key="item.key" class="hq-segment-row">
              <span>{{ item.label }}</span>
              <strong>{{ item.count }}</strong>
            </div>
          </div>
        </article>

        <article class="surface-block">
          <div class="section-label-row">
            <h3>پرداخت‌ها</h3>
          </div>
          <div class="hq-segment-list">
            <div v-for="item in state.hq.segments.payments" :key="item.key" class="hq-segment-row">
              <span>{{ item.label }}</span>
              <strong>{{ item.count }}</strong>
            </div>
          </div>
        </article>

        <article class="surface-block">
          <div class="section-label-row">
            <h3>وضعیت تیکت‌ها</h3>
          </div>
          <div class="hq-segment-list">
            <div v-for="item in state.hq.segments.tickets" :key="item.key" class="hq-segment-row">
              <span>{{ item.label }}</span>
              <strong>{{ item.count }}</strong>
            </div>
          </div>
        </article>
      </section>
    </template>
  </section>
</template>

<style scoped>
.hq-report-page {
  gap: 16px;
}

.hq-report-grid,
.hq-report-lower {
  display: grid;
  gap: 14px;
}

.hq-report-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.hq-report-lower {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.hq-report-card {
  min-height: 132px;
  padding: 18px;
  border-radius: 12px;
  display: grid;
  align-content: space-between;
  background: var(--surface, #fff);
  border: 1px solid var(--line);
  box-shadow: none;
}

.hq-locked {
  min-height: 320px;
  display: grid;
  place-items: center;
  color: var(--muted);
}

.hq-report-card .material-symbols-outlined {
  color: var(--accent-strong);
}

.hq-report-card strong {
  color: var(--primary);
  font-size: 24px;
  overflow-wrap: anywhere;
}

.hq-report-card small,
.hq-segment-row span,
.hq-audit-row small {
  color: var(--muted);
}

.hq-report-surface {
  min-width: 0;
}

.hq-create-surface {
  min-width: 0;
}

.hq-create-form {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}

.hq-create-form label {
  min-width: 0;
  display: grid;
  gap: 7px;
}

.hq-create-form label span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
}

.hq-create-form input {
  width: 100%;
  min-height: 48px;
  padding: 10px 12px;
  border-radius: 16px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.78);
  color: var(--primary);
}

.hq-create-submit {
  align-self: end;
  min-height: 48px;
}

.hq-segment-list,
.hq-audit-list {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.hq-segment-row,
.hq-audit-row {
  min-height: 54px;
  padding: 12px 14px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: rgba(255, 255, 255, 0.68);
  border: 1px solid rgba(36, 59, 107, 0.08);
}

.hq-audit-row {
  justify-content: flex-start;
}

.hq-audit-row div {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.hq-audit-row strong,
.hq-audit-row small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 1120px) {
  .hq-report-grid,
  .hq-report-lower,
  .hq-create-form {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .hq-report-grid,
  .hq-report-lower,
  .hq-create-form {
    grid-template-columns: 1fr;
  }
}
</style>
