import { computed, reactive } from 'vue'
import { useRouter } from 'vue-router'

import { formatJalali, getTodayJalali, jalaliToIso } from '../utils/jalali'
import { repairPayload } from '../utils/stitch'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const API_ORIGIN = API_BASE_URL.replace(/\/api\/v1\/?$/, '')
const TOKEN_KEY = 'workflow-hub-token'
const SUPPORT_SEEN_KEY = 'workflow-hub-support-seen'

function createCurrentUser() {
  return {
    id: null,
    slug: '',
    name: '',
    role: '',
    accessRole: '',
    department: '',
    avatar: '',
    email: '',
    organization: '',
    canManageUsers: false,
    canAccessUsers: false,
    canAccessExpenses: true,
    canAccessSettings: false,
    canViewReports: false,
    canAccessApprovals: false,
    canApproveDocuments: false,
    isManager: false,
    isHq: false,
    canUseHq: false,
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
    invoice: null,
  }
}

function createUserForm() {
  return {
    fullName: '',
    email: '',
    password: '',
    accessRole: 'employee',
    department: '',
    managerId: '',
    jobTitle: '',
    sectionAccess: {
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
      depositsTotal: '0.00',
      depositsTotalRaw: 0,
      withdrawalsTotal: '0.00',
      withdrawalsTotalRaw: 0,
      transactions: 0,
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

function resolveAssetUrl(rawUrl) {
  if (!rawUrl) return ''
  if (/^https?:\/\//i.test(rawUrl) || rawUrl.startsWith('data:')) return rawUrl
  if (rawUrl.startsWith('/')) return `${API_ORIGIN}${rawUrl}`
  return `${API_ORIGIN}/${rawUrl}`
}

function normalizeExpense(item) {
  return {
    ...item,
    invoiceUrl: resolveAssetUrl(item?.invoiceUrl),
  }
}

function normalizeApproval(item) {
  const hqDownloadQuery = state.currentUser.isHq && state.hq.selectedOrganizationId && item?.downloadUrl
    ? `${item.downloadUrl.includes('?') ? '&' : '?'}organizationId=${encodeURIComponent(state.hq.selectedOrganizationId)}`
    : ''
  return {
    ...item,
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
    throw new Error('UNAUTHORIZED')
  }

  if (!response.ok) {
    let detail = `Request failed: ${response.status}`
    try {
      const payload = repairPayload(await response.json())
      detail = payload.detail || detail
    } catch {
      // ignore parse failure
    }
    throw new Error(detail)
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
  state.lastError = ''
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

const canApproveSelectedRequest = computed(() => {
  const request = selectedRequest.value
  if (!request) return false
  const currentName = String(state.currentUser.name || '').trim()
  const managerName = String(request.manager || '').trim()
  const assignedManagers = Array.isArray(request.managerAssignees) ? request.managerAssignees : []
  const isPrivileged = ['admin', 'executive_manager'].includes(String(state.currentUser.accessRole || ''))
  const isManagerTarget = currentName && (managerName === currentName || assignedManagers.includes(currentName))
  const status = String(request.status || '')
  const isOpen = status.includes('ثبت') || status.includes('بررسی')
  return isOpen && (isPrivileged || isManagerTarget)
})

const canApproveSelectedExpense = computed(() => {
  const expense = selectedExpense.value
  if (!expense) return false
  const role = String(state.currentUser.accessRole || '')
  const isPrivileged = ['admin', 'executive_manager', 'manager'].includes(role)
  const status = String(expense.status || '')
  const isOpen = status.includes('انتظار') || status.includes('بررسی')
  return isOpen && isPrivileged
})

const canManageUsers = computed(() => state.currentUser.canManageUsers)
const canAccessUsers = computed(() => state.currentUser.canAccessUsers || canManageUsers.value)
const canViewReports = computed(() => state.currentUser.canViewReports)
const canAccessApprovals = computed(() => state.currentUser.canAccessApprovals || state.currentUser.canApproveDocuments)
const canApproveDocuments = computed(() => state.currentUser.canApproveDocuments)

const visibleNavItems = computed(() => {
  const items = [
    { to: '/dashboard', label: 'داشبورد', icon: 'dashboard' },
    { to: '/requests', label: 'درخواست‌ها', icon: 'assignment' },
  ]
  if (canAccessApprovals.value) items.push({ to: '/approvals', label: 'تاییدیه‌ها', icon: 'fact_check' })
  if (canViewReports.value) items.push({ to: '/reports', label: 'گزارشات', icon: 'monitoring' })
  if (canAccessUsers.value) items.push({ to: '/users', label: 'کاربران', icon: 'group' })

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
    matchesQuery(item, ['name', 'email', 'role', 'department', 'manager', 'status'], query) &&
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

const requestManagerAssigneeOptions = computed(() => {
  if (!state.requestForm.manager) return []
  return state.directories.managers.filter((item) => item.slug !== state.requestForm.manager)
})

function requestManagerAssigneeNames(ids = state.requestForm.managerAssigneeIds) {
  const normalizedIds = (ids || []).map((item) => Number(item))
  const names = state.directories.managers
    .filter((item) => normalizedIds.includes(item.id))
    .map((item) => item.name)
  return names.length ? names.join('، ') : 'تعیین نشده'
}

function requestEmployeeAssigneeNames(ids = state.requestForm.employeeAssigneeIds) {
  const normalizedIds = (ids || []).map((item) => Number(item))
  const names = state.users
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
    throw new Error('UNAUTHORIZED')
  }

  if (!response.ok) {
    let detail = `Request failed: ${response.status}`
    try {
      const payload = repairPayload(await response.json())
      detail = payload.detail || detail
    } catch {
      // ignore parse failure
    }
    throw new Error(detail)
  }

  return response
}

function hydrateBootstrap(payload) {
  if (!payload) return

  Object.assign(state.currentUser, createCurrentUser(), payload.currentUser || {})
  replaceItems(state.stats, payload.stats)
  replaceItems(state.chartData, payload.chartData)
  replaceItems(state.pipeline, payload.pipeline)
  replaceItems(state.requests, payload.requests)
  replaceItems(state.expenses, (payload.expenses || []).map(normalizeExpense))
  replaceItems(state.approvals, (payload.approvals || []).map(normalizeApproval))
  replaceItems(state.users, payload.users)
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
  state.directories.users = payload.directories?.users || []

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
  if (state.currentUser.isHq) return 0
  void state.support.seenVersion
  const seenMap = readSupportSeenMap()
  return (state.support.tickets || []).filter((ticket) => {
    if (ticket.status !== 'answered') return false
    const seenAt = seenMap[String(ticket.id)]
    return seenAt !== ticket.updatedAt
  }).length
})

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
  state.lastError = ''
  try {
    const organizationQuery = state.currentUser.isHq && state.hq.selectedOrganizationId
      ? `?organizationId=${encodeURIComponent(state.hq.selectedOrganizationId)}`
      : ''
    const response = await authorizedFetch(`/bootstrap${organizationQuery}`)
    const payload = repairPayload(await response.json())
    hydrateBootstrap(payload)
    state.bootstrapLoaded = true
  } catch (error) {
    state.lastError = error.message || 'خطا در بارگذاری'
    if (error.message === 'UNAUTHORIZED') throw error
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
  state.settings.organizationUsers = payload.organizationUsers || []
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

async function loadSupportTickets(force = false) {
  if (!state.authToken) return
  if (state.currentUser.isHq && !state.hq.selectedOrganizationId) {
    resetSupportState()
    return
  }
  if (state.support.loaded && !force) return
  state.support.loading = true
  state.support.error = ''
  try {
    const response = await authorizedFetch(scopedApiPath('/support/tickets'))
    hydrateSupportTickets(repairPayload(await response.json()))
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

async function submitWalletTransaction(payload) {
  if (!payload) return
  state.wallet.submitting = true
  state.wallet.error = ''
  state.wallet.message = ''
  try {
    const response = await authorizedFetch(scopedApiPath('/wallet/transactions'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    hydrateWallet(repairPayload(await response.json()))
    state.wallet.message = payload.direction === 'out' || payload.type === 'withdraw'
      ? 'برداشت ثبت شد.'
      : 'شارژ ثبت شد.'
  } catch (error) {
    state.wallet.error = error.message || 'Wallet transaction failed.'
    throw error
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
    const response = await authorizedFetch(endpoints[type], {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
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
  const requestPath = downloadUrl || (reportId ? `/reports/${reportId}/export?format=${encodeURIComponent(format)}${hqOrganizationQuery}` : '')
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
  state.settings.organizationUsers = payload.organizationUsers || []
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
  state.lastError = ''
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!response.ok) {
      const payload = repairPayload(await response.json())
      throw new Error(payload.detail || 'ورود ناموفق بود.')
    }
    const payload = repairPayload(await response.json())
    state.authToken = payload.access_token
    localStorage.setItem(TOKEN_KEY, payload.access_token)
    state.bootstrapLoaded = false
    await loadBootstrapData(true)
    return true
  } finally {
    state.loginPending = false
    state.sessionReady = true
  }
}

let singleton

export function useWorkflowHub() {
  const router = useRouter()

  if (singleton) return singleton

  function ensureAuthenticatedRedirect() {
    if (!state.authToken) router.push('/login')
  }

  function logout() {
    clearSessionState()
    router.push('/login')
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
    resetRequestForm()
    modalState.requestComposer = true
  }

  function closeRequestComposer() {
    modalState.requestComposer = false
    resetRequestForm()
  }

  function openExpenseComposer() {
    resetExpenseForm()
    modalState.expenseComposer = true
  }

  function closeExpenseComposer() {
    modalState.expenseComposer = false
    resetExpenseForm()
  }

  function openUserComposer() {
    resetUserForm()
    modalState.userComposer = true
  }

  function closeUserComposer() {
    modalState.userComposer = false
    resetUserForm()
  }

  function openDocumentComposer() {
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
    } finally {
      signatureState.loading = false
    }
  }

  async function openSignatureComposer() {
    await loadSignature()
    modalState.signatureComposer = true
  }

  function closeSignatureComposer() {
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

  async function submitRequest(action = 'refer') {
    state.requestSubmitting = true
    state.lastError = ''
    try {
      if (!state.requestForm.manager) {
        throw new Error('انتخاب مدیر الزامی است.')
      }

      const formData = new FormData()
      formData.append('title', state.requestForm.title)
      formData.append('description', state.requestForm.description)
      formData.append('department', state.requestForm.department)
      formData.append('manager', state.requestForm.manager)
      formData.append('managerAssigneeIds', state.requestForm.managerAssigneeIds.join(','))
      formData.append('employeeAssigneeIds', state.requestForm.employeeAssigneeIds.join(','))
      formData.append('priority', state.requestForm.priority)
      formData.append('action', action)
      if (state.requestForm.deadline) formData.append('deadline', jalaliToIso(state.requestForm.deadline))
      state.requestForm.attachments.forEach((file) => formData.append('attachments', file))
      await authorizedFetch('/requests', { method: 'POST', body: formData })
      await loadBootstrapData(true)
      closeRequestComposer()
    } catch (error) {
      state.lastError = error.message || 'ثبت درخواست ناموفق بود.'
      throw error
    } finally {
      state.requestSubmitting = false
    }
  }

  async function submitExpense(action = 'refer') {
    state.expenseSubmitting = true
    state.lastError = ''
    try {
      const formData = new FormData()
      formData.append('description', state.expenseForm.description)
      formData.append('amount', state.expenseForm.amount)
      formData.append('expenseDate', jalaliToIso(state.expenseForm.expenseDate))
      formData.append('department', state.expenseForm.department)
      formData.append('action', action)
      if (state.expenseForm.invoice) formData.append('invoice', state.expenseForm.invoice)
      await authorizedFetch('/expenses', { method: 'POST', body: formData })
      await loadBootstrapData(true)
      closeExpenseComposer()
    } catch (error) {
      state.lastError = error.message || 'ثبت هزینه ناموفق بود.'
      throw error
    } finally {
      state.expenseSubmitting = false
    }
  }

  async function submitUser() {
    state.userSubmitting = true
    state.lastError = ''
    try {
      await authorizedFetch('/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...state.userForm,
          managerId: state.userForm.managerId ? Number(state.userForm.managerId) : null,
        }),
      })
      await loadBootstrapData(true)
      closeUserComposer()
    } catch (error) {
      state.lastError = error.message || 'ایجاد کاربر ناموفق بود.'
      throw error
    } finally {
      state.userSubmitting = false
    }
  }

  async function submitDocument() {
    state.documentSubmitting = true
    state.lastError = ''
    try {
      if (!state.documentForm.assigneeIds.length) {
        throw new Error('حداقل یک مدیر دریافت کننده را انتخاب کنید.')
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
      state.lastError = error.message || 'ثبت سند ناموفق بود.'
      throw error
    } finally {
      state.documentSubmitting = false
    }
  }

  async function saveSignature(signatureData) {
    signatureState.loading = true
    state.lastError = ''
    try {
      const response = await authorizedFetch('/approvals/signature', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ signatureData }),
      })
      const payload = repairPayload(await response.json())
      signatureState.hasSignature = payload.hasSignature
      signatureState.signatureData = payload.signatureData
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
    await authorizedFetch(hqScopedPath(`/requests/${selectedRequest.value.id}/approve`), { method: 'POST' })
    await loadBootstrapData(true)
    await loadRequestDetail(selectedRequest.value.id)
  }

  async function rejectSelectedRequest(reason = '') {
    if (!selectedRequest.value) return
    await authorizedFetch(hqScopedPath(`/requests/${selectedRequest.value.id}/reject`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason }),
    })
    await loadBootstrapData(true)
    await loadRequestDetail(selectedRequest.value.id)
  }

  async function approveSelectedExpense() {
    if (!selectedExpense.value) return
    await authorizedFetch(hqScopedPath(`/expenses/${selectedExpense.value.id}/approve`), { method: 'POST' })
    await loadBootstrapData(true)
    await loadExpenseDetail(selectedExpense.value.id)
  }

  async function rejectSelectedExpense(reason = '') {
    if (!selectedExpense.value) return
    await authorizedFetch(hqScopedPath(`/expenses/${selectedExpense.value.id}/reject`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason }),
    })
    await loadBootstrapData(true)
    await loadExpenseDetail(selectedExpense.value.id)
  }

  async function updateUser(userId, payload) {
    state.lastError = ''
    await authorizedFetch(`/users/${userId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...payload,
        managerId: payload.managerId ? Number(payload.managerId) : null,
      }),
    })
    await loadBootstrapData(true)
    if (state.currentUser.canAccessSettings || state.currentUser.canManageUsers) {
      await loadSettings(true)
    }
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
    visibleNavItems,
    priorityLabel,
    departmentLabel,
    managerLabel,
    requestManagerAssigneeNames,
    requestEmployeeAssigneeNames,
    setRequestManager,
    navigateTo,
    toggleSidebar,
    updatePageFilter,
    resetPageFilters,
    login,
    logout,
    restoreSession,
    ensureAuthenticatedRedirect,
    loadBootstrapData,
    loadReports,
    loadSettings,
    loadWalletDashboard,
    submitWalletTransaction,
    loadSupportTickets,
    loadSupportTicketDetail,
    createSupportTicket,
    submitSupportReply,
    submitSupportFeedback,
    supportUnreadCount,
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
    approveSelectedExpense,
    rejectSelectedExpense,
    updateUser,
    approveSelectedDocument,
    rejectSelectedDocument,
  }

  return singleton
}




