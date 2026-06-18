import { computed, reactive } from 'vue'
import { useRouter } from 'vue-router'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const DEMO_CREDENTIALS = {
  email: 'admin@workflow.local',
  password: 'Admin123!',
}

const state = reactive({
  authToken: '',
  bootstrapLoaded: false,
  searchQuery: '',
  mobileMenuOpen: false,
  composerStep: 1,
  requestSubmitting: false,
  selectedRequestId: 'REQ-2408',
  selectedApprovalId: 'DOC-2841',
  currentUser: {
    name: 'آرمان کریمی',
    role: 'مدیر ارشد عملیات',
    department: 'ستاد مرکزی',
    avatar: 'AK',
    email: 'admin@workflow.local',
  },
  stats: [
    { id: 'active', label: 'درخواست‌های فعال', value: '128', detail: '+18% نسبت به هفته قبل', tone: 'primary', icon: 'assignment' },
    { id: 'pending', label: 'تأییدهای باز', value: '23', detail: '6 مورد اولویت‌دار', tone: 'warning', icon: 'pending_actions' },
    { id: 'monthly', label: 'هزینه ماه', value: '18.4B', detail: '72% بودجه مصرف شده', tone: 'success', icon: 'payments' },
    { id: 'approved', label: 'اسناد تأیید شده', value: '412', detail: 'میانگین تأیید 18 ساعت', tone: 'neutral', icon: 'fact_check' },
  ],
  chartData: [
    { day: 'شنبه', value: 48 },
    { day: 'یکشنبه', value: 62 },
    { day: 'دوشنبه', value: 54 },
    { day: 'سه‌شنبه', value: 76 },
    { day: 'چهارشنبه', value: 58 },
    { day: 'پنج‌شنبه', value: 71 },
    { day: 'جمعه', value: 44 },
  ],
  pipeline: [
    { label: 'پیش‌نویس', count: 12 },
    { label: 'ارسال شده', count: 34 },
    { label: 'در بررسی', count: 18 },
    { label: 'تأیید شده', count: 67 },
    { label: 'رد شده', count: 5 },
  ],
  requests: [
    {
      id: 'REQ-2408',
      title: 'نوسازی زیرساخت شبکه کارخانه',
      owner: 'مهدی امیری',
      manager: 'سارا احمدی',
      priority: 'بحرانی',
      status: 'ارسال شده',
      department: 'فناوری اطلاعات',
      deadline: '1405/04/02',
      description: 'تعویض سوئیچ‌های لایه توزیع و آماده‌سازی برای توسعه خط تولید.',
    },
    {
      id: 'REQ-2401',
      title: 'افزایش بودجه کمپین تابستان',
      owner: 'الهام رستمی',
      manager: 'نوید فرهادی',
      priority: 'بالا',
      status: 'در بررسی',
      department: 'بازاریابی',
      deadline: '1405/03/31',
      description: 'درخواست افزایش بودجه تبلیغات عملکردی برای رشد لید ورودی.',
    },
    {
      id: 'REQ-2389',
      title: 'تمدید قرارداد تأمین قطعات',
      owner: 'محمد آزاد',
      manager: 'حمید رضایی',
      priority: 'متوسط',
      status: 'تأیید شده',
      department: 'تدارکات',
      deadline: '1405/04/06',
      description: 'تمدید قرارداد تأمین قطعات یدکی همراه با بازبینی SLA و زمان تحویل.',
    },
  ],
  approvals: [
    {
      id: 'DOC-2841',
      title: 'قرارداد توسعه ERP',
      owner: 'سارا فلاح',
      type: 'قرارداد',
      status: 'در انتظار تأیید',
      department: 'فناوری اطلاعات',
      uploadedAt: '1405/03/27',
      risk: 'بالا',
      summary: 'فاز دوم استقرار سامانه مالی و انبار برای سه سایت عملیاتی.',
    },
    {
      id: 'DOC-2816',
      title: 'فاکتور تجهیزات دیتاسنتر',
      owner: 'رامین شایان',
      type: 'فاکتور',
      status: 'در انتظار تأیید',
      department: 'زیرساخت',
      uploadedAt: '1405/03/25',
      risk: 'متوسط',
      summary: 'شامل رک، UPS و سوئیچ‌های توزیع برای سایت پشتیبان.',
    },
    {
      id: 'DOC-2764',
      title: 'الحاقیه خدمات منابع انسانی',
      owner: 'نیلوفر فرهمند',
      type: 'الحاقیه',
      status: 'تأیید شده',
      department: 'منابع انسانی',
      uploadedAt: '1405/03/21',
      risk: 'پایین',
      summary: 'افزودن بند SLA برای پشتیبانی شیفت شب و آموزش پرسنل جدید.',
    },
  ],
  expenses: [
    { id: 'EXP-91', title: 'زیرساخت ابری', amount: '2.4B', category: 'فناوری', owner: 'رامین شایان', status: 'تأیید شده', progress: 82 },
    { id: 'EXP-88', title: 'حمل و نقل بین شهری', amount: '860M', category: 'عملیات', owner: 'نفیسه کاظمی', status: 'در بررسی', progress: 54 },
    { id: 'EXP-84', title: 'تجهیزات خط تولید', amount: '3.1B', category: 'سرمایه‌ای', owner: 'علی رضایی', status: 'نیازمند سند', progress: 91 },
    { id: 'EXP-80', title: 'تبلیغات دیجیتال', amount: '1.3B', category: 'بازاریابی', owner: 'الهام رستمی', status: 'تأیید شده', progress: 68 },
  ],
  users: [
    { name: 'سارا احمدی', role: 'مدیر فنی', department: 'فناوری اطلاعات', kpi: 'زمان پاسخ‌گویی 4 ساعت' },
    { name: 'حمید رضایی', role: 'مدیر مالی', department: 'امور مالی', kpi: '96% تأیید به‌موقع' },
    { name: 'نفیسه کاظمی', role: 'کارشناس عملیات', department: 'عملیات', kpi: '18 درخواست فعال' },
  ],
  reports: [
    { title: 'گزارش درخواست‌ها', description: 'تحلیل بر اساس کاربر، مدیر، واحد و بازه زمانی', export: 'PDF / Excel / CSV' },
    { title: 'گزارش هزینه‌ها', description: 'ماهانه، فصلی و سالانه با تفکیک دسته‌بندی', export: 'Excel / CSV' },
    { title: 'گزارش اسناد', description: 'اسناد در انتظار، تأیید شده، رد شده و آرشیو', export: 'PDF / Excel' },
  ],
  activities: [
    { id: 1, user: 'سارا علوی', action: 'یک درخواست ثبت کرد', detail: 'خرید تجهیزات سخت‌افزاری تیم فنی', time: '10 دقیقه پیش', icon: 'add_task' },
    { id: 2, user: 'مدیر مالی', action: 'سندی را تأیید کرد', detail: 'گزارش هزینه‌های سفر نمایشگاه دبی', time: '1 ساعت پیش', icon: 'verified' },
    { id: 3, user: 'علی رضایی', action: 'پیامی ارسال کرد', detail: 'لطفاً فاکتورهای مربوط به پروژه آلفا را بررسی کنید.', time: '3 ساعت پیش', icon: 'chat' },
  ],
  insights: [
    'هزینه‌های فناوری این ماه رشد داشته و فشار اصلی روی تأییدهای زیرساخت متمرکز است.',
    'واحد مالی بیشترین حجم گردش کار را دارد و زمان پاسخ مدیران بهتر شده است.',
    'چهار سند با اولویت بالا امروز نیازمند اقدام نهایی هستند.',
  ],
  expenseSummary: [
    { label: 'امروز', value: '420M' },
    { label: 'این هفته', value: '1.8B' },
    { label: 'این ماه', value: '18.4B' },
    { label: 'امسال', value: '146B' },
  ],
  approvalMetrics: {
    pending: 12,
    approved: 145,
    rejected: 8,
  },
  settingsCards: [
    { title: 'امنیت', description: 'احراز هویت، نشست‌ها و کنترل دسترسی مبتنی بر نقش' },
    { title: 'برندینگ', description: 'رنگ سازمان، فونت و هویت بصری پرتال سازمانی' },
    { title: 'اعلان‌ها', description: 'اعلان درون‌برنامه‌ای، ایمیل و اولویت پیام‌ها' },
    { title: 'یکپارچه‌سازی', description: 'آماده اتصال به ERP، CRM و سرویس اسناد' },
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

const filteredRequests = computed(() => {
  const query = state.searchQuery.trim().toLowerCase()
  if (!query) return state.requests
  return state.requests.filter((item) =>
    [item.title, item.owner, item.manager, item.department, item.status, item.id]
      .join(' ')
      .toLowerCase()
      .includes(query),
  )
})

const filteredExpenses = computed(() => {
  const query = state.searchQuery.trim().toLowerCase()
  if (!query) return state.expenses
  return state.expenses.filter((item) =>
    [item.title, item.category, item.owner, item.status, item.id].join(' ').toLowerCase().includes(query),
  )
})

const filteredApprovals = computed(() => {
  const query = state.searchQuery.trim().toLowerCase()
  if (!query) return state.approvals
  return state.approvals.filter((item) =>
    [item.title, item.type, item.owner, item.department, item.status, item.id].join(' ').toLowerCase().includes(query),
  )
})

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

  if (state.requests.length) {
    state.selectedRequestId = state.requests[0].id
  }

  if (state.approvals.length) {
    state.selectedApprovalId = state.approvals[0].id
  }
}

async function authorizedFetch(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.headers || {}),
      ...(state.authToken ? { Authorization: `Bearer ${state.authToken}` } : {}),
    },
  })

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`)
  }

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

    if (!loginResponse.ok) {
      throw new Error(`Login failed: ${loginResponse.status}`)
    }

    const loginData = await loginResponse.json()
    state.authToken = loginData.access_token

    const bootstrapResponse = await authorizedFetch('/bootstrap')
    const bootstrapData = await bootstrapResponse.json()
    hydrateBootstrap(bootstrapData)
    state.bootstrapLoaded = true
  } catch (error) {
    console.error('Backend bootstrap failed, using fallback mock data.', error)
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

async function rejectSelectedDocument(reason = 'نیازمند بازبینی') {
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
  const fallbackRequest = {
    id: `REQ-${2409 + state.requests.length}`,
    title: state.requestForm.title || 'درخواست جدید',
    owner: state.currentUser.name,
    manager: managerLabel(state.requestForm.manager),
    priority: priorityLabel(state.requestForm.priority),
    status: 'ارسال شده',
    department: departmentLabel(state.requestForm.department),
    deadline: state.requestForm.deadline || 'بدون موعد',
    description: state.requestForm.description || 'توضیحی ثبت نشده است.',
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
    if (state.requestForm.deadline) {
      formData.append('deadline', state.requestForm.deadline)
    }
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
    requestCompletion,
    approvalMetricCards,
    priorityLabel,
    departmentLabel,
    managerLabel,
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
