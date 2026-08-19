<script setup>
import IconlyIcon from '../base/IconlyIcon.vue'
import ShamsiDatePicker from '../ShamsiDatePicker.vue'
import { computed, onMounted, reactive, ref } from 'vue'
import { formatJalali, formatTehranDateTime, getTodayIso, getTodayJalali, isoToJalali, jalaliToIso, shiftIsoDate } from '../../utils/jalali'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const TOKEN_KEY = 'workflow-hub-token'

const loading = ref(false)
const errorMessage = ref('')
const workspace = ref('network')
const payload = ref({
  summary: {},
  featureSummary: [],
  organizationRows: [],
  transactionRows: [],
  dailyTrends: [],
  highlights: {},
  organizations: [],
})

const filters = reactive({
  q: '',
  start: '',
  end: '',
  organizationId: '',
  rangeKey: '',
})

const quickRanges = [
  { key: 'month', label: '۳۰ روز' },
  { key: 'week', label: '۷ روز' },
  { key: 'all', label: 'همه' },
]

const workspaces = [
  { key: 'network', label: 'شبکه مجموعه‌ها', icon: 'domain' },
  { key: 'wallet', label: 'کیف پول', icon: 'account_balance_wallet' },
  { key: 'services', label: 'سرویس‌ها', icon: 'payments' },
  { key: 'trends', label: 'روند روزانه', icon: 'calendar' },
]

const fa = (value) => Number(value || 0).toLocaleString('fa-IR')
const money = (value) => {
  if (value == null || value === '') return '۰'
  if (typeof value === 'string' && /[,۰-۹]/.test(value)) return value
  return fa(Math.round(Number(value) || 0))
}

const summary = computed(() => payload.value.summary || {})
const featureSummary = computed(() => payload.value.featureSummary || [])
const organizationRows = computed(() => payload.value.organizationRows || [])
const transactionRows = computed(() => payload.value.transactionRows || [])
const dailyTrends = computed(() => payload.value.dailyTrends || [])
const highlights = computed(() => payload.value.highlights || {})
const organizations = computed(() => payload.value.organizations || [])

const healthLabel = (health) => ({ healthy: 'سالم', watch: 'نیاز پیگیری', critical: 'بحرانی' }[health] || health)
const healthTone = (health) => ({ healthy: 'is-success', watch: 'is-warning', critical: 'is-danger' }[health] || 'is-info')
const txLabel = (type) => ({
  feature_purchase: 'خرید سرویس',
  deposit: 'واریز',
  withdraw: 'برداشت',
  adjustment: 'تعدیل',
}[type] || type)

const kpiCards = computed(() => [
  { label: 'فروش کل', value: money(summary.value.salesTotalRaw ?? summary.value.salesTotal), hint: 'ارزش قرارداد/سرویس' },
  { label: 'دریافتی', value: money(summary.value.paidTotalRaw ?? summary.value.paidTotal), hint: 'وصول شده' },
  { label: 'مطالبات', value: money(summary.value.receivablesRaw ?? summary.value.receivables), hint: 'باقی‌مانده' },
  { label: 'نرخ وصول', value: `${fa(summary.value.collectionRate || 0)}٪`, hint: 'paid / sales' },
  { label: 'واریز کیف پول', value: money(summary.value.depositsTotalRaw ?? summary.value.depositsTotal), hint: 'ورودی نقد' },
  { label: 'برداشت/مصرف', value: money(summary.value.withdrawalsTotalRaw ?? summary.value.withdrawalsTotal), hint: 'خروجی کیف پول' },
  { label: 'خرید سرویس', value: money(summary.value.featurePurchasesTotalRaw ?? summary.value.featurePurchasesTotal), hint: 'از کیف پول' },
  { label: 'بالانس کل', value: money(summary.value.walletBalanceTotalRaw ?? summary.value.walletBalanceTotal), hint: 'موجودی مجموعه‌ها' },
  { label: 'جریان خالص', value: money(summary.value.netWalletFlowRaw ?? summary.value.netWalletFlow), hint: 'واریز - برداشت' },
  { label: 'مجموعه‌ها', value: fa(summary.value.organizationsCount), hint: 'مشتری' },
  { label: 'اشتراک', value: fa(summary.value.subscriptionsCount), hint: 'در بازه' },
  { label: 'تراکنش', value: fa(summary.value.transactionsCount), hint: 'کیف پول' },
])

function applyQuickRange(key) {
  filters.rangeKey = key
  const todayIso = getTodayIso()
  const todayJalali = formatJalali(getTodayJalali())
  if (key === 'all') {
    filters.start = ''
    filters.end = ''
  } else if (key === 'week') {
    filters.start = isoToJalali(shiftIsoDate(todayIso, -6))
    filters.end = todayJalali
  } else {
    filters.start = isoToJalali(shiftIsoDate(todayIso, -29))
    filters.end = todayJalali
  }
  void loadReports()
}

async function loadReports() {
  loading.value = true
  errorMessage.value = ''
  try {
    const params = new URLSearchParams()
    if (filters.q) params.set('q', filters.q)
    if (filters.organizationId) params.set('organizationId', filters.organizationId)
    const startIso = filters.start ? jalaliToIso(filters.start) : ''
    const endIso = filters.end ? jalaliToIso(filters.end) : ''
    if (startIso) params.set('start', startIso)
    if (endIso) params.set('end', endIso)
    const response = await fetch(`${API_BASE_URL}/hq/reports?${params}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY) || ''}` },
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(data.detail || data.message || 'بارگذاری گزارشات HQ ناموفق بود.')
    payload.value = data
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  Object.assign(filters, { q: '', start: '', end: '', organizationId: '', rangeKey: '' })
  void loadReports()
}

function exportCsv() {
  const rows = workspace.value === 'wallet' ? transactionRows.value : organizationRows.value
  const headers = workspace.value === 'wallet'
    ? ['مجموعه', 'نوع', 'جهت', 'مبلغ', 'موجودی بعد', 'زمان', 'یادداشت']
    : ['مجموعه', 'فروش', 'دریافتی', 'مطالبات', 'بالانس', 'واریز', 'برداشت', 'سلامت']
  const lines = rows.map((row) => workspace.value === 'wallet'
    ? [row.organizationName, txLabel(row.transactionType), row.direction, row.amountRaw, row.balanceAfter, row.transactedAt, row.note]
    : [row.organizationName, row.salesTotalRaw, row.paidTotalRaw, row.receivablesRaw, row.walletBalanceRaw, row.depositsTotalRaw, row.withdrawalsTotalRaw, healthLabel(row.health)])
  const csv = `\uFEFF${headers.join(',')}\n${lines.map((line) => line.map((cell) => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(',')).join('\n')}`
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `hq-reports-${formatJalali(getTodayJalali())}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

onMounted(() => applyQuickRange('month'))
</script>

<template>
  <section class="hq-reports-panel">
    <header class="hq-reports-hero">
      <div>
        <span class="page-eyebrow">HQ Reports</span>
        <h2>گزارشات مرکزی</h2>
        <p>نمای یکپارچه درآمد، کیف پول، سرویس‌ها و سلامت مجموعه‌ها — بدون تفکیک سهم</p>
      </div>
      <div class="hq-reports-hero-actions">
        <button class="action-btn tone-soft" type="button" :disabled="loading" @click="loadReports">
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

    <div class="hq-reports-range">
      <button
        v-for="range in quickRanges"
        :key="range.key"
        type="button"
        :class="['hq-range-chip', filters.rangeKey === range.key && 'is-active']"
        @click="applyQuickRange(range.key)"
      >
        {{ range.label }}
      </button>
    </div>

    <div class="hq-reports-filters">
      <label class="search-shell search-shell-wide">
        <IconlyIcon name="search" decorative />
        <input v-model="filters.q" type="text" placeholder="جستجو مجموعه..." @keyup.enter="loadReports" />
      </label>
      <label class="field-shell">
        <span>از تاریخ</span>
        <ShamsiDatePicker v-model="filters.start" model-type="jalali" placeholder="1405/01/01" />
      </label>
      <label class="field-shell">
        <span>تا تاریخ</span>
        <ShamsiDatePicker v-model="filters.end" model-type="jalali" placeholder="1405/12/29" />
      </label>
      <label class="field-shell">
        <span>مجموعه</span>
        <select v-model="filters.organizationId">
          <option value="">همه</option>
          <option v-for="org in organizations" :key="org.id" :value="org.id">{{ org.name }}</option>
        </select>
      </label>
      <button class="action-btn tone-primary" type="button" @click="loadReports">اعمال</button>
      <button class="action-btn tone-soft" type="button" @click="resetFilters">پاک‌سازی</button>
    </div>

    <div class="hq-reports-kpis">
      <article v-for="card in kpiCards" :key="card.label">
        <span>{{ card.label }}</span>
        <strong>{{ card.value }}</strong>
        <small>{{ card.hint }}</small>
      </article>
    </div>

    <div v-if="highlights.topRevenue || highlights.topReceivables" class="hq-highlights">
      <article v-if="highlights.topRevenue">
        <span>بیشترین فروش</span>
        <strong>{{ highlights.topRevenue.organizationName }}</strong>
        <small>{{ money(highlights.topRevenue.salesTotalRaw) }} ریال</small>
      </article>
      <article v-if="highlights.topReceivables">
        <span>بیشترین مطالبات</span>
        <strong>{{ highlights.topReceivables.organizationName }}</strong>
        <small>{{ money(highlights.topReceivables.receivablesRaw) }} ریال</small>
      </article>
      <article v-if="(highlights.renewalsDue || []).length">
        <span>تمدیدهای نزدیک</span>
        <strong>{{ fa(highlights.renewalsDue.length) }}</strong>
        <small>سرویس نیازمند پیگیری</small>
      </article>
    </div>

    <div class="hq-workspace-tabs">
      <button
        v-for="tab in workspaces"
        :key="tab.key"
        type="button"
        :class="['hq-workspace-tab', workspace === tab.key && 'is-active']"
        @click="workspace = tab.key"
      >
        <IconlyIcon :name="tab.icon" decorative />
        <span>{{ tab.label }}</span>
      </button>
    </div>

    <section v-if="workspace === 'network'" class="surface-block hq-reports-card">
      <div class="section-label-row"><h3>رتبه‌بندی مجموعه‌ها</h3></div>
      <div class="attendance-table-wrap">
        <table class="attendance-report-table">
          <thead>
            <tr>
              <th>مجموعه</th>
              <th>فروش</th>
              <th>دریافتی</th>
              <th>مطالبات</th>
              <th>بالانس</th>
              <th>واریز</th>
              <th>برداشت</th>
              <th>جریان خالص</th>
              <th>سرویس فعال</th>
              <th>سلامت</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="10">در حال بارگذاری...</td></tr>
            <tr v-for="row in organizationRows" v-else :key="row.organizationId">
              <td><strong>{{ row.organizationName }}</strong><small class="hq-cell-sub">{{ row.organizationCode }}</small></td>
              <td>{{ money(row.salesTotalRaw ?? row.salesTotal) }}</td>
              <td>{{ money(row.paidTotalRaw ?? row.paidTotal) }}</td>
              <td>{{ money(row.receivablesRaw ?? row.receivables) }}</td>
              <td>{{ money(row.walletBalanceRaw ?? row.walletBalance) }}</td>
              <td>{{ money(row.depositsTotalRaw ?? row.depositsTotal) }}</td>
              <td>{{ money(row.withdrawalsTotalRaw ?? row.withdrawalsTotal) }}</td>
              <td>{{ money(row.netFlowRaw ?? row.netFlow) }}</td>
              <td>{{ fa(row.activeFeaturesCount) }}</td>
              <td><span :class="['status-badge', healthTone(row.health)]">{{ healthLabel(row.health) }}</span></td>
            </tr>
            <tr v-if="!loading && !organizationRows.length"><td colspan="10">داده‌ای یافت نشد.</td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-else-if="workspace === 'wallet'" class="surface-block hq-reports-card">
      <div class="section-label-row"><h3>دفتر تراکنش‌های کیف پول</h3></div>
      <div class="attendance-table-wrap">
        <table class="attendance-report-table">
          <thead>
            <tr>
              <th>مجموعه</th>
              <th>کیف</th>
              <th>نوع</th>
              <th>جهت</th>
              <th>مبلغ</th>
              <th>موجودی بعد</th>
              <th>کاربر</th>
              <th>زمان</th>
              <th>یادداشت</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in transactionRows" :key="row.id">
              <td><strong>{{ row.organizationName }}</strong></td>
              <td>{{ row.walletKey }}</td>
              <td>{{ txLabel(row.transactionType) }}</td>
              <td>{{ row.direction === 'in' ? 'ورود' : 'خروج' }}</td>
              <td>{{ money(row.amountRaw ?? row.amount) }}</td>
              <td>{{ money(row.balanceAfter) }}</td>
              <td>{{ row.actorName }}</td>
              <td>{{ row.transactedAt ? formatTehranDateTime(row.transactedAt) : '-' }}</td>
              <td>{{ row.note || '-' }}</td>
            </tr>
            <tr v-if="!transactionRows.length && !loading"><td colspan="9">تراکنشی یافت نشد.</td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-else-if="workspace === 'services'" class="surface-block hq-reports-card">
      <div class="section-label-row"><h3>تفکیک سرویس‌ها</h3></div>
      <div class="attendance-table-wrap">
        <table class="attendance-report-table">
          <thead>
            <tr>
              <th>سرویس</th>
              <th>خرید</th>
              <th>فعال</th>
              <th>فروش</th>
              <th>دریافتی</th>
              <th>مطالبات</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in featureSummary" :key="row.featureKey">
              <td><strong>{{ row.featureTitle }}</strong></td>
              <td>{{ fa(row.purchaseCount) }}</td>
              <td>{{ fa(row.activeCount) }}</td>
              <td>{{ money(row.salesRaw ?? row.sales) }}</td>
              <td>{{ money(row.paidRaw ?? row.paid) }}</td>
              <td>{{ money(row.remainingRaw ?? row.remaining) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-else class="surface-block hq-reports-card">
      <div class="section-label-row"><h3>روند روزانه</h3></div>
      <div class="hq-trend-list">
        <article v-for="day in dailyTrends" :key="day.date">
          <div class="hq-trend-head">
            <strong>{{ day.date }}</strong>
            <span>جریان {{ money(day.netFlowRaw) }}</span>
          </div>
          <div class="hq-trend-bars">
            <span class="is-in" :style="{ width: `${Math.min(100, (day.depositsRaw || 0) / Math.max(day.depositsRaw || 0, day.withdrawalsRaw || 0, 1) * 100)}%` }"></span>
            <span class="is-out" :style="{ width: `${Math.min(100, (day.withdrawalsRaw || 0) / Math.max(day.depositsRaw || 0, day.withdrawalsRaw || 0, 1) * 100)}%` }"></span>
          </div>
          <small>فروش {{ money(day.salesRaw) }} · دریافتی {{ money(day.paidRaw) }} · واریز {{ money(day.depositsRaw) }} · برداشت {{ money(day.withdrawalsRaw) }}</small>
        </article>
        <p v-if="!dailyTrends.length && !loading" class="hq-empty">داده روند در این بازه موجود نیست.</p>
      </div>
    </section>
  </section>
</template>

<style scoped>
.hq-reports-panel { display: grid; gap: 14px; min-width: 0; }
.hq-reports-hero, .hq-services-hero {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 14px;
  padding: 20px; border-radius: 16px;
  background: linear-gradient(135deg, rgba(220,239,236,.95), rgba(255,255,255,.92));
  border: 1px solid var(--line);
}
.hq-reports-hero h2 { margin: 8px 0 6px; color: var(--primary); }
.hq-reports-hero p { margin: 0; color: var(--muted); line-height: 1.7; }
.hq-reports-hero-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.hq-reports-kpis {
  display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 10px;
}
.hq-reports-kpis article, .hq-highlights article {
  padding: 12px; border-radius: 14px; background: rgba(255,255,255,.88); border: 1px solid var(--line);
}
.hq-reports-kpis span, .hq-highlights span { display: block; color: var(--muted); font-size: 11px; }
.hq-reports-kpis strong, .hq-highlights strong { display: block; margin-top: 6px; color: var(--primary); font-size: 1.1rem; }
.hq-reports-kpis small, .hq-highlights small { display: block; margin-top: 4px; color: var(--muted); font-size: 10px; }
.hq-reports-range, .hq-workspace-tabs { display: flex; flex-wrap: wrap; gap: 8px; }
.hq-range-chip, .hq-workspace-tab {
  min-height: 38px; padding: 0 14px; border-radius: 999px; border: 1px solid var(--line);
  background: rgba(255,255,255,.82); color: var(--primary); font: inherit; font-size: 12px; font-weight: 700; cursor: pointer;
  display: inline-flex; align-items: center; gap: 6px;
}
.hq-range-chip.is-active, .hq-workspace-tab.is-active {
  background: var(--button-primary-bg, #34908B); color: #fff; border-color: transparent;
}
.hq-reports-filters {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; align-items: end;
}
.hq-reports-filters .search-shell-wide { grid-column: 1 / -1; }
.hq-highlights { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.hq-reports-card { display: grid; gap: 12px; }
.hq-cell-sub { display: block; margin-top: 4px; color: var(--muted); font-size: 11px; }
.hq-trend-list { display: grid; gap: 10px; }
.hq-trend-list article {
  padding: 12px; border-radius: 14px; border: 1px solid var(--line); background: rgba(255,255,255,.82);
}
.hq-trend-head { display: flex; justify-content: space-between; gap: 10px; color: var(--primary); }
.hq-trend-bars {
  display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin: 8px 0;
}
.hq-trend-bars span { display: block; height: 8px; border-radius: 999px; min-width: 4px; }
.hq-trend-bars .is-in { background: var(--success); }
.hq-trend-bars .is-out { background: var(--danger); }
.hq-empty { margin: 0; color: var(--muted); }
@media (max-width: 1100px) {
  .hq-reports-kpis, .hq-highlights { grid-template-columns: repeat(3, minmax(0,1fr)); }
  .hq-reports-hero { flex-direction: column; }
}
@media (max-width: 760px) {
  .hq-reports-kpis, .hq-highlights { grid-template-columns: repeat(2, minmax(0,1fr)); }
}
</style>
