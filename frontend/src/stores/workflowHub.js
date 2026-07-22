import { computed, reactive } from 'vue'
import { useRouter } from 'vue-router'

import { formatAmountInput, normalizeAmountValue } from '../utils/amount'
import { AppError, appErrorFromResponse, createValidationError, hasFieldError, normalizeError } from '../utils/errors'
import { formatJalali, getTodayJalali, isoToJalali, jalaliToIso } from '../utils/jalali'
import { repairPayload } from '../utils/stitch'
import { cleanDisplayText } from '../utils/text'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const API_ORIGIN = API_BASE_URL.replace(/\/api\/v1\/?$/, '')
const TOKEN_KEY = 'workflow-hub-token'
const SUPPORT_SEEN_KEY = 'workflow-hub-support-seen'

function createCurrentUser() {
  return {
    id: null,
    slug: '',
    username: '',
    name: '',
    role: '',
    accessRole: '',
    department: '',
    avatar: '',
    email: '',
    organization: '',
    bonusAmount: '0.00',
    bonusAmountRaw: 0,
    penaltyAmount: '0.00',
    penaltyAmountRaw: 0,
    netAdjustment: '0.00',
    netAdjustmentRaw: 0,
    canManageUsers: false,
    canAccessUsers: false,
    canAccessExpenses: false,
    canAccessSettings: false,
    canViewReports: false,
    canAccessApprovals: false,
    canApproveDocuments: false,
    isManager: false,
    isHq: false,
    canUseHq: false,
    purchasedMenuAccess: [],
    menuAccess: {},
    licenseStatus: {
      isLocked: false,
      is_locked: false,
      reason: '',
      notice: '',
      amountDue: '0.00',
      amount_due: '0.00',
      trialActive: false,
      trial_active: false,
      trialEndsAt: '',
      trial_ends_at: '',
      trialRemainingSeconds: 0,
      trial_remaining_seconds: 0,
      trialHours: 24,
      trial_hours: 24,
    },
  }
}

function createRequestForm() {
  return {
    title: '',
    description: '',
    department: '',
    manager: '',
    managerAssigneeIds: [],
    employeeAssigneeIds: [],
    priority: 'medium',
    deadline: formatJalali(getTodayJalali()),
    attachments: [],
  }
}

function createExpenseForm() {
  return {
    description: '',
    amount: '0.00',
    expenseDate: formatJalali(getTodayJalali()),
    department: '',
    managerAssigneeIds: [],
    employeeAssigneeIds: [],
    invoice: null,
  }
}

function createUserForm() {
  return {
    fullName: '',
    username: '',
    password: '',
    phone: '',
    accessRole: 'employee',
    department: '',
    managerId: '',
    jobTitle: '',
    sectionAccess: {
      approvals: false,
      expenses: false,
      reports: false,
      users: false,
      settings: false,
    },
  }
}

function createDocumentForm() {
  return {
    title: '',
    description: '',
    department: '',
    assigneeIds: [],
    documentType: 'سند',
    risk: 'medium',
    file: null,
  }
}

function createSettingsState() {
  return {
    organizationName: '',
    systemId: '',
    security: {
      twoFactorRequired: true,
      recentSessionCount: 0,
      recentSessionLabel: '',
    },
    sections: [],
    organizationUsers: [],
    departments: [],
    canEdit: false,
  }
}

function createWalletState() {
  return {
    loaded: false,
    loading: false,
    submitting: false,
    error: '',
    message: '',
    organization: null,
    summary: {
      totalBalance: '0.00',
      totalBalanceRaw: 0,
      mainBalance: '0.00',
      mainBalanceRaw: 0,
      smsBalance: '0.00',
      smsBalanceRaw: 0,
      smsLowBalanceThreshold: '0.00',
      smsLowBalanceThresholdRaw: 0,
      smsIsLow: false,
      depositsTotal: '0.00',
      depositsTotalRaw: 0,
      withdrawalsTotal: '0.00',
      withdrawalsTotalRaw: 0,
      transactions: 0,
    },
    options: [],
    licenseStatus: {
      isLocked: false,
      is_locked: false,
      reason: '',
      notice: '',
      amountDue: '0.00',
      amount_due: '0.00',
      trialActive: false,
      trial_active: false,
      trialEndsAt: '',
      trial_ends_at: '',
      trialRemainingSeconds: 0,
      trial_remaining_seconds: 0,
      trialHours: 24,
      trial_hours: 24,
    },
    wallets: [],
    transactions: [],
  }
}

function createSupportState() {
  return {
    loaded: false,
    loading: false,
    detailLoading: false,
    submitting: false,
    seenVersion: 0,
    error: '',
    message: '',
    tickets: [],
    selectedTicket: null,
  }
}

function getSupportSeenStorageKey() {
  const userId = state.currentUser.id || 'guest'
  const organization = state.currentUser.organization || 'global'
  return `${SUPPORT_SEEN_KEY}:${userId}:${organization}`
}

function readSupportSeenMap() {
  try {
    return JSON.parse(localStorage.getItem(getSupportSeenStorageKey()) || '{}')
  } catch {
    return {}
  }
}

function writeSupportSeenMap(payload) {
  localStorage.setItem(getSupportSeenStorageKey(), JSON.stringify(payload))
}

const state = reactive({
  authToken: localStorage.getItem(TOKEN_KEY) || '',
  sessionReady: false,
  bootstrapLoaded: false,
  appLoading: false,
  lastError: '',
  lastErrorDetails: null,
  loginPending: false,
  mobileMenuOpen: false,
  currentUser: createCurrentUser(),
  stats: [],
  chartData: [],
  pipeline: [],
  requests: [],
  approvals: [],
  expenses: [],
  users: [],
  reports: [],
  reportSummary: null,
  reportStatus: {},
  topSubmitters: [],
  activities: [],
  insights: [],
  expenseSummary: [],
  approvalMetrics: { pending: 0, approved: 0, rejected: 0 },
  settings: createSettingsState(),
  hq: createHqState(),
  wallet: createWalletState(),
  support: createSupportState(),
  settingsCards: [],
  directories: {
    departments: [],
    managers: [],
    users: [],
  },
  requestForm: createRequestForm(),
  expenseForm: createExpenseForm(),
  userForm: createUserForm(),
  documentForm: createDocumentForm(),
  requestSubmitting: false,
  expenseSubmitting: false,
  userSubmitting: false,
  documentSubmitting: false,
  filters: {
    requests: { query: '', person: '', startDate: '', endDate: '' },
    expenses: { query: '', person: '', startDate: '', endDate: '' },
    approvals: { query: '', person: '', startDate: '', endDate: '' },
    reports: { query: '', person: '', startDate: '', endDate: '' },
    users: { query: '', person: '', startDate: '', endDate: '' },
  },
})

const modalState = reactive({
  requestDetail: false,
  expenseDetail: false,
  requestComposer: false,
  expenseComposer: false,
  approvalDetail: false,
  userComposer: false,
  documentComposer: false,
  signatureComposer: false,
})

const requestDetailState = reactive({
  loading: false,
  items: {},
})

const approvalDetailState = reactive({
  loading: false,
  item: null,
})

const expenseDetailState = reactive({
  loading: false,
  item: null,
})

const signatureState = reactive({
  loading: false,
  hasSignature: false,
  signatureData: '',
  hasStamp: false,
  stampData: '',
})

const selectedState = reactive({
  requestId: '',
  expenseId: '',
  approvalId: '',
})

function resetCurrentUser() {
  Object.assign(state.currentUser, createCurrentUser())
}

function resetRequestForm() {
  Object.assign(state.requestForm, createRequestForm())
}

function resetExpenseForm() {
  Object.assign(state.expenseForm, createExpenseForm())
}

function resetUserForm() {
  Object.assign(state.userForm, createUserForm())
}

function resetDocumentForm() {
  Object.assign(state.documentForm, createDocumentForm())
}

function resetSettingsState() {
  Object.assign(state.settings, createSettingsState())
}

function resetHqState() {
  Object.assign(state.hq, createHqState())
}

function resetWalletState() {
  Object.assign(state.wallet, createWalletState())
}

function resetSupportState() {
  Object.assign(state.support, createSupportState())
}

function replaceItems(target, items) {
  target.splice(0, target.length, ...(items || []))
}

function clearLastError() {
  state.lastError = ''
  state.lastErrorDetails = null
}

function setLastError(error, fallback = 'خطا در انجام عملیات') {
  const normalized = normalizeError(error, fallback)
  state.lastError = normalized.message
  state.lastErrorDetails = normalized
  return normalized
}

function fieldHasError(field) {
  return hasFieldError(state.lastErrorDetails, field)
}

function resolveAssetUrl(rawUrl) {
  if (!rawUrl) return ''
  if (/^https?:\/\//i.test(rawUrl) || rawUrl.startsWith('data:')) return rawUrl
  if (rawUrl.startsWith('/')) return `${API_ORIGIN}${rawUrl}`
  return `${API_ORIGIN}/${rawUrl}`
}

function formatNumber(value) {
  const normalized = normalizeAmountValue(value)
  const number = Number(normalized)
  if (!Number.isFinite(number)) return String(value || '')
  return new Intl.NumberFormat('fa-IR', { maximumFractionDigits: 2 }).format(number)
}

function formatMoneyInputValue(value) {
  return formatAmountInput(value)
}

function normalizeDisplayDate(value) {
  if (!value) return ''
  const raw = String(value).slice(0, 10)
  return /^\d{4}-\d{2}-\d{2}$/.test(raw) ? isoToJalali(raw) : value
}

function normalizeUser(item = {}) {
  return {
    ...item,
    name: cleanDisplayText(item?.name),
    username: cleanDisplayText(item?.username),
    role: cleanDisplayText(item?.role),
    department: cleanDisplayText(item?.department),
    manager: cleanDisplayText(item?.manager),
    jobTitle: cleanDisplayText(item?.jobTitle),
    phone: cleanDisplayText(item?.phone),
    status: cleanDisplayText(item?.status),
    bonusAmount: item?.bonusAmount || '0.00',
    bonusAmountRaw: Number(item?.bonusAmountRaw || 0),
    penaltyAmount: item?.penaltyAmount || '0.00',
    penaltyAmountRaw: Number(item?.penaltyAmountRaw || 0),
    netAdjustment: item?.netAdjustment || '0.00',
    netAdjustmentRaw: Number(item?.netAdjustmentRaw || 0),
    financeUpdatedAt: item?.financeUpdatedAt || '',
    financeUpdatedAtIso: item?.financeUpdatedAtIso || '',
  }
}

function upsertById(target, item) {
  if (!item?.id || !Array.isArray(target)) return
  const index = target.findIndex((entry) => Number(entry?.id) === Number(item.id))
  if (index >= 0) target[index] = { ...target[index], ...item }
  else target.unshift(item)
}

function removeById(target, itemId) {
  if (!itemId || !Array.isArray(target)) return
  const index = target.findIndex((entry) => Number(entry?.id) === Number(itemId))
  if (index >= 0) target.splice(index, 1)
}

function syncUserAcrossState(userPayload, options = {}) {
  const { remove = false } = options
  const userId = Number(userPayload?.id || options.userId)
  if (!userId) return

  if (remove) {
    removeById(state.users, userId)
    removeById(state.settings.organizationUsers || [], userId)
    removeById(state.directories.users || [], userId)
    removeById(state.directories.managers || [], userId)
    if (Number(state.currentUser.id) === userId) {
      Object.assign(state.currentUser, createCurrentUser())
    }
    return
  }

  const normalizedUser = normalizeUser(userPayload)
  upsertById(state.users, normalizedUser)
  upsertById(state.settings.organizationUsers || [], normalizedUser)
  upsertById(state.directories.users || [], normalizedUser)

  const managerEntry = {
    id: Number(normalizedUser.id),
    slug: normalizedUser.username,
    name: normalizedUser.name,
    role: normalizedUser.role,
    accessRole: normalizedUser.accessRole,
  }
  const isManagerRole = ['admin', 'executive_manager', 'manager'].includes(normalizedUser.accessRole)
  if (isManagerRole) upsertById(state.directories.managers || [], managerEntry)
  else removeById(state.directories.managers || [], normalizedUser.id)

  if (Number(state.currentUser.id) === Number(normalizedUser.id)) {
    Object.assign(state.currentUser, {
      username: normalizedUser.username,
      name: normalizedUser.name,
      accessRole: normalizedUser.accessRole,
      role: normalizedUser.role,
      department: normalizedUser.department,
      phone: normalizedUser.phone,
      bonusAmount: normalizedUser.bonusAmount,
      bonusAmountRaw: normalizedUser.bonusAmountRaw,
      penaltyAmount: normalizedUser.penaltyAmount,
      penaltyAmountRaw: normalizedUser.penaltyAmountRaw,
      netAdjustment: normalizedUser.netAdjustment,
      netAdjustmentRaw: normalizedUser.netAdjustmentRaw,
    })
  }
}

function normalizeRequest(item) {
  return {
    ...item,
    title: cleanDisplayText(item?.title),
    description: cleanDisplayText(item?.description),
    owner: cleanDisplayText(item?.owner),
    manager: cleanDisplayText(item?.manager),
    department: cleanDisplayText(item?.department),
    status: cleanDisplayText(item?.status),
    deadline: normalizeDisplayDate(item?.deadline),
    createdAt: normalizeDisplayDate(item?.createdAt),
    managerAssignees: (item?.managerAssignees || []).map((entry) => cleanDisplayText(entry)),
    employeeAssignees: (item?.employeeAssignees || []).map((entry) => cleanDisplayText(entry)),
    attachments: (item?.attachments || []).map((attachment) => ({
      ...attachment,
      originalName: cleanDisplayText(attachment?.originalName),
      fileUrl: resolveAssetUrl(attachment.fileUrl),
    })),
  }
}

function normalizeExpense(item) {
  return {
    ...item,
    title: cleanDisplayText(item?.title),
    description: cleanDisplayText(item?.description),
    owner: cleanDisplayText(item?.owner),
    category: cleanDisplayText(item?.category),
    department: cleanDisplayText(item?.department),
    status: cleanDisplayText(item?.status),
    amount: formatNumber(item?.amountRaw ?? item?.amount),
    submittedAt: normalizeDisplayDate(item?.submittedAt),
    invoiceUrl: resolveAssetUrl(item?.invoiceUrl),
  }
}

function normalizeApproval(item) {
  const hqDownloadQuery = state.currentUser.isHq && state.hq.selectedOrganizationId && item?.downloadUrl
    ? `${item.downloadUrl.includes('?') ? '&' : '?'}organizationId=${encodeURIComponent(state.hq.selectedOrganizationId)}`
    : ''
  return {
    ...item,
    title: cleanDisplayText(item?.title),
    owner: cleanDisplayText(item?.owner),
    type: cleanDisplayText(item?.type),
    status: cleanDisplayText(item?.status),
    department: cleanDisplayText(item?.department),
    risk: cleanDisplayText(item?.risk),
    summary: cleanDisplayText(item?.summary),
    decisionNote: cleanDisplayText(item?.decisionNote),
    assignees: (item?.assignees || []).map((entry) => cleanDisplayText(entry)),
    uploadedAt: normalizeDisplayDate(item?.uploadedAt),
    previewUrl: resolveAssetUrl(item?.previewUrl),
    downloadUrl: resolveAssetUrl(`${item?.downloadUrl || ''}${hqDownloadQuery}`),
  }
}

function createHqState() {
  return {
    loaded: false,
    loading: false,
    saving: false,
    activeTable: 'organizations',
    selectedOrganizationId: '',
    selectedOrganization: null,
    selectedType: '',
    selectedItem: null,
    query: '',
    summary: {},
    organizations: [],
    users: [],
    requests: [],
    payments: [],
    documents: [],
    tickets: [],
    audits: [],
    segments: { roles: [], payments: [], requests: [], documents: [], tickets: [] },
    directories: {
      organizations: [],
      departments: [],
      users: [],
      roles: [],
      requestStatuses: [],
      expenseStatuses: [],
      documentStatuses: [],
    },
  }
}

function normalizeReport(item) {
  return {
    ...item,
    title: cleanDisplayText(item?.title),
    description: cleanDisplayText(item?.description),
    owner: cleanDisplayText(item?.owner),
    downloadUrl: resolveAssetUrl(item?.downloadUrl),
  }
}

function parseDownloadFilename(disposition = '') {
  const utfMatch = disposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utfMatch?.[1]) {
    try {
      return decodeURIComponent(utfMatch[1])
    } catch {
      // ignore malformed header encoding
    }
  }

  const asciiMatch = disposition.match(/filename="([^"]+)"|filename=([^;]+)/i)
  return asciiMatch?.[1] || asciiMatch?.[2] || ''
}

function fallbackFilenameFromUrl(rawUrl = '', fallback = 'download') {
  try {
    const url = new URL(rawUrl, API_ORIGIN)
    const fileName = decodeURIComponent(url.pathname.split('/').filter(Boolean).pop() || '')
    return fileName || fallback
  } catch {
    return fallback
  }
}

async function authorizedFetchUrl(rawUrl, options = {}) {
  const requestUrl = /^https?:\/\//i.test(rawUrl) ? rawUrl : resolveAssetUrl(rawUrl)
  const response = await fetch(requestUrl, {
    ...options,
    headers: {
      ...(options.headers || {}),
      ...(state.authToken ? { Authorization: `Bearer ${state.authToken}` } : {}),
    },
  })

  if (response.status === 401) {
    clearSessionState()
    throw new AppError({
      status: 401,
      title: 'نشست منقضی شده است',
      message: 'برای ادامه کار دوباره وارد سامانه شوید.',
      suggestion: 'صفحه ورود را باز کنید و دوباره وارد حساب شوید.',
    })
  }

  if (!response.ok) {
    let payload = null
    try {
      payload = repairPayload(await response.json())
    } catch {
      // ignore parse failure
    }
    throw appErrorFromResponse(payload || {}, response.status)
  }

  return response
}

async function downloadProtectedFile(rawUrl, fallbackName = 'download') {
  if (!rawUrl) return
  const response = await authorizedFetchUrl(rawUrl)
  const blob = await response.blob()
  const disposition = response.headers.get('Content-Disposition') || ''
  const fileName = parseDownloadFilename(disposition) || fallbackFilenameFromUrl(rawUrl, fallbackName)
  const objectUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = fileName
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 2000)
}

async function openProtectedFile(rawUrl, fallbackName = 'preview') {
  if (!rawUrl) return
  const response = await authorizedFetchUrl(rawUrl)
  const blob = await response.blob()
  const objectUrl = URL.createObjectURL(blob)
  const popup = window.open(objectUrl, '_blank', 'noopener,noreferrer')

  if (!popup) {
    const link = document.createElement('a')
    link.href = objectUrl
    link.target = '_blank'
    link.rel = 'noreferrer'
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()
    link.remove()
  }

  const revokeDelay = /\.(pdf|png|jpe?g|webp|gif|bmp)$/i.test(fallbackFilenameFromUrl(rawUrl, fallbackName)) ? 60000 : 15000
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), revokeDelay)
}

async function createProtectedObjectUrl(rawUrl) {
  if (!rawUrl) return ''
  const response = await authorizedFetchUrl(rawUrl)
  const blob = await response.blob()
  return URL.createObjectURL(blob)
}

function clearSessionState() {
  state.authToken = ''
  state.bootstrapLoaded = false
  state.sessionReady = true
  clearLastError()
  resetCurrentUser()
  replaceItems(state.stats, [])
  replaceItems(state.chartData, [])
  replaceItems(state.pipeline, [])
  replaceItems(state.requests, [])
  replaceItems(state.expenses, [])
  replaceItems(state.approvals, [])
  replaceItems(state.users, [])
  replaceItems(state.reports, [])
  replaceItems(state.activities, [])
  replaceItems(state.expenseSummary, [])
  replaceItems(state.settingsCards, [])
  resetSettingsState()
  resetHqState()
  resetWalletState()
  resetSupportState()
  state.directories.departments = []
  state.directories.managers = []
  state.directories.users = []
  state.reportSummary = null
  state.reportStatus = {}
  state.topSubmitters = []
  signatureState.hasSignature = false
  signatureState.signatureData = ''
  signatureState.hasStamp = false
  signatureState.stampData = ''
  approvalDetailState.item = null
  expenseDetailState.item = null
  selectedState.requestId = ''
  selectedState.expenseId = ''
  selectedState.approvalId = ''
  localStorage.removeItem(TOKEN_KEY)
}

function inDateRange(rawValue, startDate, endDate) {
  if (!startDate && !endDate) return true
  const value = String(rawValue || '')
  if (!value) return false
  if (startDate && value < startDate) return false
  if (endDate && value > endDate) return false
  return true
}

function matchesQuery(item, fields, query) {
  if (!query) return true
  return fields.some((field) => String(item[field] || '').toLowerCase().includes(query))
}

function matchesPerson(item, fields, person) {
  if (!person) return true
  return fields.some((field) => String(item[field] || '') === person)
}

const selectedRequest = computed(
  () => state.requests.find((item) => item.id === selectedState.requestId) ?? state.requests[0] ?? null,
)

const selectedApproval = computed(
  () => approvalDetailState.item ?? state.approvals.find((item) => item.id === selectedState.approvalId) ?? null,
)

const selectedExpense = computed(
  () => expenseDetailState.item ?? state.expenses.find((item) => item.id === selectedState.expenseId) ?? null,
)

const selectedRequestTimeline = computed(() => requestDetailState.items[selectedState.requestId]?.timeline ?? [])

const canApproveSelectedRequest = computed(() => Boolean(selectedRequest.value?.canApprove))

const canApproveSelectedExpense = computed(() => Boolean(selectedExpense.value?.canApprove))

const canManageUsers = computed(() => state.currentUser.canManageUsers)
const canAccessUsers = computed(() => state.currentUser.canAccessUsers || canManageUsers.value)
const canViewReports = computed(() => state.currentUser.canViewReports)
const canAccessApprovals = computed(() => state.currentUser.canAccessApprovals || state.currentUser.canApproveDocuments)
const canApproveDocuments = computed(() => state.currentUser.canApproveDocuments)
const isLicenseLocked = computed(() => Boolean(state.currentUser.licenseStatus?.isLocked || state.currentUser.licenseStatus?.is_locked))
const canAccessCloud = computed(() => state.currentUser.isHq || state.currentUser.menuAccess?.cloud_storage === true)

const visibleNavItems = computed(() => {
  const items = [
    { to: '/dashboard', label: 'داشبورد', icon: 'dashboard' },
    { to: '/requests', label: 'درخواست‌ها', icon: 'assignment' },
    { to: '/approvals', label: 'تاییدیه‌ها', icon: 'fact_check' },
  ]
  if (canViewReports.value) items.push({ to: '/reports', label: 'گزارشات', icon: 'monitoring' })
  if (canAccessUsers.value) items.push({ to: '/users', label: 'کاربران', icon: 'group' })
  if (canAccessCloud.value) items.push({ to: '/cloud', label: 'فضای ابری', icon: 'cloud' })

  if (state.currentUser.canAccessSettings || canManageUsers.value) {
    items.push({ to: '/settings', label: 'تنظیمات', icon: 'settings' })
  }
  return items
})

const filteredRequests = computed(() => {
  const filter = state.filters.requests
  const query = filter.query.trim().toLowerCase()
  return state.requests.filter((item) =>
    matchesQuery(item, ['title', 'owner', 'manager', 'department', 'status', 'id', 'description'], query) &&
    matchesPerson(item, ['owner', 'manager'], filter.person) &&
    inDateRange(item.deadlineIso || item.createdAtIso, filter.startDate, filter.endDate),
  )
})

const filteredExpenses = computed(() => {
  const filter = state.filters.expenses
  const query = filter.query.trim().toLowerCase()
  return state.expenses.filter((item) =>
    matchesQuery(item, ['title', 'description', 'category', 'owner', 'status', 'id', 'department'], query) &&
    matchesPerson(item, ['owner'], filter.person) &&
    inDateRange(item.createdAtIso, filter.startDate, filter.endDate),
  )
})

const filteredApprovals = computed(() => {
  const filter = state.filters.approvals
  const query = filter.query.trim().toLowerCase()
  return state.approvals.filter((item) =>
    matchesQuery(item, ['title', 'type', 'owner', 'department', 'status', 'id', 'summary'], query) &&
    matchesPerson(item, ['owner'], filter.person) &&
    inDateRange(item.uploadedAtIso, filter.startDate, filter.endDate),
  )
})

const approvalInbox = computed(() => filteredApprovals.value.filter((item) => item.bucket === 'pending'))
const approvalHistory = computed(() => filteredApprovals.value.filter((item) => item.bucket !== 'pending'))

const filteredReports = computed(() => {
  const filter = state.filters.reports
  const query = filter.query.trim().toLowerCase()
  return state.reports.filter((item) =>
    matchesQuery(item, ['title', 'description', 'export', 'owner'], query) &&
    matchesPerson(item, ['owner'], filter.person) &&
    inDateRange(item.generatedAtIso, filter.startDate, filter.endDate),
  )
})

const filteredUsers = computed(() => {
  const filter = state.filters.users
  const query = filter.query.trim().toLowerCase()
  return state.users.filter((item) =>
    matchesQuery(item, ['name', 'username', 'role', 'department', 'manager', 'status'], query) &&
    matchesPerson(item, ['name', 'manager'], filter.person) &&
    inDateRange(item.joinedAtIso, filter.startDate, filter.endDate),
  )
})

const requestPeople = computed(() => [...new Set(state.requests.flatMap((item) => [item.owner, item.manager, ...(item.managerAssignees || [])]).filter(Boolean))])
const expensePeople = computed(() => [...new Set(state.expenses.map((item) => item.owner).filter(Boolean))])
const approvalPeople = computed(() => [...new Set(state.approvals.map((item) => item.owner).filter(Boolean))])
const reportPeople = computed(() => [...new Set(state.reports.map((item) => item.owner).filter(Boolean))])
const userPeople = computed(() => [...new Set(state.users.flatMap((item) => [item.name, item.manager]).filter(Boolean))])

function priorityLabel(value) {
  return {
    low: 'پایین',
    medium: 'متوسط',
    high: 'بالا',
    critical: 'بحرانی',
  }[value] || 'متوسط'
}

function departmentLabel(value) {
  return state.directories.departments.find((item) => item.code === value)?.name || 'بدون واحد'
}

function managerLabel(value) {
  return state.directories.managers.find((item) => item.slug === value)?.name || 'تعیین نشده'
}

function availableManagerDirectory(excludeId = null) {
  const seen = new Set()
  return [...state.directories.managers, ...state.users
    .filter((item) => ['admin', 'executive_manager', 'manager'].includes(item.accessRole))
    .map((item) => ({ id: Number(item.id), slug: item.username, name: item.name, role: item.role }))]
    .filter((item) => {
      const id = Number(item?.id)
      if (!id || (excludeId && id === Number(excludeId)) || seen.has(id)) return false
      seen.add(id)
      return true
    })
}

function availableRecipientUsers() {
  return Array.isArray(state.directories.users) && state.directories.users.length
    ? state.directories.users
    : state.users
}

const requestManagerAssigneeOptions = computed(() => {
  if (!state.requestForm.manager) return []
  return availableManagerDirectory().filter((item) => item.slug !== state.requestForm.manager)
})

function requestManagerAssigneeNames(ids = state.requestForm.managerAssigneeIds) {
  const normalizedIds = (ids || []).map((item) => Number(item))
  const names = availableManagerDirectory()
    .filter((item) => normalizedIds.includes(item.id))
    .map((item) => item.name)
  return names.length ? names.join('، ') : 'تعیین نشده'
}

function requestEmployeeAssigneeNames(ids = state.requestForm.employeeAssigneeIds) {
  const normalizedIds = (ids || []).map((item) => Number(item))
  const names = availableRecipientUsers()
    .filter((item) => item.accessRole === 'employee' && normalizedIds.includes(Number(item.id)))
    .map((item) => item.name)
  return names.length ? names.join('، ') : 'تعیین نشده'
}

function setRequestManager(value) {
  state.requestForm.manager = value
  if (!value) {
    state.requestForm.managerAssigneeIds = []
    return
  }

  const allowedIds = requestManagerAssigneeOptions.value.map((item) => item.id)
  state.requestForm.managerAssigneeIds = state.requestForm.managerAssigneeIds
    .map((item) => Number(item))
    .filter((item) => allowedIds.includes(item))
}

async function authorizedFetch(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.headers || {}),
      ...(state.authToken ? { Authorization: `Bearer ${state.authToken}` } : {}),
    },
  })

  if (response.status === 401) {
    clearSessionState()
    throw new AppError({
      status: 401,
      title: 'نشست منقضی شده است',
      message: 'برای ادامه کار دوباره وارد سامانه شوید.',
      suggestion: 'صفحه ورود را باز کنید و دوباره وارد حساب شوید.',
    })
  }

  if (!response.ok) {
    let payload = null
    try {
      payload = repairPayload(await response.json())
    } catch {
      // ignore parse failure
    }
    throw appErrorFromResponse(payload || {}, response.status)
  }

  return response
}

function hydrateBootstrap(payload) {
  if (!payload) return

  Object.assign(state.currentUser, createCurrentUser(), payload.currentUser || {})
  replaceItems(state.stats, payload.stats)
  replaceItems(state.chartData, payload.chartData)
  replaceItems(state.pipeline, payload.pipeline)
  replaceItems(state.requests, (payload.requests || []).map(normalizeRequest))
  replaceItems(state.expenses, (payload.expenses || []).map(normalizeExpense))
  replaceItems(state.approvals, (payload.approvals || []).map(normalizeApproval))
  replaceItems(state.users, (payload.users || []).map(normalizeUser))
  replaceItems(state.reports, (payload.reports || []).map(normalizeReport))
  replaceItems(state.activities, payload.activities)
  replaceItems(state.insights, payload.insights)
  replaceItems(state.expenseSummary, payload.expenseSummary)
  replaceItems(state.settingsCards, payload.settingsCards)
  if (payload.settings) Object.assign(state.settings, createSettingsState(), payload.settings)
  if (Array.isArray(payload.hqOrganizations)) {
    replaceItems(state.hq.directories.organizations, payload.hqOrganizations)
  }
  state.hq.selectedOrganization = payload.selectedOrganization || null
  Object.assign(state.approvalMetrics, payload.approvalMetrics || {})
  state.directories.departments = payload.directories?.departments || []
  state.directories.managers = payload.directories?.managers || []
  state.directories.users = (payload.directories?.users || []).map(normalizeUser)
  if (payload.wallet?.summary) {
    Object.assign(state.wallet.summary, payload.wallet.summary)
  }

  selectedState.requestId = state.requests[0]?.id || ''
  if (!expenseDetailState.item) selectedState.expenseId = state.expenses[0]?.id || ''
  if (!approvalDetailState.item) selectedState.approvalId = state.approvals[0]?.id || ''
}

function hydrateHq(payload) {
  if (!payload) return
  Object.assign(state.hq.summary, payload.summary || {})
  replaceItems(state.hq.organizations, payload.organizations)
  replaceItems(state.hq.users, payload.users)
  replaceItems(state.hq.requests, payload.requests)
  replaceItems(state.hq.payments, payload.payments)
  replaceItems(state.hq.documents, payload.documents)
  replaceItems(state.hq.tickets, payload.tickets)
  replaceItems(state.hq.audits, payload.audits)
  state.hq.segments = payload.segments || createHqState().segments
  state.hq.directories = payload.directories || createHqState().directories
  state.hq.loaded = true
}

function hydrateWallet(payload) {
  if (!payload) return
  state.wallet.organization = payload.organization || null
  Object.assign(state.wallet.summary, createWalletState().summary, payload.summary || {})
  Object.assign(state.wallet.licenseStatus, createWalletState().licenseStatus, payload.licenseStatus || payload.license_status || {})
  replaceItems(state.wallet.options, payload.options || [])
  replaceItems(state.wallet.wallets, payload.wallets || [])
  replaceItems(state.wallet.transactions, payload.transactions || [])
  state.wallet.loaded = true
}

function hydrateSupportTickets(payload) {
  replaceItems(state.support.tickets, Array.isArray(payload) ? payload : [])
  state.support.loaded = true
}

function hydrateSupportTicket(payload) {
  state.support.selectedTicket = payload || null
  if (!payload?.id) return
  const index = state.support.tickets.findIndex((item) => Number(item.id) === Number(payload.id))
  if (index >= 0) state.support.tickets[index] = { ...state.support.tickets[index], ...payload }
  else state.support.tickets.unshift(payload)
}

const supportUnreadCount = computed(() => {
  if (state.currentUser.isHq) {
    const tickets = (state.support.tickets?.length ? state.support.tickets : state.hq.tickets) || []
    const actionableTickets = tickets.filter((ticket) => ['open', 'pending'].includes(ticket.status)).length
    if (actionableTickets) return actionableTickets
    return Number(state.hq.summary.openTickets || 0) + Number(state.hq.summary.pendingTickets || 0)
  }
  void state.support.seenVersion
  const seenMap = readSupportSeenMap()
  return (state.support.tickets || []).filter((ticket) => {
    if (ticket.status !== 'answered') return false
    const seenAt = seenMap[String(ticket.id)]
    return seenAt !== ticket.updatedAt
  }).length
})

const requestInboxCount = computed(() => state.requests.filter((item) => item.canApprove).length)
const expenseInboxCount = computed(() => state.expenses.filter((item) => item.canApprove).length)
const approvalInboxCount = computed(() => state.approvals.filter((item) => item.canApprove).length)

function markSupportTicketsSeen(ticketIds = []) {
  if (state.currentUser.isHq) return
  const seenMap = readSupportSeenMap()
  const ids = ticketIds.length ? ticketIds.map((item) => String(item)) : (state.support.tickets || []).map((item) => String(item.id))
  ids.forEach((id) => {
    const ticket = (state.support.tickets || []).find((item) => String(item.id) === id)
    if (ticket?.status === 'answered' && ticket.updatedAt) {
      seenMap[id] = ticket.updatedAt
    }
  })
  writeSupportSeenMap(seenMap)
  state.support.seenVersion += 1
}

function scopedApiPath(path) {
  if (!state.currentUser.isHq || !state.hq.selectedOrganizationId) return path
  const separator = path.includes('?') ? '&' : '?'
  return `${path}${separator}organizationId=${encodeURIComponent(state.hq.selectedOrganizationId)}`
}

async function loadBootstrapData(force = false) {
  if (!state.authToken) {
    state.sessionReady = true
    return
  }
  if (state.bootstrapLoaded && !force) return

  state.appLoading = true
  clearLastError()
  try {
    const organizationQuery = state.currentUser.isHq && state.hq.selectedOrganizationId
      ? `?organizationId=${encodeURIComponent(state.hq.selectedOrganizationId)}`
      : ''
    const response = await authorizedFetch(`/bootstrap${organizationQuery}`)
    const payload = repairPayload(await response.json())
    hydrateBootstrap(payload)
    state.bootstrapLoaded = true
  } catch (error) {
    setLastError(error, 'خطا در بارگذاری')
    if (error.status === 401) throw error
  } finally {
    state.appLoading = false
    state.sessionReady = true
  }
}

async function loadReports(force = false) {
  if (!state.authToken || !canViewReports.value) return
  if (state.currentUser.isHq) {
    if (!state.hq.selectedOrganizationId) {
      state.reportSummary = null
      return
    }
    state.reportSummary = {
      users: state.users.length,
      requests: state.requests.length,
      expenses: state.expenses.length,
      approvals: state.approvals.length,
      expenseTotal: state.expenseSummary[2]?.value || '0',
    }
    return
  }
  if (state.reportSummary && !force) return
  const response = await authorizedFetch('/reports')
  const payload = repairPayload(await response.json())
  state.reportSummary = payload.summary
  state.reportStatus = payload.requestStatus
  state.topSubmitters = payload.topSubmitters
  replaceItems(state.reports, (payload.reports || []).map(normalizeReport))
  replaceItems(state.requests, (payload.requests || state.requests || []).map(normalizeRequest))
  replaceItems(state.expenses, (payload.expenses || state.expenses || []).map(normalizeExpense))
  replaceItems(state.approvals, (payload.approvals || state.approvals || []).map(normalizeApproval))
  replaceItems(state.users, (payload.users || state.users || []).map(normalizeUser))
}

async function loadSettings(force = false) {
  if (!state.authToken) return
  if (state.currentUser.isHq && !state.hq.selectedOrganizationId) {
    resetSettingsState()
    return
  }
  if (state.settings.systemId && !force) return
  const organizationQuery = state.currentUser.isHq && state.hq.selectedOrganizationId
    ? `?organizationId=${encodeURIComponent(state.hq.selectedOrganizationId)}`
    : ''
  const response = await authorizedFetch(`/settings/profile${organizationQuery}`)
  const payload = repairPayload(await response.json())
  Object.assign(state.settings, createSettingsState(), payload)
  replaceItems(state.settingsCards, payload.sections || [])
  state.settings.organizationUsers = (payload.organizationUsers || []).map(normalizeUser)
  state.settings.departments = payload.departments || []
  state.directories.departments = payload.departments || state.directories.departments
  state.currentUser.organization = payload.organizationName || state.currentUser.organization
}

async function loadWalletDashboard(force = false) {
  if (!state.authToken) return
  if (!state.currentUser.isManager && !state.currentUser.canUseHq) {
    resetWalletState()
    return
  }
  if (state.currentUser.isHq && !state.hq.selectedOrganizationId) {
    resetWalletState()
    return
  }
  if (state.wallet.loaded && !force) return

  state.wallet.loading = true
  state.wallet.error = ''
  try {
    const response = await authorizedFetch(scopedApiPath('/wallet'))
    hydrateWallet(repairPayload(await response.json()))
  } catch (error) {
    state.wallet.error = error.message || 'Wallet load failed.'
    throw error
  } finally {
    state.wallet.loading = false
  }
}

async function loadWalletOptions(force = false) {
  if (!state.authToken) return
  if (state.wallet.options.length && !force) return
  state.wallet.loading = true
  state.wallet.error = ''
  try {
    const response = await authorizedFetch(scopedApiPath('/wallet/options'))
    const payload = repairPayload(await response.json())
    Object.assign(state.wallet.licenseStatus, createWalletState().licenseStatus, payload.licenseStatus || payload.license_status || {})
    replaceItems(state.wallet.options, payload.options || [])
  } catch (error) {
    state.wallet.error = error.message || 'Wallet options load failed.'
    throw error
  } finally {
    state.wallet.loading = false
  }
}

async function loadSupportTickets(force = false) {
  if (!state.authToken) return
  if (state.support.loaded && !force) return
  state.support.loading = true
  state.support.error = ''
  try {
    if (state.currentUser.isHq && !state.hq.selectedOrganizationId) {
      const response = await authorizedFetch('/hq')
      const payload = repairPayload(await response.json())
      hydrateHq(payload)
      hydrateSupportTickets(payload.tickets || [])
    } else {
      const response = await authorizedFetch(scopedApiPath('/support/tickets'))
      hydrateSupportTickets(repairPayload(await response.json()))
    }
  } catch (error) {
    state.support.error = error.message || 'Support load failed.'
    throw error
  } finally {
    state.support.loading = false
  }
}

async function loadSupportTicketDetail(ticketId) {
  if (!ticketId) return
  state.support.detailLoading = true
  state.support.error = ''
  try {
    const response = await authorizedFetch(scopedApiPath(`/support/tickets/${ticketId}`))
    hydrateSupportTicket(repairPayload(await response.json()))
  } catch (error) {
    state.support.error = error.message || 'Support detail failed.'
    throw error
  } finally {
    state.support.detailLoading = false
  }
}

async function createSupportTicket(payload) {
  state.support.submitting = true
  state.support.error = ''
  state.support.message = ''
  try {
    const formData = new FormData()
    formData.append('subject', payload.subject || '')
    formData.append('message', payload.message || '')
    formData.append('category', payload.category || 'technical')
    formData.append('priority', payload.priority || 'medium')
    ;(payload.attachments || []).forEach((file) => formData.append('attachments', file))
    const response = await authorizedFetch(scopedApiPath('/support/tickets'), { method: 'POST', body: formData })
    hydrateSupportTicket(repairPayload(await response.json()))
    await loadSupportTickets(true)
    state.support.message = 'تیکت ثبت شد.'
  } catch (error) {
    state.support.error = error.message || 'Support submit failed.'
    throw error
  } finally {
    state.support.submitting = false
  }
}

async function submitSupportReply(ticketId, payload) {
  state.support.submitting = true
  state.support.error = ''
  try {
    const response = await authorizedFetch(scopedApiPath(`/support/tickets/${ticketId}/messages`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    hydrateSupportTicket(repairPayload(await response.json()))
    await loadSupportTickets(true)
  } catch (error) {
    state.support.error = error.message || 'Support reply failed.'
    throw error
  } finally {
    state.support.submitting = false
  }
}

async function submitSupportFeedback(ticketId, payload) {
  state.support.submitting = true
  state.support.error = ''
  try {
    const response = await authorizedFetch(scopedApiPath(`/support/tickets/${ticketId}/feedback`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    hydrateSupportTicket(repairPayload(await response.json()))
    await loadSupportTickets(true)
  } catch (error) {
    state.support.error = error.message || 'Support feedback failed.'
    throw error
  } finally {
    state.support.submitting = false
  }
}

async function submitSupportWalletDeposit(ticketId, payload) {
  state.support.submitting = true
  state.support.error = ''
  try {
    const requestPayload = { ...payload, amount: normalizeAmountValue(payload?.amount) }
    const response = await authorizedFetch(`/support/tickets/${ticketId}/wallet-deposit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestPayload),
    })
    hydrateSupportTicket(repairPayload(await response.json()))
    await loadSupportTickets(true)
    await loadWalletDashboard(true)
  } catch (error) {
    state.support.error = error.message || 'Support wallet deposit failed.'
    throw error
  } finally {
    state.support.submitting = false
  }
}

async function submitWalletTransaction(payload) {
  if (!payload) return
  state.wallet.submitting = true
  state.wallet.error = ''
  state.wallet.message = ''
  try {
    const requestPayload = { ...payload, amount: normalizeAmountValue(payload.amount) }
    const response = await authorizedFetch(scopedApiPath('/wallet/transactions'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestPayload),
    })
    hydrateWallet(repairPayload(await response.json()))
    state.wallet.message = payload.direction === 'out' || payload.type === 'withdraw'
      ? 'برداشت ثبت شد.'
      : 'شارژ ثبت شد.'
  } catch (error) {
    const normalized = setLastError(error, 'ثبت تراکنش کیف پول ناموفق بود.')
    state.wallet.error = normalized.message
    throw error
  } finally {
    state.wallet.submitting = false
  }
}

async function submitFeaturePurchase(payload) {
  if (!payload) return false
  state.wallet.submitting = true
  state.wallet.error = ''
  state.wallet.message = ''
  try {
    const response = await authorizedFetch(scopedApiPath('/wallet/purchases'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    const responsePayload = repairPayload(await response.json())
    if (responsePayload.wallets || responsePayload.summary) {
      hydrateWallet(responsePayload)
      state.wallet.message = 'خرید با موفقیت از کیف پول انجام شد.'
    }
    else {
      Object.assign(state.wallet.licenseStatus, createWalletState().licenseStatus, responsePayload.licenseStatus || responsePayload.license_status || {})
      replaceItems(state.wallet.options, responsePayload.options || [])
      state.wallet.message = responsePayload.message || 'خرید ثبت شد.'
    }
    await loadBootstrapData(true)
    return true
  } catch (error) {
    const normalized = setLastError(error, 'خرید قابلیت ناموفق بود.')
    state.wallet.error = normalized.message
    return false
  } finally {
    state.wallet.submitting = false
  }
}

async function loadHqPanel(force = false) {
  if (!state.authToken || !state.currentUser.canUseHq) return
  if (state.hq.loaded && !force) return
  state.hq.loading = true
  state.lastError = ''
  try {
    const response = await authorizedFetch('/hq')
    hydrateHq(repairPayload(await response.json()))
  } catch (error) {
    state.lastError = error.message || 'HQ load failed.'
    throw error
  } finally {
    state.hq.loading = false
  }
}

async function selectHqOrganization(organizationId) {
  state.hq.selectedOrganizationId = organizationId ? String(organizationId) : ''
  state.bootstrapLoaded = false
  state.reportSummary = null
  resetSettingsState()
  resetWalletState()
  resetSupportState()
  await loadBootstrapData(true)
}

async function saveHqEntity(type, id, payload) {
  const endpoints = {
    organization: `/hq/organizations/${id}`,
    user: `/hq/users/${id}`,
    request: `/hq/requests/${id}`,
    payment: `/hq/payments/${id}`,
    document: `/hq/documents/${id}`,
  }
  if (!endpoints[type]) return
  state.hq.saving = true
  state.lastError = ''
  try {
    const requestPayload = type === 'payment' && 'amount' in payload
      ? { ...payload, amount: normalizeAmountValue(payload.amount) }
      : payload
    const response = await authorizedFetch(endpoints[type], {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestPayload),
    })
    hydrateHq(repairPayload(await response.json()))
  } catch (error) {
    state.lastError = error.message || 'HQ save failed.'
    throw error
  } finally {
    state.hq.saving = false
  }
}

async function createHqOrganization(payload) {
  if (!state.authToken || !state.currentUser.canUseHq) return
  state.hq.saving = true
  state.lastError = ''
  try {
    const response = await authorizedFetch('/hq/organizations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    hydrateHq(repairPayload(await response.json()))
  } catch (error) {
    state.lastError = error.message || 'ساخت مجموعه ناموفق بود.'
    throw error
  } finally {
    state.hq.saving = false
  }
}

async function exportReport(reportId, format = 'csv', downloadUrl = '') {
  const hqOrganizationQuery = state.currentUser.isHq && state.hq.selectedOrganizationId
    ? `&organizationId=${encodeURIComponent(state.hq.selectedOrganizationId)}`
    : ''
  let requestPath = downloadUrl || (reportId ? `/reports/${reportId}/export?format=${encodeURIComponent(format)}` : '')
  if (requestPath && hqOrganizationQuery) {
    requestPath += requestPath.includes('?') ? hqOrganizationQuery : `?${hqOrganizationQuery.slice(1)}`
  }
  if (!requestPath) return
  const response = await authorizedFetch(requestPath)
  const blob = await response.blob()
  const disposition = response.headers.get('Content-Disposition') || ''
  const fileName = parseDownloadFilename(disposition) || `${reportId || 'report'}-report.${format === 'csv' ? 'csv' : 'xlsx'}`
  const objectUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = fileName
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000)
}

async function saveSettings(nextSettings) {
  const organizationQuery = state.currentUser.isHq && state.hq.selectedOrganizationId
    ? `?organizationId=${encodeURIComponent(state.hq.selectedOrganizationId)}`
    : ''
  const response = await authorizedFetch(`/settings/profile${organizationQuery}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...nextSettings,
      ...(state.currentUser.isHq && state.hq.selectedOrganizationId ? { organizationId: state.hq.selectedOrganizationId } : {}),
    }),
  })
  const payload = repairPayload(await response.json())
  Object.assign(state.settings, createSettingsState(), payload)
  replaceItems(state.settingsCards, payload.sections || [])
  state.settings.organizationUsers = (payload.organizationUsers || []).map(normalizeUser)
  state.settings.departments = payload.departments || []
  state.directories.departments = payload.departments || state.directories.departments
  state.currentUser.organization = payload.organizationName || state.currentUser.organization
}

async function restoreSession() {
  state.sessionReady = false
  if (!state.authToken) {
    state.sessionReady = true
    return
  }
  await loadBootstrapData(true)
  try {
    await loadSupportTickets(true)
  } catch (error) {
    state.lastError = error.message || state.lastError
  }
  if (canViewReports.value) {
    try {
      await loadReports(true)
    } catch (error) {
      state.lastError = error.message || state.lastError
    }
  }
}

async function login(email, password) {
  state.loginPending = true
  clearLastError()
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!response.ok) {
      const payload = repairPayload(await response.json())
      throw appErrorFromResponse(payload, response.status, 'ورود ناموفق بود.')
    }
    const payload = repairPayload(await response.json())
    state.authToken = payload.access_token
    localStorage.setItem(TOKEN_KEY, payload.access_token)
    state.bootstrapLoaded = false
    await loadBootstrapData(true)
    return true
  } catch (error) {
    setLastError(error, 'ورود ناموفق بود.')
    return false
  } finally {
    state.loginPending = false
    state.sessionReady = true
  }
}

async function submitSupportBankWithdrawComplete(ticketId, payload) {
  state.support.submitting = true
  state.support.error = ''
  try {
    const requestPayload = { ...payload, amount: normalizeAmountValue(payload?.amount) }
    const response = await authorizedFetch(`/support/tickets/${ticketId}/bank-withdraw-complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestPayload),
    })
    hydrateSupportTicket(repairPayload(await response.json()))
    await loadSupportTickets(true)
    await loadWalletDashboard(true)
  } catch (error) {
    state.support.error = error.message || 'Support bank withdrawal failed.'
    throw error
  } finally {
    state.support.submitting = false
  }
}

async function registerOrganization(payload) {
  state.loginPending = true
  clearLastError()
  try {
    const formData = new FormData()
    Object.entries(payload).forEach(([key, value]) => {
      if (key !== 'documents' && value !== undefined && value !== null) formData.append(key, value)
    })
    ;(payload.documents || []).forEach((file) => formData.append('documents', file))
    const response = await fetch(`${API_BASE_URL}/auth/register`, { method: 'POST', body: formData })
    if (!response.ok) {
      const errorPayload = repairPayload(await response.json())
      throw appErrorFromResponse(errorPayload, response.status, 'ثبت نام ناموفق بود.')
    }
    await response.json()
    return true
  } catch (error) {
    setLastError(error, 'ثبت نام ناموفق بود.')
    return false
  } finally {
    state.loginPending = false
  }
}

async function submitSupportRegistrationApproval(ticketId, companyCode) {
  state.support.submitting = true
  state.support.error = ''
  try {
    const response = await authorizedFetch(`/support/tickets/${ticketId}/approve-registration`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ companyCode }),
    })
    hydrateSupportTicket(repairPayload(await response.json()))
    await loadSupportTickets(true)
    return true
  } catch (error) {
    state.support.error = error.message || 'ثبت مجموعه ناموفق بود.'
    return false
  } finally {
    state.support.submitting = false
  }
}

let singleton

export function useWorkflowHub() {
  const router = useRouter()

  if (singleton) return singleton

  function ensureAuthenticatedRedirect() {
    if (!state.authToken) router.push('/login')
  }

  async function logout() {
    try {
      if (state.authToken) {
        await authorizedFetch('/auth/logout', { method: 'POST' })
      }
    } catch {
      // Local session cleanup must still happen if the server cannot record logout.
    } finally {
      clearSessionState()
      router.push('/login')
    }
  }

  function navigateTo(path) {
    router.push(path)
    state.mobileMenuOpen = false
  }

  function toggleSidebar() {
    state.mobileMenuOpen = !state.mobileMenuOpen
  }

  function updatePageFilter(page, key, value) {
    if (!state.filters[page]) return
    state.filters[page][key] = value
  }

  function resetPageFilters(page) {
    if (!state.filters[page]) return
    Object.assign(state.filters[page], { query: '', person: '', startDate: '', endDate: '' })
  }

  function hqScopedPath(path) {
    if (!state.currentUser.isHq || !state.hq.selectedOrganizationId) return path
    const separator = path.includes('?') ? '&' : '?'
    return `${path}${separator}organizationId=${encodeURIComponent(state.hq.selectedOrganizationId)}`
  }

  async function loadRequestDetail(requestId) {
    if (!requestId) return
    if (requestDetailState.items[requestId]) return
    requestDetailState.loading = true
    try {
      const response = await authorizedFetch(hqScopedPath(`/requests/${requestId}`))
      requestDetailState.items[requestId] = repairPayload(await response.json())
    } finally {
      requestDetailState.loading = false
    }
  }

  function openRequestDetail(id) {
    selectedState.requestId = id
    modalState.requestDetail = true
    void loadRequestDetail(id)
  }

  function closeRequestDetail() {
    modalState.requestDetail = false
  }

  async function loadExpenseDetail(id) {
    expenseDetailState.loading = true
    try {
      const response = await authorizedFetch(hqScopedPath(`/expenses/${id}`))
      expenseDetailState.item = normalizeExpense(repairPayload(await response.json()))
      selectedState.expenseId = id
    } finally {
      expenseDetailState.loading = false
    }
  }

  function openExpenseDetail(id) {
    modalState.expenseDetail = true
    void loadExpenseDetail(id)
  }

  function closeExpenseDetail() {
    modalState.expenseDetail = false
    expenseDetailState.item = null
  }

  async function loadApprovalDetail(id) {
    approvalDetailState.loading = true
    try {
      const response = await authorizedFetch(hqScopedPath(`/approvals/${id}`))
      approvalDetailState.item = normalizeApproval(repairPayload(await response.json()))
      selectedState.approvalId = id
    } finally {
      approvalDetailState.loading = false
    }
  }

  function openApprovalDetail(id) {
    modalState.approvalDetail = true
    void loadApprovalDetail(id)
  }

  function closeApprovalDetail() {
    modalState.approvalDetail = false
    approvalDetailState.item = null
  }

  function openRequestComposer() {
    clearLastError()
    resetRequestForm()
    modalState.requestComposer = true
  }

  function closeRequestComposer() {
    clearLastError()
    modalState.requestComposer = false
    resetRequestForm()
  }

  function openExpenseComposer() {
    clearLastError()
    resetExpenseForm()
    modalState.expenseComposer = true
  }

  function closeExpenseComposer() {
    clearLastError()
    modalState.expenseComposer = false
    resetExpenseForm()
  }

  function openUserComposer() {
    clearLastError()
    resetUserForm()
    modalState.userComposer = true
  }

  function closeUserComposer() {
    clearLastError()
    modalState.userComposer = false
    resetUserForm()
  }

  function openDocumentComposer() {
    clearLastError()
    resetDocumentForm()
    if (state.directories.managers.length === 1) {
      state.documentForm.assigneeIds = [state.directories.managers[0].id]
    }
    if (!state.documentForm.department && state.directories.departments.length === 1) {
      state.documentForm.department = state.directories.departments[0].code
    }
    modalState.documentComposer = true
  }

  function closeDocumentComposer() {
    clearLastError()
    modalState.documentComposer = false
    resetDocumentForm()
  }

  async function loadSignature() {
    if (!canApproveDocuments.value) return
    signatureState.loading = true
    try {
      const response = await authorizedFetch('/approvals/signature')
      const payload = repairPayload(await response.json())
      signatureState.hasSignature = payload.hasSignature
      signatureState.signatureData = payload.signatureData || ''
      signatureState.hasStamp = Boolean(payload.hasStamp)
      signatureState.stampData = payload.stampData || ''
      return true
    } catch (error) {
      signatureState.hasSignature = false
      signatureState.signatureData = ''
      signatureState.hasStamp = false
      signatureState.stampData = ''
      state.lastError = error.message || 'بارگذاری امضا انجام نشد.'
      return false
    } finally {
      signatureState.loading = false
    }
  }

  async function openSignatureComposer() {
    clearLastError()
    modalState.signatureComposer = true
    await loadSignature()
  }

  function closeSignatureComposer() {
    clearLastError()
    modalState.signatureComposer = false
  }

  function setRequestFiles(files) {
    state.requestForm.attachments = Array.from(files || [])
  }

  function removeAttachment(index) {
    state.requestForm.attachments = state.requestForm.attachments.filter((_, itemIndex) => itemIndex !== index)
  }

  function setExpenseInvoice(file) {
    state.expenseForm.invoice = file || null
  }

  function setDocumentFile(file) {
    state.documentForm.file = file || null
  }

  async function submitRequest() {
    state.requestSubmitting = true
    clearLastError()
    try {
      if (!String(state.requestForm.title || '').trim()) {
        throw createValidationError('عنوان درخواست الزامی است.', [{ field: 'title', message: 'عنوان درخواست را وارد کنید.' }])
      }
      if (!state.requestForm.manager) {
        throw createValidationError('حداقل یک مدیر ارجاع گیرنده باید انتخاب شود.', [{ field: 'manager', message: 'از بخش ارجاع گیرنده یک مدیر انتخاب کنید.' }])
      }

      const formData = new FormData()
      const primaryManagerId = state.directories.managers.find((item) => item.slug === state.requestForm.manager)?.id
      const managerAssigneeIds = (state.requestForm.managerAssigneeIds || [])
        .map((item) => Number(item))
        .filter((item) => item && item !== Number(primaryManagerId))
      formData.append('title', state.requestForm.title)
      formData.append('description', state.requestForm.description)
      formData.append('department', state.requestForm.department)
      formData.append('manager', state.requestForm.manager)
      formData.append('managerAssigneeIds', managerAssigneeIds.join(','))
      formData.append('employeeAssigneeIds', state.requestForm.employeeAssigneeIds.join(','))
      formData.append('priority', state.requestForm.priority)
      formData.append('action', 'refer')
      if (state.requestForm.deadline) formData.append('deadline', jalaliToIso(state.requestForm.deadline))
      state.requestForm.attachments.forEach((file) => formData.append('attachments', file))
      await authorizedFetch('/requests', { method: 'POST', body: formData })
      await loadBootstrapData(true)
      closeRequestComposer()
    } catch (error) {
      setLastError(error, 'ثبت درخواست ناموفق بود.')
      throw error
    } finally {
      state.requestSubmitting = false
    }
  }

  async function submitExpense(action = 'refer') {
    state.expenseSubmitting = true
    clearLastError()
    try {
      const amountValue = normalizeAmountValue(state.expenseForm.amount)
      if (!Number(amountValue || 0)) {
        throw createValidationError('مبلغ هزینه باید بیشتر از صفر باشد.', [{ field: 'amount', message: 'یک مبلغ معتبر و بزرگ تر از صفر وارد کنید.' }])
      }
      if (!String(state.expenseForm.description || '').trim()) {
        throw createValidationError('شرح هزینه الزامی است.', [{ field: 'description', message: 'شرح هزینه را وارد کنید.' }])
      }
      const formData = new FormData()
      formData.append('description', state.expenseForm.description)
      formData.append('amount', amountValue)
      formData.append('expenseDate', jalaliToIso(state.expenseForm.expenseDate))
      formData.append('department', state.expenseForm.department)
      formData.append('action', 'refer')
      formData.append('managerAssigneeIds', (state.expenseForm.managerAssigneeIds || []).join(','))
      formData.append('employeeAssigneeIds', (state.expenseForm.employeeAssigneeIds || []).join(','))
      if (state.expenseForm.invoice) formData.append('invoice', state.expenseForm.invoice)
      await authorizedFetch('/expenses', { method: 'POST', body: formData })
      await loadBootstrapData(true)
      closeExpenseComposer()
    } catch (error) {
      setLastError(error, 'ثبت هزینه ناموفق بود.')
      throw error
    } finally {
      state.expenseSubmitting = false
    }
  }

  async function submitUser() {
    state.userSubmitting = true
    clearLastError()
    try {
      if (!String(state.userForm.fullName || '').trim()) {
        throw createValidationError('نام کامل کاربر الزامی است.', [{ field: 'fullName', message: 'نام و نام خانوادگی را وارد کنید.' }])
      }
      if (!String(state.userForm.username || '').trim()) {
        throw createValidationError('نام کاربری الزامی است.', [{ field: 'username', message: 'نام کاربری کاربر را وارد کنید.' }])
      }
      if (state.userForm.password && String(state.userForm.password).length < 6) {
        throw createValidationError('رمز عبور باید حداقل 6 کاراکتر باشد.', [{ field: 'password', message: 'رمز عبور کوتاه است.' }])
      }
      await authorizedFetch('/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...state.userForm,
          username: state.userForm.username,
          managerId: state.userForm.managerId ? Number(state.userForm.managerId) : null,
        }),
      })
      await loadBootstrapData(true)
      if (state.currentUser.canAccessSettings || state.currentUser.canManageUsers) {
        await loadSettings(true)
      }
      closeUserComposer()
    } catch (error) {
      setLastError(error, 'ایجاد کاربر ناموفق بود.')
      throw error
    } finally {
      state.userSubmitting = false
    }
  }

  async function submitDocument() {
    state.documentSubmitting = true
    clearLastError()
    try {
      if (!String(state.documentForm.title || '').trim()) {
        throw createValidationError('عنوان سند الزامی است.', [{ field: 'title', message: 'عنوان سند را وارد کنید.' }])
      }
      if (!state.documentForm.file) {
        throw createValidationError('فایل سند الزامی است.', [{ field: 'file', message: 'فایل سند را انتخاب کنید.' }])
      }
      if (!state.documentForm.assigneeIds.length) {
        throw createValidationError('حداقل یک دریافت کننده را انتخاب کنید.', [{ field: 'assigneeIds', message: 'حداقل یک دریافت کننده برای سند انتخاب کنید.' }])
      }
      const formData = new FormData()
      formData.append('title', state.documentForm.title)
      formData.append('description', state.documentForm.description)
      formData.append('department', state.documentForm.department)
      formData.append('documentType', state.documentForm.documentType)
      formData.append('risk', state.documentForm.risk)
      formData.append('assigneeIds', state.documentForm.assigneeIds.join(','))
      if (state.documentForm.file) formData.append('file', state.documentForm.file)
      await authorizedFetch('/approvals/documents', { method: 'POST', body: formData })
      await loadBootstrapData(true)
      closeDocumentComposer()
    } catch (error) {
      setLastError(error, 'ثبت سند ناموفق بود.')
      throw error
    } finally {
      state.documentSubmitting = false
    }
  }

  async function saveSignature(signatureData, stampData = '') {
    signatureState.loading = true
    state.lastError = ''
    try {
      const response = await authorizedFetch('/approvals/signature', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ signatureData, stampData }),
      })
      const payload = repairPayload(await response.json())
      signatureState.hasSignature = payload.hasSignature
      signatureState.signatureData = payload.signatureData
      signatureState.hasStamp = Boolean(payload.hasStamp)
      signatureState.stampData = payload.stampData || ''
      closeSignatureComposer()
      await loadBootstrapData(true)
    } catch (error) {
      state.lastError = error.message || 'ثبت امضا ناموفق بود.'
      throw error
    } finally {
      signatureState.loading = false
    }
  }

  async function approveSelectedDocument() {
    if (!selectedApproval.value) return
    state.lastError = ''
    try {
      await authorizedFetch(hqScopedPath(`/approvals/${selectedApproval.value.id}/approve`), { method: 'POST' })
      await loadBootstrapData(true)
      await loadApprovalDetail(selectedApproval.value.id)
    } catch (error) {
      state.lastError = error.message || 'تایید سند ناموفق بود.'
      throw error
    }
  }

  async function rejectSelectedDocument(reason = '') {
    if (!selectedApproval.value) return
    state.lastError = ''
    try {
      await authorizedFetch(hqScopedPath(`/approvals/${selectedApproval.value.id}/reject`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason }),
      })
      await loadBootstrapData(true)
      await loadApprovalDetail(selectedApproval.value.id)
    } catch (error) {
      state.lastError = error.message || 'رد سند ناموفق بود.'
      throw error
    }
  }

  async function approveSelectedRequest() {
    if (!selectedRequest.value) return
    state.lastError = ''
    try {
      await authorizedFetch(hqScopedPath(`/requests/${selectedRequest.value.id}/approve`), { method: 'POST' })
      await loadBootstrapData(true)
      await loadRequestDetail(selectedRequest.value.id)
    } catch (error) {
      state.lastError = error.message || 'تایید درخواست ناموفق بود.'
      throw error
    }
  }

  async function rejectSelectedRequest(reason = '') {
    if (!selectedRequest.value) return
    state.lastError = ''
    try {
      await authorizedFetch(hqScopedPath(`/requests/${selectedRequest.value.id}/reject`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason }),
      })
      await loadBootstrapData(true)
      await loadRequestDetail(selectedRequest.value.id)
    } catch (error) {
      state.lastError = error.message || 'رد درخواست ناموفق بود.'
      throw error
    }
  }

  async function referSelectedRequest(payload) {
    if (!selectedRequest.value) return
    state.lastError = ''
    await authorizedFetch(hqScopedPath(`/requests/${selectedRequest.value.id}/refer`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    await loadBootstrapData(true)
    await loadRequestDetail(selectedRequest.value.id)
  }

  async function approveSelectedExpense() {
    if (!selectedExpense.value) return
    state.lastError = ''
    try {
      await authorizedFetch(hqScopedPath(`/expenses/${selectedExpense.value.id}/approve`), { method: 'POST' })
      await loadBootstrapData(true)
      await loadExpenseDetail(selectedExpense.value.id)
    } catch (error) {
      state.lastError = error.message || 'تایید هزینه ناموفق بود.'
      throw error
    }
  }

  async function rejectSelectedExpense(reason = '') {
    if (!selectedExpense.value) return
    state.lastError = ''
    try {
      await authorizedFetch(hqScopedPath(`/expenses/${selectedExpense.value.id}/reject`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason }),
      })
      await loadBootstrapData(true)
      await loadExpenseDetail(selectedExpense.value.id)
    } catch (error) {
      state.lastError = error.message || 'رد هزینه ناموفق بود.'
      throw error
    }
  }

  async function referSelectedExpense(payload) {
    if (!selectedExpense.value) return
    state.lastError = ''
    await authorizedFetch(hqScopedPath(`/expenses/${selectedExpense.value.id}/refer`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    await loadBootstrapData(true)
    await loadExpenseDetail(selectedExpense.value.id)
  }

async function updateUser(userId, payload) {
  clearLastError()
  try {
    const response = await authorizedFetch(`/users/${userId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...payload,
        managerId: payload.managerId ? Number(payload.managerId) : null,
      }),
    })
    const updatedUser = normalizeUser(repairPayload(await response.json()))
    syncUserAcrossState(updatedUser)
    if (state.currentUser.canAccessSettings || state.currentUser.canManageUsers) {
      try {
        await loadSettings(true)
      } catch (error) {
        setLastError(error, 'کاربر ذخیره شد اما تازه‌سازی تنظیمات انجام نشد.')
      }
    }
    return updatedUser
  } catch (error) {
    setLastError(error, 'ذخیره تغییرات کاربر ناموفق بود.')
    throw error
  }
}

  async function referSelectedDocument(payload) {
    if (!selectedApproval.value) return
    state.lastError = ''
    await authorizedFetch(hqScopedPath(`/approvals/${selectedApproval.value.id}/refer`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    await loadBootstrapData(true)
    await loadApprovalDetail(selectedApproval.value.id)
  }

  singleton = {
    state,
    modalState,
    requestDetailState,
    expenseDetailState,
    approvalDetailState,
    signatureState,
    selectedRequest,
    selectedExpense,
    selectedApproval,
    selectedRequestTimeline,
    canApproveSelectedRequest,
    canApproveSelectedExpense,
    filteredRequests,
    filteredExpenses,
    filteredApprovals,
    approvalInbox,
    approvalHistory,
    filteredReports,
    filteredUsers,
    requestPeople,
    requestManagerAssigneeOptions,
    expensePeople,
    approvalPeople,
    reportPeople,
    userPeople,
    canManageUsers,
    canViewReports,
    canAccessApprovals,
    canApproveDocuments,
    isLicenseLocked,
    canAccessCloud,
    visibleNavItems,
    priorityLabel,
    departmentLabel,
    managerLabel,
    availableManagerDirectory,
    availableRecipientUsers,
    requestManagerAssigneeNames,
    requestEmployeeAssigneeNames,
    setRequestManager,
    navigateTo,
    toggleSidebar,
    updatePageFilter,
    resetPageFilters,
    clearLastError,
    setLastError,
    fieldHasError,
    login,
    registerOrganization,
    submitSupportRegistrationApproval,
    logout,
    restoreSession,
    ensureAuthenticatedRedirect,
    loadBootstrapData,
    loadReports,
    loadSettings,
    loadWalletDashboard,
    loadWalletOptions,
    submitFeaturePurchase,
    submitWalletTransaction,
    loadSupportTickets,
    loadSupportTicketDetail,
    createSupportTicket,
    submitSupportReply,
    submitSupportFeedback,
    submitSupportWalletDeposit,
    submitSupportBankWithdrawComplete,
    supportUnreadCount,
    requestInboxCount,
    expenseInboxCount,
    approvalInboxCount,
    markSupportTicketsSeen,
    loadHqPanel,
    selectHqOrganization,
    createHqOrganization,
    saveSettings,
    saveHqEntity,
    exportReport,
    openProtectedFile,
    downloadProtectedFile,
    createProtectedObjectUrl,
    openRequestDetail,
    closeRequestDetail,
    openExpenseDetail,
    closeExpenseDetail,
    openApprovalDetail,
    closeApprovalDetail,
    openRequestComposer,
    closeRequestComposer,
    openExpenseComposer,
    closeExpenseComposer,
    openUserComposer,
    closeUserComposer,
    openDocumentComposer,
    closeDocumentComposer,
    openSignatureComposer,
    closeSignatureComposer,
    loadSignature,
    setRequestFiles,
    removeAttachment,
    setExpenseInvoice,
    setDocumentFile,
    submitRequest,
    submitExpense,
    submitUser,
    submitDocument,
    saveSignature,
    approveSelectedRequest,
    rejectSelectedRequest,
    referSelectedRequest,
    approveSelectedExpense,
    rejectSelectedExpense,
    referSelectedExpense,
    updateUser,
    formatMoneyInputValue,
    approveSelectedDocument,
    rejectSelectedDocument,
    referSelectedDocument,
  }

  return singleton
}





