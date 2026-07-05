<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import PageFilters from './PageFilters.vue'
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
  state,
  toggleSidebar,
  updatePageFilter,
  userPeople,
} = useWorkflowHub()

const displayName = computed(() => state.currentUser.name || 'کاربر')

const pageConfig = computed(() => {
  const configs = {
    '/dashboard': {
      eyebrow: 'مرکز کنترل',
      title: 'داشبورد اجرایی',
      description: 'منوی سمت راست، هدر و ابزارهای کلیدی همیشه ثابت می‌مانند و فقط محتوای اصلی صفحه تغییر می‌کند.',
    },
    '/requests': {
      eyebrow: 'درخواست‌ها',
      title: 'مدیریت درخواست‌های سازمانی',
      description: 'ثبت، پیگیری و تفکیک درخواست‌ها با فیلتر سراسری و اکشن سریع.',
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
    '/approvals': {
      eyebrow: 'تاییدها',
      title: 'گردش سند، ارجاع و امضا',
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
      description: 'نمای تفکیکی گزارش درخواست‌ها، هزینه‌ها و تاییدها با خروجی مستقیم.',
      filterPage: 'reports',
    },
    '/users': {
      eyebrow: 'کاربران',
      title: 'فهرست فشرده کاربران و نقش‌ها',
      description: 'کارت‌ها و جدول‌های سبک‌تر برای پیدا کردن سریع‌تر افراد و مدیریت بهتر.',
      filterPage: 'users',
      actions: state.currentUser.canManageUsers
        ? [{ label: 'افزودن کاربر', icon: 'person_add', handler: openUserComposer, tone: 'primary' }]
        : [],
    },
    '/settings': {
      eyebrow: 'تنظیمات',
      title: 'پیکربندی سازمان و سطح دسترسی',
      description: 'تنظیمات اصلی سازمان و دسترسی بخش‌ها در قالبی جدولی و مقیاس‌پذیر.',
    },
  }

  return configs[route.path] || {
    eyebrow: 'سامانه سازمانی',
    title: 'کارمند',
    description: '',
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
</script>

<template>
  <header class="topbar-shell">
    <div class="topbar-main-row">
      <div class="topbar-intro">
        <button class="icon-btn mobile-menu-trigger" type="button" @click="toggleSidebar">
          <span class="material-symbols-outlined">menu</span>
        </button>

        <div class="topbar-intro-copy">
          <span class="topbar-eyebrow">{{ pageConfig.eyebrow }}</span>
          <strong>{{ pageConfig.title }}</strong>
          <small v-if="pageConfig.description">{{ pageConfig.description }}</small>
        </div>
      </div>

      <div class="topbar-actions">
        <div v-if="pageConfig.actions?.length" class="topbar-action-row">
          <button
            v-for="action in pageConfig.actions"
            :key="action.label"
            :class="['action-btn', `tone-${action.tone || 'primary'}`]"
            type="button"
            @click="action.handler"
          >
            <span class="material-symbols-outlined">{{ action.icon }}</span>
            <span>{{ action.label }}</span>
          </button>
        </div>

        <div class="topbar-user-card">
          <div class="topbar-avatar">
            {{ (displayName || 'ک').slice(0, 1) }}
          </div>
          <div class="topbar-user-copy">
            <strong>{{ displayName }}</strong>
            <small>{{ state.currentUser.role || state.currentUser.department || 'عضو سازمان' }}</small>
          </div>
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
