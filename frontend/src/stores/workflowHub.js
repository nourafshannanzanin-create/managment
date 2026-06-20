import { computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { jalaliToIso } from '../utils/jalali'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const DEMO_CREDENTIALS = {
  email: 'admin@karomand.local',
  password: 'AdminSecret!',
}

const state = reactive({
  authToken: '',
  bootstrapLoaded: false,
  mobileMenuOpen: false,
  composerStep: 1,
  requestSubmitting: false,
  selectedRequestId: '',
  selectedApprovalId: '',
  currentUser: {
    name: 'آرمان کریمی',
    role: 'مدیر ارشد عملیات',
    department: 'ستاد مرکزی',
    avatar: 'AK',
    email: 'admin@karomand.local',
  },
  stats: [],
  chartData: [],
  pipeline: [],
  requests: [],
  approvals: [],
  expenses: [],
  users: [],
  reports: [],
  activities: [],
  insights: [],
  expenseSummary: [],
  approvalMetrics: {
    pending: 0,
    approved: 0,
    rejected: 0,
  },
  settingsCards: [
    { title: 'امنیت', description: '' },
    { title: 'برندینگ', description: '' },
    { title: 'اعلان‌ها', description: '' },
    { title: 'یکپارچه‌سازی', description: '' },
  ],
  requestForm: {
    title: '',
    description: '',
    department: '',
    manager: '',
    priority: 'medium',
    deadline: '',
    attachments: [],
  },
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
  approvalDetail: false,
  composer: false,
})

const requestDetailState = reactive({
  loading: false,
  items: {},
})

const selectedRequest = computed(
  () => state.requests.find((item) => item.id === state.selectedRequestId) ?? state.requests[0] ?? null,
)

const selectedApproval = computed(
  () => state.approvals.find((item) => item.id === state.selectedApprovalId) ?? state.approvals[0] ?? null,
)

const selectedRequestTimeline = computed(() => {
  const detail = requestDetailState.items[state.selectedRequestId]
  return detail?.timeline ?? []
})

const requestCompletion = computed(() => {
  const fields = [
    state.requestForm.title,
    state.requestForm.description,
    state.requestForm.department,
    state.requestForm.manager,
    state.requestForm.priority,
    state.requestForm.deadline,
  ]
  return Math.round((fields.filter(Boolean).length / fields.length) * 100)
})

const approvalMetricCards = computed(() => [
  { label: 'در انتظار', value: state.approvalMetrics.pending, tone: '' },
  { label: 'تأیید شده', value: state.approvalMetrics.approved, tone: 'success' },
  { label: 'رد شده', value: state.approvalMetrics.rejected, tone: 'danger' },
])

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
  return fields.some((field) => item[field] === person)
}

const filteredRequests = computed(() => {
  const filter = state.filters.requests
  const query = filter.query.trim().toLowerCase()
  return state.requests.filter((item) =>
    matchesQuery(item, ['title', 'owner', 'manager', 'department', 'status', 'id'], query) &&
    matchesPerson(item, ['owner', 'manager'], filter.person) &&
    inDateRange(item.deadlineIso, filter.startDate, filter.endDate),
  )
})

const filteredExpenses = computed(() => {
  const filter = state.filters.expenses
  const query = filter.query.trim().toLowerCase()
  return state.expenses.filter((item) =>
    matchesQuery(item, ['title', 'category', 'owner', 'status', 'id'], query) &&
    matchesPerson(item, ['owner'], filter.person) &&
    inDateRange(item.createdAtIso, filter.startDate, filter.endDate),
  )
})

const filteredApprovals = computed(() => {
  const filter = state.filters.approvals
  const query = filter.query.trim().toLowerCase()
  return state.approvals.filter((item) =>
    matchesQuery(item, ['title', 'type', 'owner', 'department', 'status', 'id'], query) &&
    matchesPerson(item, ['owner'], filter.person) &&
    inDateRange(item.uploadedAtIso, filter.startDate, filter.endDate),
  )
})

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
    matchesQuery(item, ['name', 'role', 'department', 'kpi', 'manager'], query) &&
    matchesPerson(item, ['name', 'manager'], filter.person) &&
    inDateRange(item.joinedAtIso, filter.startDate, filter.endDate),
  )
})

const requestPeople = computed(() => [...new Set(state.requests.flatMap((item) => [item.owner, item.manager]).filter(Boolean))])
const expensePeople = computed(() => [...new Set(state.expenses.map((item) => item.owner).filter(Boolean))])
const approvalPeople = computed(() => [...new Set(state.approvals.map((item) => item.owner).filter(Boolean))])
const reportPeople = computed(() => [...new Set(state.reports.map((item) => item.owner).filter(Boolean))])
const userPeople = computed(() => [...new Set(state.users.flatMap((item) => [item.name, item.manager]).filter(Boolean))])

function replaceItems(target, items) {
  target.splice(0, target.length, ...(items || []))
}

function priorityLabel(value) {
  return {
    low: 'پایین',
    medium: 'متوسط',
    high: 'بالا',
    critical: 'بحرانی',
  }[value] || 'متوسط'
}

function departmentLabel(value) {
  return {
    it: 'فناوری اطلاعات',
    finance: 'امور مالی',
    hr: 'منابع انسانی',
    ops: 'عملیات',
    marketing: 'بازاریابی',
  }[value] || 'بدون واحد'
}

function managerLabel(value) {
  return {
    'sara-ahmadi': 'سارا احمدی',
    'hamid-rezaei': 'حمید رضایی',
    'navid-farhadi': 'نوید فرهادی',
    'niloufar-farahmand': 'نیلوفر فرهمند',
  }[value] || 'تعیین نشده'
}

function resetRequestForm() {
  state.requestForm.title = ''
  state.requestForm.description = ''
  state.requestForm.department = ''
  state.requestForm.manager = ''
  state.requestForm.priority = 'medium'
  state.requestForm.deadline = ''
  state.requestForm.attachments = []
  state.composerStep = 1
}

function updatePageFilter(page, key, value) {
  if (!state.filters[page]) return
  state.filters[page][key] = value
}

function resetPageFilters(page) {
  if (!state.filters[page]) return
  state.filters[page].query = ''
  state.filters[page].person = ''
  state.filters[page].startDate = ''
  state.filters[page].endDate = ''
}

function hydrateBootstrap(payload) {
  if (!payload) return

  Object.assign(state.currentUser, {
    name: payload.currentUser?.name || state.currentUser.name,
    role: payload.currentUser?.role || state.currentUser.role,
    department: payload.currentUser?.department || state.currentUser.department,
    avatar: payload.currentUser?.avatar || state.currentUser.avatar,
    email: payload.currentUser?.email || state.currentUser.email,
  })

  replaceItems(state.stats, payload.stats)
  replaceItems(state.chartData, payload.chartData)
  replaceItems(state.pipeline, payload.pipeline)
  replaceItems(state.requests, payload.requests)
  replaceItems(state.expenses, payload.expenses)
  replaceItems(state.approvals, payload.approvals)
  replaceItems(state.users, payload.users)
  replaceItems(state.reports, payload.reports)
  replaceItems(state.activities, payload.activities)
  replaceItems(state.insights, payload.insights)
  replaceItems(state.expenseSummary, payload.expenseSummary)
  replaceItems(state.settingsCards, payload.settingsCards)

  state.approvalMetrics.pending = payload.approvalMetrics?.pending ?? state.approvalMetrics.pending
  state.approvalMetrics.approved = payload.approvalMetrics?.approved ?? state.approvalMetrics.approved
  state.approvalMetrics.rejected = payload.approvalMetrics?.rejected ?? state.approvalMetrics.rejected

  if (state.requests.length) state.selectedRequestId = state.requests[0].id
  if (state.approvals.length) state.selectedApprovalId = state.approvals[0].id
}

async function authorizedFetch(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.headers || {}),
      ...(state.authToken ? { Authorization: `Bearer ${state.authToken}` } : {}),
    },
  })

  if (!response.ok) throw new Error(`Request failed: ${response.status}`)
  return response
}

async function loadBootstrapData() {
  if (state.bootstrapLoaded) return
  try {
    const loginResponse = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(DEMO_CREDENTIALS),
    })

    if (!loginResponse.ok) throw new Error(`Login failed: ${loginResponse.status}`)

    const loginData = await loginResponse.json()
    state.authToken = loginData.access_token

    const bootstrapResponse = await authorizedFetch('/bootstrap')
    const bootstrapData = await bootstrapResponse.json()
    hydrateBootstrap(bootstrapData)
    state.bootstrapLoaded = true
  } catch (error) {
    console.error('Backend bootstrap failed, keeping empty state.', error)
  }
}

async function ensureRequestDetail(requestId) {
  if (!requestId || requestDetailState.items[requestId] || !state.authToken) return

  requestDetailState.loading = true
  try {
    const response = await authorizedFetch(`/requests/${requestId}`)
    const payload = await response.json()
    requestDetailState.items[requestId] = payload
  } catch (error) {
    console.error('Unable to load request detail.', error)
  } finally {
    requestDetailState.loading = false
  }
}

async function approveSelectedDocument() {
  if (!selectedApproval.value || !state.authToken) return
  try {
    await authorizedFetch(`/approvals/${selectedApproval.value.id}/approve`, { method: 'POST' })
    await refreshApprovals()
  } catch (error) {
    console.error('Approve action failed.', error)
  }
}

async function rejectSelectedDocument(reason = '') {
  if (!selectedApproval.value || !state.authToken) return
  try {
    await authorizedFetch(`/approvals/${selectedApproval.value.id}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason }),
    })
    await refreshApprovals()
  } catch (error) {
    console.error('Reject action failed.', error)
  }
}

async function refreshApprovals() {
  const approvalsResponse = await authorizedFetch('/approvals')
  const metricsResponse = await authorizedFetch('/approvals/metrics')
  replaceItems(state.approvals, await approvalsResponse.json())
  Object.assign(state.approvalMetrics, await metricsResponse.json())
}

function openRequestDetail(id) {
  state.selectedRequestId = id
  modalState.requestDetail = true
  void ensureRequestDetail(id)
}

function closeRequestDetail() {
  modalState.requestDetail = false
}

function openApprovalDetail(id) {
  state.selectedApprovalId = id
  modalState.approvalDetail = true
}

function closeApprovalDetail() {
  modalState.approvalDetail = false
}

function openComposer() {
  modalState.composer = true
}

function closeComposer() {
  modalState.composer = false
  resetRequestForm()
}

function toggleSidebar() {
  state.mobileMenuOpen = !state.mobileMenuOpen
}

function nextComposerStep() {
  if (state.composerStep < 3) state.composerStep += 1
}

function prevComposerStep() {
  if (state.composerStep > 1) state.composerStep -= 1
}

function setRequestFiles(files) {
  state.requestForm.attachments = Array.from(files || [])
}

function removeAttachment(index) {
  state.requestForm.attachments = state.requestForm.attachments.filter((_, itemIndex) => itemIndex !== index)
}

async function submitRequest() {
  const deadlineIso = state.requestForm.deadline ? jalaliToIso(state.requestForm.deadline) : ''
  const fallbackRequest = {
    id: 'REQ-LOCAL',
    title: state.requestForm.title || '',
    owner: state.currentUser.name,
    manager: managerLabel(state.requestForm.manager),
    priority: priorityLabel(state.requestForm.priority),
    status: 'ارسال شده',
    department: departmentLabel(state.requestForm.department),
    deadline: state.requestForm.deadline || '',
    deadlineIso,
    description: state.requestForm.description || '',
  }

  state.requestSubmitting = true
  try {
    if (!state.authToken) throw new Error('Missing token')

    const formData = new FormData()
    formData.append('title', state.requestForm.title)
    formData.append('description', state.requestForm.description)
    formData.append('department', state.requestForm.department)
    formData.append('manager', state.requestForm.manager)
    formData.append('priority', state.requestForm.priority)
    if (state.requestForm.deadline) formData.append('deadline', state.requestForm.deadline)
    state.requestForm.attachments.forEach((file) => {
      formData.append('attachments', file)
    })

    const response = await authorizedFetch('/requests', {
      method: 'POST',
      body: formData,
    })
    const createdRequest = await response.json()
    state.requests.unshift(createdRequest)
    state.selectedRequestId = createdRequest.id
  } catch (error) {
    console.error('Backend request submit failed, using local fallback.', error)
    state.requests.unshift(fallbackRequest)
    state.selectedRequestId = fallbackRequest.id
  } finally {
    state.requestSubmitting = false
    modalState.composer = false
    resetRequestForm()
  }
}

let singleton

export function useWorkflowHub() {
  const router = useRouter()

  if (singleton) return singleton

  function navigateTo(path) {
    router.push(path)
    state.mobileMenuOpen = false
  }

  singleton = {
    state,
    modalState,
    requestDetailState,
    selectedRequest,
    selectedApproval,
    selectedRequestTimeline,
    filteredRequests,
    filteredExpenses,
    filteredApprovals,
    filteredReports,
    filteredUsers,
    requestCompletion,
    approvalMetricCards,
    requestPeople,
    expensePeople,
    approvalPeople,
    reportPeople,
    userPeople,
    priorityLabel,
    departmentLabel,
    managerLabel,
    updatePageFilter,
    resetPageFilters,
    loadBootstrapData,
    navigateTo,
    openRequestDetail,
    closeRequestDetail,
    openApprovalDetail,
    closeApprovalDetail,
    openComposer,
    closeComposer,
    nextComposerStep,
    prevComposerStep,
    toggleSidebar,
    setRequestFiles,
    removeAttachment,
    submitRequest,
    approveSelectedDocument,
    rejectSelectedDocument,
  }

  return singleton
}
