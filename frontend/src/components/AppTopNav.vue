<script setup>
import IconlyIcon from './base/IconlyIcon.vue'
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import PageFilters from './PageFilters.vue'
import TitleHint from './TitleHint.vue'
import { useWorkflowHub } from '../stores/workflowHub'

const route = useRoute()
const {
  approvalPeople,
  expensePeople,
  openDocumentComposer,
  openExpenseComposer,
  openRequestComposer,
  openSignatureComposer,
  openUserComposer,
  reportPeople,
  requestPeople,
  resetPageFilters,
  selectHqOrganization,
  state,
  toggleSidebar,
  updatePageFilter,
  userPeople,
} = useWorkflowHub()

const hqOrganizations = computed(() => state.hq.directories.organizations || [])

const pageConfig = computed(() => {
  const configs = {
    '/dashboard': {
      eyebrow: 'مرکز کنترل',
      title: 'داشبورد اجرایی',
      description: 'نمای خلاصه وضعیت درخواست‌ها، هزینه‌ها و تاییدها برای تصمیم‌گیری سریع روز.',
    },
    '/requests': {
      eyebrow: 'درخواست‌ها',
      title: 'مدیریت درخواست‌های سازمانی',
      description: 'ثبت، پیگیری و مدیریت درخواست‌های سازمانی در یک فهرست فشرده و خوانا.',
      filterPage: 'requests',
      actions: [{ label: 'ثبت درخواست', icon: 'add_circle', handler: openRequestComposer, tone: 'primary' }],
    },
    '/expenses': {
      eyebrow: 'هزینه‌ها',
      title: 'کنترل هزینه و اسناد مالی',
      description: 'ثبت هزینه، مرور فاکتورها و پایش وضعیت‌ها در یک نمای فشرده و خوانا.',
      filterPage: 'expenses',
      actions: [{ label: 'ثبت هزینه', icon: 'receipt_long', handler: openExpenseComposer, tone: 'primary' }],
    },
    '/wallet': {
      eyebrow: 'کیف پول',
      title: 'کیف پول',
      description: 'موجودی، شارژ، خرید امکانات و پیگیری تراکنش‌های مالی مجموعه.',
    },
    '/support': {
      eyebrow: 'پشتیبانی',
      title: 'پشتیبانی',
      description: 'ثبت تیکت، پیگیری گفتگوها و ارتباط مستقیم با تیم پشتیبانی.',
    },
    '/attendance': {
      eyebrow: 'ورود و خروج',
      title: 'ورود و خروج پرسنل',
      description: 'کنترل حضور، لینک اختصاصی هر کاربر و گزارش ساعات کاری نیروها.',
    },
    '/cloud': {
      eyebrow: 'فضای ابری',
      title: 'فضای ابری',
      description: 'نگهداری و دسترسی به اسناد و فایل‌های عملیاتی مجموعه.',
    },
    '/approvals': {
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
    '/reports': {
      eyebrow: 'گزارشات',
      title: 'گزارش‌های مدیریتی و خروجی‌ها',
      description: 'نمای تفکیکی گزارش در درخواست‌ها، هزینه‌ها و تاییدها با خروجی مستقیم.',
      filterPage: 'reports',
    },
    '/users': {
      eyebrow: 'کاربران',
      title: 'فهرست فشرده کاربران و نقش‌ها',
      description: 'کارت‌ها و جدول‌های سبک‌تر برای پیدا کردن سریع‌تر افراد و مدیریت بهتر.',
      actions: state.currentUser.canManageUsers
        ? [{ label: 'افزودن کاربر', icon: 'person_add', handler: openUserComposer, tone: 'primary' }]
        : [],
    },
    '/settings': {
      eyebrow: 'تنظیمات',
      title: 'پیکربندی سازمان و سطح دسترسی',
      description: 'تنظیمات اصلی سازمان و دسترسی بخش‌ها در قالبی جدولی و مقیاس‌پذیر.',
    },
    '/hq': {
      eyebrow: 'HQ',
      title: 'گزارشات HQ',
      description: 'نظارت مرکزی بر مجموعه‌ها، تیکت‌ها، کیف پول و وضعیت سرویس.',
    },
  }

  return configs[route.path] || {
    eyebrow: 'سامانه سازمانی',
    title: 'کارمند',
    description: 'مرکز عملیات سازمانی کارنومند برای مدیریت فرآیندهای روزانه.',
  }
})

const peopleByPage = computed(() => ({
  requests: requestPeople.value,
  expenses: expensePeople.value,
  approvals: approvalPeople.value,
  reports: reportPeople.value,
  users: userPeople.value,
}))

const activeFilterPage = computed(() => pageConfig.value.filterPage || '')
const activeFilters = computed(() => (activeFilterPage.value ? state.filters[activeFilterPage.value] : null))
const activePeople = computed(() => peopleByPage.value[activeFilterPage.value] || [])

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
  <header class="topbar-shell">
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
            :class="['action-btn', `tone-${action.tone || 'primary'}`]"
            type="button"
            @click="action.handler"
          >
            <IconlyIcon :name="action.icon" decorative />
            <span>{{ action.label }}</span>
          </button>
        </div>
      </div>
    </div>

    <PageFilters
      v-if="activeFilters"
      class="topbar-filters"
      :query="activeFilters.query"
      :person="activeFilters.person"
      :start-date="activeFilters.startDate"
      :end-date="activeFilters.endDate"
      :people="activePeople"
      @update:query="setFilter('query', $event)"
      @update:person="setFilter('person', $event)"
      @update:start-date="setFilter('startDate', $event)"
      @update:end-date="setFilter('endDate', $event)"
      @reset="resetFilters"
    />
  </header>
</template>

<style scoped>
.topbar-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.topbar-title-row strong {
  min-width: 0;
}
</style>
