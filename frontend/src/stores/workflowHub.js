import { computed, reactive } from 'vue'
import { useRouter } from 'vue-router'

import { jalaliToIso } from '../utils/jalali'
import { repairPayload } from '../utils/stitch'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const API_ORIGIN = API_BASE_URL.replace(/\/api\/v1\/?$/, '')
const TOKEN_KEY = 'workflow-hub-token'

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
    canViewReports: false,
    canApproveDocuments: false,
    isManager: false,
  }
}

function createRequestForm() {
  return {
    title: '',
    description: '',
    department: '',
    manager: '',
    managerAssigneeIds: [],
    priority: 'medium',
    deadline: '',
    attachments: [],
  }
}

function createExpenseForm() {
  return {
    description: '',
    amount: '',
    expenseDate: '',
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
    canEdit: false,
  }
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

const signatureState = reactive({
  loading: false,
  hasSignature: false,
  signatureData: '',
})

const selectedState = reactive({
  requestId: '',
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
  return {
    ...item,
    previewUrl: resolveAssetUrl(item?.previewUrl),
    downloadUrl: resolveAssetUrl(item?.downloadUrl || item?.previewUrl),
  }
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
  state.directories.departments = []
  state.directories.managers = []
  state.directories.users = []
  state.reportSummary = null
  state.reportStatus = {}
  state.topSubmitters = []
  signatureState.hasSignature = false
  signatureState.signatureData = ''
  approvalDetailState.item = null
  selectedState.requestId = ''
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

const selectedRequestTimeline = computed(() => requestDetailState.items[selectedState.requestId]?.timeline ?? [])

const canManageUsers = computed(() => state.currentUser.canManageUsers)
const canAccessUsers = computed(() => state.currentUser.canAccessUsers || canManageUsers.value)
const canViewReports = computed(() => state.currentUser.canViewReports)
const canApproveDocuments = computed(() => state.currentUser.canApproveDocuments)

const visibleNavItems = computed(() => {
  const items = [
    { to: '/dashboard', label: 'داشبورد', icon: 'dashboard' },
    { to: '/requests', label: 'درخواست‌ها', icon: 'assignment' },
  ]
  if (canApproveDocuments.value) items.push({ to: '/approvals', label: 'تاییدیه‌ها', icon: 'fact_check' })
  if (canViewReports.value) items.push({ to: '/reports', label: 'گزارشات', icon: 'monitoring' })
  if (canManageUsers.value) items.push({ to: '/users', label: 'کاربران', icon: 'group' })

  items.push({ to: '/settings', label: 'تنظیمات', icon: 'settings' })
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
  replaceItems(state.reports, payload.reports)
  replaceItems(state.activities, payload.activities)
  replaceItems(state.insights, payload.insights)
  replaceItems(state.expenseSummary, payload.expenseSummary)
  replaceItems(state.settingsCards, payload.settingsCards)
  if (payload.settings) Object.assign(state.settings, createSettingsState(), payload.settings)
  Object.assign(state.approvalMetrics, payload.approvalMetrics || {})
  state.directories.departments = payload.directories?.departments || []
  state.directories.managers = payload.directories?.managers || []
  state.directories.users = payload.directories?.users || []

  selectedState.requestId = state.requests[0]?.id || ''
  if (!approvalDetailState.item) selectedState.approvalId = state.approvals[0]?.id || ''
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
    const response = await authorizedFetch('/bootstrap')
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
  if (state.reportSummary && !force) return
  const response = await authorizedFetch('/reports')
  const payload = repairPayload(await response.json())
  state.reportSummary = payload.summary
  state.reportStatus = payload.requestStatus
  state.topSubmitters = payload.topSubmitters
  replaceItems(state.reports, payload.reports || [])
}

async function loadSettings(force = false) {
  if (!state.authToken) return
  if (state.settings.systemId && !force) return
  const response = await authorizedFetch('/settings/profile')
  const payload = repairPayload(await response.json())
  Object.assign(state.settings, createSettingsState(), payload)
  replaceItems(state.settingsCards, payload.sections || [])
  state.settings.organizationUsers = payload.organizationUsers || []
  state.currentUser.organization = payload.organizationName || state.currentUser.organization
}

async function exportReport(reportId, format = 'csv') {
  if (!reportId) return
  const response = await authorizedFetch(`/reports/${reportId}/export?format=${encodeURIComponent(format)}`)
  const blob = await response.blob()
  const disposition = response.headers.get('Content-Disposition') || ''
  const match = disposition.match(/filename="([^"]+)"/i)
  const fileName = match?.[1] || `${reportId}-report.${format === 'csv' ? 'csv' : 'xlsx'}`
  const objectUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(objectUrl)
}

async function saveSettings(nextSettings) {
  const response = await authorizedFetch('/settings/profile', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(nextSettings),
  })
  const payload = repairPayload(await response.json())
  Object.assign(state.settings, createSettingsState(), payload)
  replaceItems(state.settingsCards, payload.sections || [])
  state.settings.organizationUsers = payload.organizationUsers || []
  state.currentUser.organization = payload.organizationName || state.currentUser.organization
}

async function restoreSession() {
  state.sessionReady = false
  if (!state.authToken) {
    state.sessionReady = true
    return
  }
  await loadBootstrapData(true)
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

  async function loadRequestDetail(requestId) {
    if (!requestId) return
    if (requestDetailState.items[requestId]) return
    requestDetailState.loading = true
    try {
      const response = await authorizedFetch(`/requests/${requestId}`)
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

  async function loadApprovalDetail(id) {
    approvalDetailState.loading = true
    try {
      const response = await authorizedFetch(`/approvals/${id}`)
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
      if (!state.documentForm.file) {
        throw new Error('فایل سند الزامی است.')
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
    await authorizedFetch(`/approvals/${selectedApproval.value.id}/approve`, { method: 'POST' })
    await loadBootstrapData(true)
    await loadApprovalDetail(selectedApproval.value.id)
  }

  async function rejectSelectedDocument(reason = '') {
    if (!selectedApproval.value) return
    await authorizedFetch(`/approvals/${selectedApproval.value.id}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason }),
    })
    await loadBootstrapData(true)
    await loadApprovalDetail(selectedApproval.value.id)
  }

  singleton = {
    state,
    modalState,
    requestDetailState,
    approvalDetailState,
    signatureState,
    selectedRequest,
    selectedApproval,
    selectedRequestTimeline,
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
    canApproveDocuments,
    visibleNavItems,
    priorityLabel,
    departmentLabel,
    managerLabel,
    requestManagerAssigneeNames,
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
    saveSettings,
    exportReport,
    openRequestDetail,
    closeRequestDetail,
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
    approveSelectedDocument,
    rejectSelectedDocument,
  }

  return singleton
}





