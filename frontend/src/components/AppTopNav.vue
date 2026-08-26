<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

import AttendancePunchModal from './AttendancePunchModal.vue'
import PageFilters from './PageFilters.vue'
import TitleHint from './TitleHint.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const route = useRoute()
const {
  approvalPeople,
  archivePeople,
  expensePeople,
  openDocumentComposer,
  openExpenseComposer,
  openRequestComposer,
  openSignatureComposer,
  openArchiveComposer,
  reportPeople,
  requestPeople,
  resetPageFilters,
  selectHqOrganization,
  state,
  toggleSidebar,
  updatePageFilter,
  userPeople,
} = useWorkflowHub()

const attendancePunchOpen = ref(false)
const hqOrganizations = computed(() => state.hq.directories.organizations || [])
const attendanceToken = computed(() =>
  String(state.currentUser.attendanceToken || state.currentUser.attendance_token || '').trim(),
)
const canPunchAttendance = computed(() =>
  Boolean(
    !state.currentUser.isHq &&
    attendanceToken.value &&
    state.currentUser.menuAccess?.attendance === true,
  ),
)

const pageConfig = computed(() => {
  const configs = {
    dashboard: {
      eyebrow: 'مرکز کنترل',
      title: 'داشبورد اجرایی',
      description: 'نمای خلاصه وضعیت درخواست‌ها، هزینه‌ها و تاییدها برای تصمیم‌گیری سریع روز.',
      actions: [],
    },
    requests: {
      eyebrow: 'درخواست‌ها',
      title: 'مدیریت درخواست‌های سازمانی',
      description: 'ثبت، پیگیری و مدیریت درخواست‌های سازمانی در یک فهرست فشرده و خوانا.',
      filterPage: 'requests',
      actions: [{ label: 'ثبت درخواست', icon: 'add_circle', handler: openRequestComposer, tone: 'primary' }],
    },
    expenses: {
      eyebrow: 'هزینه‌ها',
      title: 'کنترل هزینه و اسناد مالی',
      description: 'ثبت هزینه، مرور فاکتورها و پایش وضعیت‌ها در یک نمای فشرده و خوانا.',
      filterPage: 'expenses',
      actions: [{ label: 'ثبت هزینه', icon: 'receipt_long', handler: openExpenseComposer, tone: 'primary' }],
    },
    wallet: {
      eyebrow: 'کیف پول',
      title: 'کیف پول',
      description: 'موجودی، واریز، خرید امکانات و پیگیری تراکنش‌های مالی مجموعه.',
    },
    support: {
      eyebrow: 'پشتیبانی',
      title: 'پشتیبانی',
      description: 'ثبت تیکت، پیگیری گفتگوها و ارتباط مستقیم با تیم پشتیبانی.',
    },
    attendance: {
      eyebrow: 'ورود و خروج',
      title: 'ورود و خروج پرسنل',
      description: 'کنترل حضور، لینک اختصاصی هر کاربر و گزارش ساعات کاری نیروها.',
    },
    cloud: {
      eyebrow: 'فضای ابری',
      title: 'فضای ابری',
      description: 'نگهداری و دسترسی به اسناد و فایل‌های عملیاتی مجموعه.',
    },
    approvals: {
      eyebrow: 'تاییدها',
      title: 'ثبت سند و ارجاع و امضا',
      description: 'ارسال سند، انتخاب گیرنده و دانلود نسخه نهایی با وضعیت‌های تفکیک‌پذیر.',
      filterPage: 'approvals',
      actions: [
        { label: 'ثبت سند', icon: 'upload_file', handler: openDocumentComposer, tone: 'primary' },
        ...(state.currentUser.canApproveDocuments
          ? [{ label: 'ثبت امضا', icon: 'draw', handler: openSignatureComposer, tone: 'soft' }]
          : []),
      ],
    },
    archive: {
      eyebrow: 'بایگانی الکترونیکی',
      title: 'بایگانی اسناد سازمانی',
      description: 'ثبت نام و توضیحات سند، تاریخ، بارگذاری فایل و ارجاع به اعضای مجموعه.',
      filterPage: 'archive',
      filterVariant: 'archive',
      actions: [{ label: 'ثبت سند بایگانی', icon: 'upload_file', handler: openArchiveComposer, tone: 'primary' }],
    },
    reports: {
      eyebrow: 'گزارشات',
      title: 'گزارش‌های مدیریتی و خروجی‌ها',
      description: 'نمای تفکیکی گزارش در درخواست‌ها، هزینه‌ها و تاییدها با خروجی مستقیم.',
      // Filters live on the page (period chips + person) — topbar dates/person fight them on mobile.
    },
    users: {
      eyebrow: 'کاربران',
      title: 'فهرست فشرده کاربران و نقش‌ها',
      description: 'کارت‌ها و جدول‌های سبک‌تر برای پیدا کردن سریع‌تر افراد و مدیریت بهتر.',
    },
    settings: {
      eyebrow: 'تنظیمات',
      title: 'پیکربندی سازمان و سطح دسترسی',
      description: 'تنظیمات اصلی سازمان و دسترسی بخش‌ها در قالبی جدولی و مقیاس‌پذیر.',
    },
    hq: {
      eyebrow: 'HQ',
      title: 'گزارشات HQ',
      description: 'نظارت مرکزی بر مجموعه‌ها، تیکت‌ها، کیف پول و وضعیت سرویس.',
    },
  }

  const byName = configs[String(route.name || '')]
  if (byName) return byName

  const byPath = configs[String(route.path || '').replace(/^\//, '')]
  return byPath || {
    eyebrow: 'سامانه سازمانی',
    title: 'کارنومند',
    description: 'مرکز عملیات سازمانی کارنومند برای مدیریت فرآیندهای روزانه.',
  }
})

const peopleByPage = computed(() => ({
  requests: requestPeople.value,
  expenses: expensePeople.value,
  approvals: approvalPeople.value,
  reports: reportPeople.value,
  users: userPeople.value,
  archive: archivePeople.value,
}))

const activeFilterPage = computed(() => pageConfig.value.filterPage || '')
const activeFilters = computed(() => (activeFilterPage.value ? state.filters[activeFilterPage.value] : null))
const activePeople = computed(() => peopleByPage.value[activeFilterPage.value] || [])
const filterVariant = computed(() => pageConfig.value.filterVariant || 'default')

function setFilter(key, value) {
  if (!activeFilterPage.value) return
  updatePageFilter(activeFilterPage.value, key, value)
}

function resetFilters() {
  if (!activeFilterPage.value) return
  resetPageFilters(activeFilterPage.value)
}

function handleHqOrganizationChange(event) {
  void selectHqOrganization(event.target.value)
}
</script>

<template>
  <header class="topbar-shell" :data-route="route.name || route.path">
    <div class="topbar-main-row">
      <div class="topbar-intro">
        <button class="icon-btn mobile-menu-trigger" type="button" aria-label="باز کردن منو" @click="toggleSidebar">
          <IconlyIcon name="menu" decorative />
        </button>

        <div class="topbar-intro-copy">
          <span class="topbar-eyebrow">{{ pageConfig.eyebrow }}</span>
          <div class="topbar-title-row">
            <strong>{{ pageConfig.title }}</strong>
            <TitleHint :text="pageConfig.description" label="درباره این صفحه" />
          </div>
        </div>
      </div>

      <div class="topbar-actions">
        <label v-if="state.currentUser.canUseHq" class="hq-organization-select">
          <IconlyIcon name="corporate_fare" decorative />
          <select :value="state.hq.selectedOrganizationId" @change="handleHqOrganizationChange">
            <option value="">مجموعه</option>
            <option v-for="organization in hqOrganizations" :key="organization.id" :value="organization.id">
              {{ organization.name }}
            </option>
          </select>
        </label>

        <div v-if="pageConfig.actions?.length" class="topbar-action-row">
          <button
            v-for="action in pageConfig.actions"
            :key="action.label"
            :class="[
              action.iconOnly ? 'icon-btn topbar-icon-action' : 'action-btn',
              `tone-${action.tone || 'primary'}`,
              action.iconOnly && 'is-icon-only',
              (action.punch || action.icon === 'fingerprint') && 'is-punch-action attendance-punch-topbar-btn',
            ]"
            type="button"
            :aria-label="action.label"
            :title="action.label"
            @click="() => action.handler?.()"
          >
            <IconlyIcon
              :name="action.icon"
              :size="(action.punch || action.icon === 'fingerprint') ? 'xl' : 'md'"
              decorative
            />
            <span v-if="!action.iconOnly">{{ action.label }}</span>
          </button>
        </div>
      </div>
    </div>

    <PageFilters
      v-if="activeFilters"
      class="topbar-filters"
      :variant="filterVariant"
      :query="activeFilters.query"
      :description="activeFilters.description || ''"
      :person="activeFilters.person"
      :start-date="activeFilters.startDate"
      :end-date="activeFilters.endDate"
      :status="activeFilters.status || ''"
      :show-status-filter="['requests', 'expenses', 'approvals'].includes(activeFilterPage)"
      :people="activePeople"
      @update:query="setFilter('query', $event)"
      @update:description="setFilter('description', $event)"
      @update:person="setFilter('person', $event)"
      @update:start-date="setFilter('startDate', $event)"
      @update:end-date="setFilter('endDate', $event)"
      @update:status="setFilter('status', $event)"
      @reset="resetFilters"
    />
  </header>

  <AttendancePunchModal
    :open="attendancePunchOpen"
    :token="attendanceToken"
    @close="attendancePunchOpen = false"
  />
</template>

<style scoped>
.topbar-shell {
  direction: rtl;
  width: 100%;
  max-width: none;
  box-sizing: border-box;
}

.topbar-filters :deep(.modern-page-filters.has-status-filter) {
  grid-template-columns: repeat(5, minmax(0, 1fr)) auto;
}

.topbar-filters {
  width: 100%;
  max-width: none;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr)) auto;
  gap: 10px;
  align-items: end;
  box-sizing: border-box;
}

.topbar-main-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
}

.topbar-intro {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  min-width: 0;
  flex: 1 1 auto;
  text-align: right;
}

.topbar-intro-copy {
  min-width: 0;
  text-align: right;
}

.topbar-title-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 8px;
  min-width: 0;
}

.topbar-title-row strong {
  min-width: 0;
}

.topbar-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  flex: 0 1 auto;
  margin-inline-start: auto;
}

.mobile-menu-trigger {
  flex: 0 0 auto;
  order: 0;
}

.topbar-icon-action.is-icon-only {
  width: 42px;
  height: 42px;
  min-height: 42px;
  padding: 0;
  border-radius: 12px;
  display: inline-grid;
  place-items: center;
}

.topbar-icon-action.is-icon-only.tone-primary {
  background: #34908B;
  color: #fff;
  border: 0;
}

.topbar-icon-action.is-icon-only.is-punch-action,
.topbar-icon-action.is-icon-only.attendance-punch-topbar-btn {
  width: 64px !important;
  height: 64px !important;
  min-width: 64px !important;
  min-height: 64px !important;
  padding: 0 !important;
  border: 0 !important;
  border-radius: 20px !important;
  background: #1f8a70 !important;
  color: #fff !important;
  box-shadow: none !important;
}

.topbar-icon-action.is-icon-only.is-punch-action:hover,
.topbar-icon-action.is-icon-only.is-punch-action:focus-visible,
.topbar-icon-action.is-icon-only.attendance-punch-topbar-btn:hover,
.topbar-icon-action.is-icon-only.attendance-punch-topbar-btn:focus-visible {
  background: #187a63 !important;
  color: #fff !important;
  box-shadow: none !important;
}

.topbar-icon-action.is-icon-only.is-punch-action :deep(.iconly-shell),
.topbar-icon-action.is-icon-only.attendance-punch-topbar-btn :deep(.iconly-shell) {
  font-size: 34px !important;
  color: #fff !important;
  --iconly-filter: brightness(0) invert(1) !important;
}

.topbar-icon-action.is-icon-only.is-punch-action :deep(.iconly-img),
.topbar-icon-action.is-icon-only.attendance-punch-topbar-btn :deep(.iconly-img) {
  filter: brightness(0) invert(1) !important;
}
</style>
