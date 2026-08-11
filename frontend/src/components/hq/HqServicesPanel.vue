<script setup>
import IconlyIcon from '../base/IconlyIcon.vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const TOKEN_KEY = 'workflow-hub-token'

const loading = ref(false)
const errorMessage = ref('')
const payload = ref({
  summary: {},
  catalog: { products: [] },
  rows: [],
  pagination: { total: 0, page: 1, pages: 1, pageSize: 25 },
  revenueByProduct: [],
  revenueByOrganization: [],
  alerts: [],
  organizations: [],
})

const reportTab = ref('all')
const filters = reactive({
  q: '',
  featureKey: '',
  organizationId: '',
  status: '',
  paymentPlan: '',
  hasDebt: false,
  nearExpiry: false,
  isActive: '',
  page: 1,
})

const reportTabs = [
  { key: 'all', label: 'همه سرویس‌ها' },
  { key: 'core_software', label: 'نرم‌افزار پایه', featureKey: 'core_software' },
  { key: 'cloud_storage', label: 'فضای ابری', featureKey: 'cloud_storage' },
  { key: 'attendance', label: 'ورود و خروج', featureKey: 'attendance' },
  { key: 'revenue', label: 'ماتریس درآمد' },
]

const statusOptions = [
  { value: '', label: 'همه وضعیت‌ها' },
  { value: 'active', label: 'فعال' },
  { value: 'inactive', label: 'غیرفعال' },
  { value: 'pending_payment', label: 'بدهکار' },
  { value: 'overdue', label: 'معوق' },
  { value: 'near_expiry', label: 'نزدیک تمدید' },
  { value: 'locked', label: 'قفل لایسنس' },
]

const fa = (value) => Number(value || 0).toLocaleString('fa-IR')
const money = (value) => {
  if (value == null || value === '') return '۰'
  if (typeof value === 'string' && /[,۰-۹]/.test(value)) return value
  return fa(Math.round(Number(value) || 0))
}

const summary = computed(() => payload.value.summary || {})
const rows = computed(() => payload.value.rows || [])
const pagination = computed(() => payload.value.pagination || {})
const alerts = computed(() => payload.value.alerts || [])
const products = computed(() => payload.value.catalog?.products || [])
const revenueByProduct = computed(() => payload.value.revenueByProduct || [])
const revenueByOrganization = computed(() => payload.value.revenueByOrganization || [])
const organizations = computed(() => payload.value.organizations || [])

const statusLabel = (status) => statusOptions.find((item) => item.value === status)?.label || status
const statusTone = (status) => ({
  active: 'is-success',
  inactive: 'is-muted',
  pending_payment: 'is-warning',
  overdue: 'is-danger',
  near_expiry: 'is-warning',
  locked: 'is-danger',
}[status] || 'is-info')

const kpiCards = computed(() => [
  { label: 'مجموعه‌ها', value: fa(summary.value.organizationsCount), hint: 'مشتری فعال' },
  { label: 'مشتری با سرویس', value: fa(summary.value.activeClientsCount), hint: 'حداقل یک اشتراک فعال' },
  { label: 'اشتراک فعال', value: fa(summary.value.activeSubscriptions), hint: `از ${fa(summary.value.subscriptionsCount)}` },
  { label: 'فروش کل', value: money(summary.value.salesTotalRaw ?? summary.value.salesTotal), hint: 'ریال' },
  { label: 'دریافتی', value: money(summary.value.paidTotalRaw ?? summary.value.paidTotal), hint: 'ریال' },
  { label: 'مطالبات', value: money(summary.value.receivablesRaw ?? summary.value.receivables), hint: 'باقی‌مانده' },
  { label: 'معوق', value: fa(summary.value.overdueCount), hint: 'قسط/بدهی' },
  { label: 'نزدیک تمدید', value: fa(summary.value.nearExpiryCount), hint: '۳۰ روز' },
  { label: 'قفل لایسنس', value: fa(summary.value.lockedCount), hint: 'نیاز پیگیری' },
  { label: 'بالانس کیف پول', value: money(summary.value.walletBalanceTotalRaw ?? summary.value.walletBalanceTotal), hint: 'کل مجموعه‌ها' },
  { label: 'فرصت فروش', value: fa(summary.value.unpurchasedSlots), hint: 'سرویس نخریده' },
  { label: 'هشدار', value: fa(summary.value.alertsCount), hint: 'مورد نیاز اقدام' },
])

async function loadServices() {
  loading.value = true
  errorMessage.value = ''
  try {
    const params = new URLSearchParams()
    if (filters.q) params.set('q', filters.q)
    if (filters.organizationId) params.set('organizationId', filters.organizationId)
    if (filters.status) params.set('status', filters.status)
    if (filters.paymentPlan) params.set('paymentPlan', filters.paymentPlan)
    if (filters.hasDebt) params.set('hasDebt', '1')
    if (filters.nearExpiry) params.set('nearExpiry', '1')
    if (filters.isActive) params.set('isActive', filters.isActive)
    params.set('page', String(filters.page))
    const activeTab = reportTabs.find((item) => item.key === reportTab.value)
    if (activeTab?.featureKey) params.set('featureKey', activeTab.featureKey)
    else if (filters.featureKey) params.set('featureKey', filters.featureKey)

    const response = await fetch(`${API_BASE_URL}/hq/services?${params}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY) || ''}` },
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(data.detail || data.message || 'بارگذاری سرویس‌ها ناموفق بود.')
    payload.value = data
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

function selectReportTab(key) {
  reportTab.value = key
  filters.page = 1
  const tab = reportTabs.find((item) => item.key === key)
  filters.featureKey = tab?.featureKey || ''
  void loadServices()
}

function resetFilters() {
  Object.assign(filters, { q: '', featureKey: '', organizationId: '', status: '', paymentPlan: '', hasDebt: false, nearExpiry: false, isActive: '', page: 1 })
  reportTab.value = 'all'
  void loadServices()
}

function exportCsv() {
  const headers = ['مجموعه', 'کد', 'سرویس', 'وضعیت', 'طرح', 'فروش', 'دریافتی', 'مانده', 'قسط بعد', 'تمدید', 'خرید']
  const lines = (rows.value.length ? rows.value : revenueByOrganization.value).map((row) => [
    row.organizationName || row.featureTitle,
    row.organizationCode || row.featureKey,
    row.featureTitle || row.organizationName,
    statusLabel(row.status) || '',
    row.paymentPlan || '',
    row.totalAmountRaw ?? row.salesRaw ?? '',
    row.paidAmountRaw ?? row.paidRaw ?? '',
    row.remainingAmountRaw ?? row.remainingRaw ?? '',
    row.nextInstallmentDueAt || '',
    row.renewalDueAt || '',
    row.purchasedAt || '',
  ].map((cell) => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(','))
  const csv = `\uFEFF${headers.join(',')}\n${lines.join('\n')}`
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'hq-services.csv'
  link.click()
  URL.revokeObjectURL(url)
}

watch(() => filters.page, () => void loadServices())

onMounted(() => void loadServices())
</script>

<template>
  <section class="hq-services-panel">
    <header class="hq-services-hero">
      <div>
        <span class="page-eyebrow">HQ Services</span>
        <h2>سرویس‌ها و اشتراک‌ها</h2>
        <p>مدیریت یکپارچه فروش، دریافت، مطالبات، تمدید و وضعیت سرویس‌های کارنومند</p>
      </div>
      <div class="hq-services-hero-actions">
        <button class="action-btn tone-soft" type="button" :disabled="loading" @click="loadServices">
          <IconlyIcon name="refresh" decorative />
          <span>بروزرسانی</span>
        </button>
        <button class="action-btn tone-primary" type="button" @click="exportCsv">
          <IconlyIcon name="download" decorative />
          <span>CSV</span>
        </button>
      </div>
    </header>

    <div v-if="errorMessage" class="attendance-alert is-danger">{{ errorMessage }}</div>

    <div v-if="alerts.length" class="hq-services-alerts">
      <article v-for="alert in alerts.slice(0, 6)" :key="`${alert.type}-${alert.purchaseId}`" :class="['hq-alert-chip', alert.severity]">
        {{ alert.message }}
      </article>
    </div>

    <div class="hq-services-kpis">
      <article v-for="card in kpiCards" :key="card.label">
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <small>{{ card.hint }}</small>
      </article>
    </div>

    <div class="hq-services-tabs">
      <button
        v-for="tab in reportTabs"
        :key="tab.key"
        type="button"
        :class="['hq-services-tab', reportTab === tab.key && 'is-active']"
        @click="selectReportTab(tab.key)"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="hq-services-filters">
      <label class="search-shell search-shell-wide">
        <IconlyIcon name="search" decorative />
        <input v-model="filters.q" type="text" placeholder="جستجو مجموعه، کد یا سرویس..." @keyup.enter="loadServices" />
      </label>
      <label class="field-shell">
        <span>مجموعه</span>
        <select v-model="filters.organizationId">
          <option value="">همه</option>
          <option v-for="org in organizations" :key="org.id" :value="org.id">{{ org.name }}</option>
        </select>
      </label>
      <label class="field-shell">
        <span>وضعیت</span>
        <select v-model="filters.status">
          <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </label>
      <label class="field-shell">
        <span>طرح پرداخت</span>
        <select v-model="filters.paymentPlan">
          <option value="">همه</option>
          <option value="cash">نقد</option>
          <option value="installment">اقساط</option>
        </select>
      </label>
      <label class="field-shell hq-checkbox-field">
        <input v-model="filters.hasDebt" type="checkbox" />
        <span>فقط بدهکار</span>
      </label>
      <label class="field-shell hq-checkbox-field">
        <input v-model="filters.nearExpiry" type="checkbox" />
        <span>نزدیک تمدید</span>
      </label>
      <button class="action-btn tone-primary" type="button" @click="() => { filters.page = 1; loadServices() }">اعمال</button>
      <button class="action-btn tone-soft" type="button" @click="resetFilters">پاک‌سازی</button>
    </div>

    <section v-if="reportTab === 'revenue'" class="surface-block hq-services-card">
      <div class="section-label-row">
        <div>
          <h3>ماتریس درآمد یکپارچه</h3>
          <p class="hq-subtitle">تفکیک فروش، دریافت و مطالبات — بدون سهم‌بندی</p>
        </div>
      </div>
      <div class="attendance-table-wrap">
        <table class="attendance-report-table">
          <thead>
            <tr>
              <th>سرویس</th>
              <th>تعداد</th>
              <th>فعال</th>
              <th>فروش</th>
              <th>دریافتی</th>
              <th>مطالبات</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in revenueByProduct" :key="row.featureKey">
              <td><strong>{{ row.featureTitle }}</strong></td>
              <td>{{ fa(row.subscriptionsCount) }}</td>
              <td>{{ fa(row.activeCount) }}</td>
              <td>{{ money(row.salesRaw ?? row.sales) }}</td>
              <td>{{ money(row.paidRaw ?? row.paid) }}</td>
              <td>{{ money(row.remainingRaw ?? row.remaining) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <h4 class="hq-section-title">به تفکیک مجموعه</h4>
      <div class="attendance-table-wrap">
        <table class="attendance-report-table">
          <thead>
            <tr>
              <th>مجموعه</th>
              <th>اشتراک</th>
              <th>فعال</th>
              <th>فروش</th>
              <th>دریافتی</th>
              <th>مطالبات</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in revenueByOrganization" :key="row.organizationId">
              <td><strong>{{ row.organizationName }}</strong><small class="hq-cell-sub">{{ row.organizationCode }}</small></td>
              <td>{{ fa(row.subscriptionsCount) }}</td>
              <td>{{ fa(row.activeCount) }}</td>
              <td>{{ money(row.salesRaw ?? row.sales) }}</td>
              <td>{{ money(row.paidRaw ?? row.paid) }}</td>
              <td>{{ money(row.remainingRaw ?? row.remaining) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-else class="surface-block hq-services-card">
      <div class="section-label-row">
        <div>
          <h3>لیست اشتراک‌ها</h3>
          <p class="hq-subtitle">{{ fa(pagination.total) }} ردیف · صفحه {{ fa(pagination.page) }} از {{ fa(pagination.pages) }}</p>
        </div>
      </div>
      <div class="attendance-table-wrap">
        <table class="attendance-report-table hq-services-table">
          <thead>
            <tr>
              <th>مجموعه</th>
              <th>سرویس</th>
              <th>وضعیت</th>
              <th>طرح</th>
              <th>فروش</th>
              <th>دریافتی</th>
              <th>مانده</th>
              <th>قسط بعد</th>
              <th>تمدید</th>
              <th>خرید</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="10">در حال بارگذاری...</td></tr>
            <tr v-for="row in rows" v-else :key="row.id">
              <td>
                <strong>{{ row.organizationName }}</strong>
                <small class="hq-cell-sub">{{ row.organizationCode }}</small>
              </td>
              <td>{{ row.featureTitle }}</td>
              <td><span :class="['status-badge', statusTone(row.status)]">{{ statusLabel(row.status) }}</span></td>
              <td>{{ row.paymentPlan === 'installment' ? 'اقساط' : row.paymentPlan === 'cash' ? 'نقد' : row.paymentPlan || '-' }}</td>
              <td>{{ money(row.totalAmountRaw ?? row.totalAmount) }}</td>
              <td>{{ money(row.paidAmountRaw ?? row.paidAmount) }}</td>
              <td>{{ money(row.remainingAmountRaw ?? row.remainingAmount) }}</td>
              <td>{{ row.nextInstallmentDueAt || '-' }}</td>
              <td>{{ row.renewalDueAt || '-' }}</td>
              <td>{{ row.purchasedAt || '-' }}</td>
            </tr>
            <tr v-if="!loading && !rows.length"><td colspan="10">اشتراکی یافت نشد.</td></tr>
          </tbody>
        </table>
      </div>
      <div v-if="pagination.pages > 1" class="hq-pagination">
        <button class="action-btn tone-soft" type="button" :disabled="filters.page <= 1 || loading" @click="filters.page -= 1">قبلی</button>
        <span>{{ fa(filters.page) }} / {{ fa(pagination.pages) }}</span>
        <button class="action-btn tone-soft" type="button" :disabled="filters.page >= pagination.pages || loading" @click="filters.page += 1">بعدی</button>
      </div>
    </section>

    <section class="surface-block hq-services-card">
      <div class="section-label-row"><h3>کاتالوگ سرویس‌ها</h3></div>
      <div class="hq-catalog-grid">
        <article v-for="product in products" :key="product.featureKey" :class="['hq-catalog-card', product.disabled && 'is-disabled']">
          <strong>{{ product.title }}</strong>
          <small>{{ product.subtitle }}</small>
          <span>{{ product.disabled ? 'غیرفعال' : money(product.basePriceRaw ?? product.basePrice) }}</span>
        </article>
      </div>
    </section>
  </section>
</template>

<style scoped>
.hq-services-panel { display: grid; gap: 14px; min-width: 0; }
.hq-services-hero {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 14px;
  padding: 20px; border-radius: 16px;
  background: linear-gradient(135deg, rgba(220,239,236,.95), rgba(255,255,255,.92));
  border: 1px solid var(--line);
}
.hq-services-hero h2 { margin: 8px 0 6px; color: var(--primary); font-size: clamp(1.2rem, 3vw, 1.7rem); }
.hq-services-hero p { margin: 0; color: var(--muted); line-height: 1.7; }
.hq-services-hero-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.hq-services-kpis {
  display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 10px;
}
.hq-services-kpis article {
  padding: 12px; border-radius: 14px; background: rgba(255,255,255,.88); border: 1px solid var(--line);
}
.hq-services-kpis span { display: block; color: var(--muted); font-size: 11px; }
.hq-services-kpis strong { display: block; margin-top: 6px; color: var(--primary); font-size: 1.15rem; }
.hq-services-kpis small { display: block; margin-top: 4px; color: var(--muted); font-size: 10px; }
.hq-services-tabs, .hq-services-filters { display: flex; flex-wrap: wrap; gap: 8px; }
.hq-services-tab {
  min-height: 38px; padding: 0 14px; border-radius: 999px; border: 1px solid var(--line);
  background: rgba(255,255,255,.82); color: var(--primary); font: inherit; font-size: 12px; font-weight: 700; cursor: pointer;
}
.hq-services-tab.is-active { background: var(--button-primary-bg, #34908B); color: #fff; border-color: transparent; }
.hq-services-filters { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; align-items: end; }
.hq-services-filters .search-shell-wide { grid-column: 1 / -1; }
.hq-checkbox-field { flex-direction: row; align-items: center; gap: 8px; min-height: 52px; }
.hq-services-card { display: grid; gap: 12px; }
.hq-subtitle { margin: 6px 0 0; color: var(--muted); font-size: 12px; }
.hq-cell-sub { display: block; margin-top: 4px; color: var(--muted); font-size: 11px; }
.hq-section-title { margin: 12px 0 0; color: var(--primary); font-size: 0.95rem; }
.hq-services-table { min-width: 980px; }
.hq-pagination { display: flex; align-items: center; justify-content: center; gap: 12px; }
.hq-services-alerts { display: flex; flex-wrap: wrap; gap: 8px; }
.hq-alert-chip {
  padding: 8px 12px; border-radius: 12px; font-size: 12px; font-weight: 700;
  background: rgba(52,144,139,.1); color: var(--primary); border: 1px solid var(--line);
}
.hq-alert-chip.critical { background: var(--danger-soft); color: var(--danger); }
.hq-alert-chip.warning { background: var(--warning-soft); color: var(--warning); }
.hq-catalog-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }
.hq-catalog-card {
  padding: 14px; border-radius: 14px; border: 1px solid var(--line); background: rgba(255,255,255,.82);
  display: grid; gap: 6px;
}
.hq-catalog-card.is-disabled { opacity: .55; }
.hq-catalog-card strong { color: var(--primary); }
.hq-catalog-card small { color: var(--muted); line-height: 1.5; }
.status-badge.is-muted { background: rgba(36,59,107,.08); color: var(--muted); }
@media (max-width: 1100px) { .hq-services-kpis { grid-template-columns: repeat(3, minmax(0,1fr)); } .hq-services-hero { flex-direction: column; } }
@media (max-width: 760px) { .hq-services-kpis { grid-template-columns: repeat(2, minmax(0,1fr)); } }
</style>
