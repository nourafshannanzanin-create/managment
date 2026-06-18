<script setup>
import { computed, reactive, ref } from 'vue'

const activeView = ref('dashboard')
const searchQuery = ref('')
const currentStep = ref(1)
const previewMode = ref(false)
const mobileMenuOpen = ref(false)
const selectedRequestId = ref('REQ-2408')
const selectedApprovalId = ref('DOC-2841')

const currentUser = reactive({
  name: 'آرمان کریمی',
  role: 'مدیر ارشد عملیات',
  department: 'ستاد مرکزی',
  avatar: 'AK'
})

const stats = [
  { id: 'active', label: 'درخواست های فعال', value: '128', detail: '+18% نسبت به هفته قبل', tone: 'primary', icon: 'assignment' },
  { id: 'pending', label: 'تاییدات در انتظار', value: '23', detail: '6 مورد نیازمند اقدام فوری', tone: 'warning', icon: 'pending_actions' },
  { id: 'monthly', label: 'هزینه های ماه', value: '18.4B', detail: 'بودجه مصرف شده 72%', tone: 'secondary', icon: 'payments' },
  { id: 'approved', label: 'اسناد تایید شده', value: '412', detail: 'میانگین زمان تایید 18 ساعت', tone: 'success', icon: 'fact_check' }
]

const chartData = [
  { day: 'شنبه', value: 48 },
  { day: 'یکشنبه', value: 62 },
  { day: 'دوشنبه', value: 54 },
  { day: 'سه شنبه', value: 76 },
  { day: 'چهارشنبه', value: 58 },
  { day: 'پنج شنبه', value: 71 },
  { day: 'جمعه', value: 44 }
]

const pipeline = [
  { label: 'پیش نویس', count: 12 },
  { label: 'ارسال شده', count: 34 },
  { label: 'در بررسی', count: 18 },
  { label: 'تایید شده', count: 67 },
  { label: 'رد شده', count: 5 }
]

const requests = reactive([
  {
    id: 'REQ-2408',
    title: 'نوسازی زیرساخت شبکه کارخانه',
    owner: 'مهدی امیری',
    manager: 'سارا احمدی',
    priority: 'بحرانی',
    status: 'در بررسی',
    department: 'فناوری اطلاعات',
    deadline: '1405/04/02',
    description: 'تعویض سوییچ های لایه توزیع، بهبود افزونگی و آماده سازی برای گسترش خط تولید.'
  },
  {
    id: 'REQ-2401',
    title: 'افزایش بودجه کمپین تابستان',
    owner: 'الهام رستمی',
    manager: 'نوید فرهادی',
    priority: 'بالا',
    status: 'نیازمند تایید',
    department: 'بازاریابی',
    deadline: '1405/03/31',
    description: 'درخواست افزایش بودجه تبلیغات عملکردی برای رشد لید ورودی و پوشش رسانه ای.'
  },
  {
    id: 'REQ-2389',
    title: 'تمدید قرارداد تامین قطعات',
    owner: 'محمد آزاد',
    manager: 'حمید رضایی',
    priority: 'متوسط',
    status: 'تایید شده',
    department: 'تدارکات',
    deadline: '1405/04/06',
    description: 'تمدید قرارداد تامین قطعات یدکی به همراه بازبینی SLA و زمان تحویل.'
  }
])

const expenses = reactive([
  { id: 'EXP-91', title: 'زیرساخت ابری', amount: '2.4B', category: 'فناوری', owner: 'رامین شایان', status: 'تایید شده', progress: 82 },
  { id: 'EXP-88', title: 'حمل و نقل بین شهری', amount: '860M', category: 'عملیات', owner: 'نفیسه کاظمی', status: 'در بررسی', progress: 54 },
  { id: 'EXP-84', title: 'تجهیزات خط تولید', amount: '3.1B', category: 'سرمایه ای', owner: 'علی رضایی', status: 'نیازمند سند', progress: 91 },
  { id: 'EXP-80', title: 'تبلیغات دیجیتال', amount: '1.3B', category: 'بازاریابی', owner: 'الهام رستمی', status: 'تایید شده', progress: 68 }
])

const approvals = reactive([
  {
    id: 'DOC-2841',
    title: 'قرارداد توسعه ERP',
    owner: 'سارا فلاح',
    type: 'قرارداد',
    status: 'در انتظار امضا',
    department: 'فناوری اطلاعات',
    uploadedAt: '1405/03/27',
    risk: 'بالا',
    summary: 'فاز دوم استقرار سامانه مالی و انبار برای سه سایت عملیاتی نیازمند تایید نهایی است.',
    actions: ['مشاهده', 'تایید', 'رد']
  },
  {
    id: 'DOC-2816',
    title: 'فاکتور تجهیزات دیتاسنتر',
    owner: 'رامین شایان',
    type: 'فاکتور',
    status: 'در انتظار تایید',
    department: 'زیرساخت',
    uploadedAt: '1405/03/25',
    risk: 'متوسط',
    summary: 'شامل رک، UPS و سوییچ های توزیع برای سایت پشتیبان.'
  },
  {
    id: 'DOC-2764',
    title: 'الحاقیه خدمات منابع انسانی',
    owner: 'نیلوفر فرهمند',
    type: 'الحاقیه',
    status: 'تایید شده',
    department: 'منابع انسانی',
    uploadedAt: '1405/03/21',
    risk: 'پایین',
    summary: 'افزودن بند SLA برای پشتیبانی شیفت شب و آموزش پرسنل جدید.'
  }
])

const users = [
  { name: 'سارا احمدی', role: 'مدیر فنی', department: 'فناوری اطلاعات', kpi: 'زمان پاسخگویی 4h' },
  { name: 'حمید رضایی', role: 'مدیر مالی', department: 'امور مالی', kpi: '96% تایید به موقع' },
  { name: 'نفیسه کاظمی', role: 'کارشناس عملیات', department: 'عملیات', kpi: '18 درخواست فعال' }
]

const reports = [
  { title: 'گزارش درخواست ها', description: 'تحلیل بر اساس کاربر، مدیر، واحد و بازه زمانی', export: 'PDF / Excel / CSV' },
  { title: 'گزارش هزینه ها', description: 'ماهانه، فصلی، سالانه و تفکیک دسته بندی', export: 'Excel / CSV' },
  { title: 'گزارش اسناد', description: 'در انتظار، تایید شده، رد شده و آرشیو', export: 'PDF / Excel' }
]

const activities = [
  { id: 1, user: 'سارا علوی', action: 'درخواست جدید ثبت کرد', detail: 'خرید تجهیزات سخت افزاری تیم فنی', time: '10 دقیقه پیش', icon: 'add_task' },
  { id: 2, user: 'مدیر مالی', action: 'سندی را تایید کرد', detail: 'گزارش هزینه های سفر نمایشگاه دبی', time: '1 ساعت پیش', icon: 'verified' },
  { id: 3, user: 'علی رضایی', action: 'پیامی ارسال کرد', detail: 'لطفا فاکتورهای مربوط به پروژه آلفا را بررسی کنید.', time: '3 ساعت پیش', icon: 'chat' }
]

const insights = [
  'هزینه های فناوری این ماه 12 درصد رشد داشته و بیشترین فشار روی تاییدهای زیرساخت متمرکز شده است.',
  'بیشترین درخواست ثبت شده مربوط به واحد مالی است و زمان پاسخ مدیران 8 درصد بهبود یافته است.',
  '4 سند با اولویت بحرانی امروز نیازمند اقدام نهایی هستند.'
]

const requestForm = reactive({
  title: '',
  description: '',
  department: '',
  manager: '',
  priority: 'medium',
  deadline: '',
  attachments: []
})

const navItems = [
  { id: 'dashboard', label: 'پیشخوان', icon: 'space_dashboard' },
  { id: 'requests', label: 'درخواست ها', icon: 'assignment' },
  { id: 'new-request', label: 'درخواست جدید', icon: 'edit_square' },
  { id: 'expenses', label: 'هزینه ها', icon: 'payments' },
  { id: 'approvals', label: 'تاییدات', icon: 'fact_check' },
  { id: 'reports', label: 'گزارشات', icon: 'monitoring' },
  { id: 'users', label: 'کاربران', icon: 'group' },
  { id: 'settings', label: 'تنظیمات', icon: 'settings' }
]

const mobileNavItems = computed(() => [
  navItems[0],
  navItems[1],
  navItems[3],
  navItems[4],
  { id: 'more', label: 'بیشتر', icon: 'more_horiz' }
])

const selectedRequest = computed(
  () => requests.find((item) => item.id === selectedRequestId.value) ?? requests[0]
)

const selectedApproval = computed(
  () => approvals.find((item) => item.id === selectedApprovalId.value) ?? approvals[0]
)

const filteredRequests = computed(() => {
  const query = searchQuery.value.trim()
  if (!query) return requests
  return requests.filter((item) =>
    [item.title, item.owner, item.manager, item.department, item.status, item.id]
      .join(' ')
      .includes(query)
  )
})

const completionPercent = computed(() => {
  const fields = [
    requestForm.title,
    requestForm.description,
    requestForm.department,
    requestForm.manager,
    requestForm.priority,
    requestForm.deadline
  ]

  const filled = fields.filter(Boolean).length
  return Math.round((filled / fields.length) * 100)
})

function setView(view) {
  activeView.value = view
  mobileMenuOpen.value = false
}

function nextStep() {
  if (currentStep.value < 3) currentStep.value += 1
}

function prevStep() {
  if (currentStep.value > 1) currentStep.value -= 1
}

function openPreview() {
  previewMode.value = true
}

function closePreview() {
  previewMode.value = false
}

function submitRequest() {
  requests.unshift({
    id: `REQ-${2409 + requests.length}`,
    title: requestForm.title || 'درخواست بدون عنوان',
    owner: currentUser.name,
    manager: requestForm.manager || 'تعیین نشده',
    priority: priorityLabel(requestForm.priority),
    status: 'ارسال شده',
    department: departmentLabel(requestForm.department),
    deadline: requestForm.deadline || 'بدون موعد',
    description: requestForm.description || 'توضیحی ثبت نشده است.'
  })

  resetRequestForm()
  activeView.value = 'requests'
  previewMode.value = false
}

function resetRequestForm() {
  currentStep.value = 1
  requestForm.title = ''
  requestForm.description = ''
  requestForm.department = ''
  requestForm.manager = ''
  requestForm.priority = 'medium'
  requestForm.deadline = ''
  requestForm.attachments = []
}

function onFileChange(event) {
  const files = Array.from(event.target.files || [])
  requestForm.attachments = [...requestForm.attachments, ...files]
}

function removeAttachment(index) {
  requestForm.attachments.splice(index, 1)
}

function departmentLabel(value) {
  return (
    {
      it: 'فناوری اطلاعات',
      finance: 'امور مالی',
      hr: 'منابع انسانی',
      ops: 'عملیات',
      marketing: 'بازاریابی'
    }[value] ?? value
  )
}

function managerLabel(value) {
  return (
    {
      'sara-ahmadi': 'سارا احمدی',
      'hamid-rezaei': 'حمید رضایی',
      'navid-farhadi': 'نوید فرهادی',
      'niloufar-farahmand': 'نیلوفر فرهمند'
    }[value] ?? value
  )
}

function priorityLabel(value) {
  return (
    {
      low: 'پایین',
      medium: 'متوسط',
      high: 'بالا',
      critical: 'بحرانی'
    }[value] ?? value
  )
}
</script>

<template>
  <div class="app-shell">
    <div class="ambient ambient-one"></div>
    <div class="ambient ambient-two"></div>

    <aside :class="['sidebar', mobileMenuOpen && 'is-open']">
      <div class="brand-card">
        <div class="brand-badge">WH</div>
        <div>
          <p class="eyebrow">Enterprise Workflow</p>
          <h1>Workflow Hub</h1>
        </div>
      </div>

      <nav class="nav-list">
        <button
          v-for="item in navItems"
          :key="item.id"
          :class="['nav-item', activeView === item.id && 'is-active']"
          @click="setView(item.id)"
        >
          <span class="material-symbols-outlined">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </button>
      </nav>

      <div class="profile-card">
        <div class="profile-avatar">{{ currentUser.avatar }}</div>
        <div>
          <strong>{{ currentUser.name }}</strong>
          <p>{{ currentUser.role }}</p>
          <small>{{ currentUser.department }}</small>
        </div>
      </div>
    </aside>

    <main class="content">
      <header class="topbar">
        <div class="topbar-copy">
          <p class="eyebrow">سامانه مدیریت درخواست ها، هزینه ها و تایید اسناد</p>
          <h2>طراحی شده بر اساس ساختار پروژه شما و زبان بصری UI مرجع</h2>
        </div>

        <div class="topbar-actions">
          <label class="search-field">
            <span class="material-symbols-outlined">search</span>
            <input v-model="searchQuery" type="text" placeholder="جستجو در درخواست ها، اسناد و کاربران" />
          </label>

          <button class="ghost-btn mobile-only" @click="mobileMenuOpen = !mobileMenuOpen">
            <span class="material-symbols-outlined">menu</span>
          </button>

          <button class="ghost-btn">
            <span class="material-symbols-outlined">notifications</span>
          </button>

          <button class="primary-btn" @click="setView('new-request')">
            <span class="material-symbols-outlined">add</span>
            <span>درخواست جدید</span>
          </button>
        </div>
      </header>

      <section v-if="activeView === 'dashboard'" class="dashboard-grid">
        <article class="hero-panel">
          <div class="hero-copy">
            <p class="eyebrow">Executive Overview</p>
            <h3>کنترل کامل گردش کار سازمان با داشبوردی مدرن، حرفه ای و عملیاتی</h3>
            <p>
              وضعیت درخواست ها، روند هزینه ها، اسناد در انتظار تایید، گزارش های مدیریتی و فعالیت کاربران
              در یک تجربه یکپارچه، شفاف و بسیار نزدیک به UI مرجع.
            </p>

            <div class="hero-pills">
              <span>Real-time approvals</span>
              <span>Audit ready</span>
              <span>Role based access</span>
            </div>
          </div>

          <div class="hero-kpi">
            <div class="hero-score">
              <strong>98.2%</strong>
              <span>پایداری فرایندها</span>
            </div>
            <div class="hero-mini-grid">
              <div>
                <strong>18h</strong>
                <span>میانگین تایید</span>
              </div>
              <div>
                <strong>145</strong>
                <span>تایید شده</span>
              </div>
            </div>
          </div>
        </article>

        <div class="stats-grid">
          <article v-for="item in stats" :key="item.id" :class="['stat-card', `tone-${item.tone}`]">
            <div class="stat-icon">
              <span class="material-symbols-outlined">{{ item.icon }}</span>
            </div>
            <div>
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <small>{{ item.detail }}</small>
            </div>
          </article>
        </div>

        <section class="panel chart-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Expense Trend</p>
              <h3>روند هزینه های هفتگی</h3>
            </div>
            <button class="ghost-btn">
              <span class="material-symbols-outlined">more_horiz</span>
            </button>
          </div>

          <div class="chart-area">
            <div
              v-for="bar in chartData"
              :key="bar.day"
              class="chart-bar"
            >
              <span :style="{ height: `${bar.value}%` }"></span>
              <small>{{ bar.day }}</small>
            </div>
          </div>
        </section>

        <section class="panel insight-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Smart Insights</p>
              <h3>بینش هوشمند</h3>
            </div>
          </div>

          <div class="insight-list">
            <article v-for="item in insights" :key="item" class="insight-card">
              <span class="material-symbols-outlined">lightbulb</span>
              <p>{{ item }}</p>
            </article>
          </div>
        </section>

        <section class="panel pipeline-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Workflow Status</p>
              <h3>وضعیت گردش کار</h3>
            </div>
          </div>

          <div class="pipeline-grid">
            <article v-for="stage in pipeline" :key="stage.label" class="pipeline-card">
              <strong>{{ stage.count }}</strong>
              <span>{{ stage.label }}</span>
            </article>
          </div>
        </section>

        <section class="panel activities-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Activity Feed</p>
              <h3>فعالیت های اخیر</h3>
            </div>
          </div>

          <div class="activity-list">
            <article v-for="item in activities" :key="item.id" class="activity-card">
              <div class="activity-icon">
                <span class="material-symbols-outlined">{{ item.icon }}</span>
              </div>
              <div>
                <strong>{{ item.user }} {{ item.action }}</strong>
                <p>{{ item.detail }}</p>
                <small>{{ item.time }}</small>
              </div>
            </article>
          </div>
        </section>
      </section>

      <section v-if="activeView === 'requests'" class="module-grid">
        <article class="panel module-intro">
          <div>
            <p class="eyebrow">Requests Module</p>
            <h3>همه درخواست ها</h3>
            <p class="intro-copy">
              جستجوی سراسری، فیلتر پیشرفته، نمایش وضعیت، اولویت، مدیر مسئول و ددلاین هر درخواست.
            </p>
          </div>
          <button class="secondary-btn" @click="setView('new-request')">
            <span class="material-symbols-outlined">edit_square</span>
            <span>ثبت درخواست جدید</span>
          </button>
        </article>

        <section class="panel request-table-panel">
          <div class="filter-row">
            <span class="filter-chip">همه وضعیت ها</span>
            <span class="filter-chip">همه مدیران</span>
            <span class="filter-chip">همه واحدها</span>
            <span class="filter-chip">نمای جدول</span>
          </div>

          <div class="request-list">
            <article
              v-for="item in filteredRequests"
              :key="item.id"
              :class="['request-card', selectedRequestId === item.id && 'is-selected']"
              @click="selectedRequestId = item.id"
            >
              <div class="request-main">
                <strong>{{ item.title }}</strong>
                <p>{{ item.id }} | {{ item.owner }} | {{ item.department }}</p>
              </div>
              <div class="request-meta">
                <span class="pill">{{ item.priority }}</span>
                <span class="muted">{{ item.status }}</span>
                <small>{{ item.deadline }}</small>
              </div>
            </article>
          </div>
        </section>

        <aside class="panel detail-card">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Request Details</p>
              <h3>{{ selectedRequest.title }}</h3>
            </div>
          </div>

          <div class="detail-grid">
            <div>
              <span>ثبت کننده</span>
              <strong>{{ selectedRequest.owner }}</strong>
            </div>
            <div>
              <span>مدیر</span>
              <strong>{{ selectedRequest.manager }}</strong>
            </div>
            <div>
              <span>اولویت</span>
              <strong>{{ selectedRequest.priority }}</strong>
            </div>
            <div>
              <span>مهلت</span>
              <strong>{{ selectedRequest.deadline }}</strong>
            </div>
          </div>

          <p class="summary-copy">{{ selectedRequest.description }}</p>

          <div class="timeline-list">
            <div class="timeline-item">
              <span>1</span>
              <p>ثبت اولیه توسط کارمند</p>
            </div>
            <div class="timeline-item">
              <span>2</span>
              <p>ارجاع به مدیر مسئول</p>
            </div>
            <div class="timeline-item">
              <span>3</span>
              <p>بررسی و تصمیم نهایی</p>
            </div>
          </div>
        </aside>
      </section>

      <section v-if="activeView === 'new-request'" class="module-grid">
        <article class="panel form-shell">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Create Request</p>
              <h3>ثبت درخواست جدید</h3>
            </div>
            <div class="completion-badge">{{ completionPercent }}%</div>
          </div>

          <div class="stepper">
            <div :class="['step-item', currentStep >= 1 && 'is-done']">
              <span>1</span>
              <small>اطلاعات اولیه</small>
            </div>
            <div :class="['step-item', currentStep >= 2 && 'is-done']">
              <span>2</span>
              <small>گردش کاری</small>
            </div>
            <div :class="['step-item', currentStep >= 3 && 'is-done']">
              <span>3</span>
              <small>پیوست ها</small>
            </div>
          </div>

          <div v-if="currentStep === 1" class="form-grid">
            <label class="field-block span-2">
              <span>عنوان درخواست</span>
              <input v-model="requestForm.title" type="text" placeholder="مثلا: نوسازی سرورهای مرکزی" />
            </label>
            <label class="field-block">
              <span>دپارتمان</span>
              <select v-model="requestForm.department">
                <option value="">انتخاب کنید</option>
                <option value="it">فناوری اطلاعات</option>
                <option value="finance">امور مالی</option>
                <option value="hr">منابع انسانی</option>
                <option value="ops">عملیات</option>
                <option value="marketing">بازاریابی</option>
              </select>
            </label>
            <label class="field-block span-2">
              <span>توضیحات کامل</span>
              <textarea
                v-model="requestForm.description"
                rows="6"
                placeholder="جزئیات دقیق درخواست، هدف، تاثیر و نیازمندی ها را اینجا وارد کنید."
              ></textarea>
            </label>
          </div>

          <div v-else-if="currentStep === 2" class="form-grid">
            <label class="field-block">
              <span>مدیر تایید کننده</span>
              <select v-model="requestForm.manager">
                <option value="">انتخاب مدیر</option>
                <option value="sara-ahmadi">سارا احمدی</option>
                <option value="hamid-rezaei">حمید رضایی</option>
                <option value="navid-farhadi">نوید فرهادی</option>
                <option value="niloufar-farahmand">نیلوفر فرهمند</option>
              </select>
            </label>
            <label class="field-block">
              <span>مهلت انجام</span>
              <input v-model="requestForm.deadline" type="date" />
            </label>

            <div class="priority-grid span-2">
              <button
                :class="['priority-card', requestForm.priority === 'low' && 'is-active']"
                @click="requestForm.priority = 'low'"
              >
                <span class="material-symbols-outlined">low_priority</span>
                <strong>پایین</strong>
              </button>
              <button
                :class="['priority-card', requestForm.priority === 'medium' && 'is-active']"
                @click="requestForm.priority = 'medium'"
              >
                <span class="material-symbols-outlined">equalizer</span>
                <strong>متوسط</strong>
              </button>
              <button
                :class="['priority-card', requestForm.priority === 'high' && 'is-active warning']"
                @click="requestForm.priority = 'high'"
              >
                <span class="material-symbols-outlined">priority_high</span>
                <strong>بالا</strong>
              </button>
              <button
                :class="['priority-card', requestForm.priority === 'critical' && 'is-active danger']"
                @click="requestForm.priority = 'critical'"
              >
                <span class="material-symbols-outlined">warning</span>
                <strong>بحرانی</strong>
              </button>
            </div>
          </div>

          <div v-else class="form-grid">
            <label class="upload-zone span-2">
              <input type="file" multiple @change="onFileChange" />
              <span class="material-symbols-outlined">cloud_upload</span>
              <strong>فایل ها را اینجا بکشید یا انتخاب کنید</strong>
              <small>پشتیبانی از PDF, Word, Excel, JPG, PNG</small>
            </label>

            <div class="attachment-list span-2" v-if="requestForm.attachments.length">
              <article
                v-for="(file, index) in requestForm.attachments"
                :key="`${file.name}-${index}`"
                class="attachment-card"
              >
                <div>
                  <strong>{{ file.name }}</strong>
                  <p>{{ Math.round(file.size / 1024) }} KB</p>
                </div>
                <button class="ghost-btn" @click="removeAttachment(index)">
                  <span class="material-symbols-outlined">delete</span>
                </button>
              </article>
            </div>
          </div>

          <div class="form-actions">
            <button v-if="currentStep > 1" class="secondary-btn" @click="prevStep">مرحله قبل</button>
            <div class="spacer"></div>
            <button v-if="currentStep < 3" class="primary-btn" @click="nextStep">مرحله بعد</button>
            <template v-else>
              <button class="secondary-btn" @click="openPreview">پیش نمایش</button>
              <button class="primary-btn" @click="submitRequest">ثبت و ارسال</button>
            </template>
          </div>
        </article>

        <aside class="panel preview-side">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Preview</p>
              <h3>نمای خلاصه درخواست</h3>
            </div>
          </div>

          <div class="preview-stack">
            <div class="preview-card">
              <span>عنوان</span>
              <strong>{{ requestForm.title || '---' }}</strong>
            </div>
            <div class="preview-card">
              <span>دپارتمان</span>
              <strong>{{ departmentLabel(requestForm.department) || '---' }}</strong>
            </div>
            <div class="preview-card">
              <span>مدیر</span>
              <strong>{{ managerLabel(requestForm.manager) || '---' }}</strong>
            </div>
            <div class="preview-card">
              <span>اولویت</span>
              <strong>{{ priorityLabel(requestForm.priority) }}</strong>
            </div>
            <div class="preview-card span-full">
              <span>توضیحات</span>
              <p>{{ requestForm.description || 'توضیحی ثبت نشده است.' }}</p>
            </div>
          </div>
        </aside>
      </section>

      <section v-if="activeView === 'expenses'" class="module-grid">
        <article class="panel module-intro">
          <div>
            <p class="eyebrow">Expenses Module</p>
            <h3>داشبورد هزینه ها</h3>
            <p class="intro-copy">نمای مالی روزانه، هفتگی، ماهانه و سالانه به همراه ریز هزینه ها و تحلیل دسته بندی.</p>
          </div>
        </article>

        <section class="panel cards-grid expense-summary">
          <article class="mini-kpi">
            <span>امروز</span>
            <strong>420M</strong>
          </article>
          <article class="mini-kpi">
            <span>این هفته</span>
            <strong>1.8B</strong>
          </article>
          <article class="mini-kpi">
            <span>این ماه</span>
            <strong>18.4B</strong>
          </article>
          <article class="mini-kpi">
            <span>امسال</span>
            <strong>146B</strong>
          </article>
        </section>

        <section class="panel span-2">
          <div class="expense-list">
            <article v-for="item in expenses" :key="item.id" class="expense-card">
              <div class="expense-head">
                <div>
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.category }} | {{ item.owner }}</p>
                </div>
                <span class="amount-pill">{{ item.amount }}</span>
              </div>
              <div class="progress-track">
                <span :style="{ width: `${item.progress}%` }"></span>
              </div>
              <small>{{ item.status }}</small>
            </article>
          </div>
        </section>
      </section>

      <section v-if="activeView === 'approvals'" class="module-grid approvals-layout">
        <section class="panel approvals-list-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Approval Center</p>
              <h3>صف تایید اسناد</h3>
            </div>
          </div>

          <div class="approval-list">
            <button
              v-for="item in approvals"
              :key="item.id"
              :class="['approval-card', selectedApprovalId === item.id && 'is-selected']"
              @click="selectedApprovalId = item.id"
            >
              <div class="approval-main">
                <strong>{{ item.title }}</strong>
                <p>{{ item.type }} | {{ item.department }}</p>
              </div>
              <div class="approval-meta">
                <span class="pill">{{ item.status }}</span>
                <small>ریسک {{ item.risk }}</small>
              </div>
            </button>
          </div>
        </section>

        <section class="panel approval-detail-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Document Details</p>
              <h3>{{ selectedApproval.title }}</h3>
            </div>
            <span class="muted">{{ selectedApproval.uploadedAt }}</span>
          </div>

          <div class="detail-grid">
            <div>
              <span>مالک</span>
              <strong>{{ selectedApproval.owner }}</strong>
            </div>
            <div>
              <span>نوع سند</span>
              <strong>{{ selectedApproval.type }}</strong>
            </div>
            <div>
              <span>وضعیت</span>
              <strong>{{ selectedApproval.status }}</strong>
            </div>
            <div>
              <span>واحد</span>
              <strong>{{ selectedApproval.department }}</strong>
            </div>
          </div>

          <p class="summary-copy">{{ selectedApproval.summary }}</p>

          <div class="viewer-surface">
            <span class="material-symbols-outlined">description</span>
            <div>
              <strong>پیش نمایش سند</strong>
              <p>PDF Viewer / Image Viewer / Office Viewer</p>
            </div>
          </div>

          <div class="action-row">
            <button class="ghost-btn action-btn">
              <span class="material-symbols-outlined">visibility</span>
              <span>مشاهده</span>
            </button>
            <button class="primary-btn action-btn">
              <span class="material-symbols-outlined">check_circle</span>
              <span>تایید</span>
            </button>
            <button class="danger-btn action-btn">
              <span class="material-symbols-outlined">cancel</span>
              <span>رد</span>
            </button>
          </div>
        </section>

        <aside class="panel quick-metrics-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Metrics</p>
              <h3>آمار تاییدات</h3>
            </div>
          </div>

          <div class="metric-stack">
            <article class="metric-card">
              <strong>12</strong>
              <span>صف انتظار</span>
            </article>
            <article class="metric-card success">
              <strong>145</strong>
              <span>تایید شده</span>
            </article>
            <article class="metric-card danger">
              <strong>8</strong>
              <span>رد شده</span>
            </article>
          </div>
        </aside>
      </section>

      <section v-if="activeView === 'reports'" class="module-grid">
        <article class="panel module-intro span-2">
          <div>
            <p class="eyebrow">Reports Center</p>
            <h3>گزارشات مدیریتی</h3>
            <p class="intro-copy">خروجی های PDF، Excel و CSV برای درخواست ها، هزینه ها و اسناد.</p>
          </div>
        </article>

        <article v-for="item in reports" :key="item.title" class="panel report-card">
          <strong>{{ item.title }}</strong>
          <p>{{ item.description }}</p>
          <small>{{ item.export }}</small>
        </article>
      </section>

      <section v-if="activeView === 'users'" class="module-grid">
        <article class="panel module-intro span-2">
          <div>
            <p class="eyebrow">Users Module</p>
            <h3>مدیریت کاربران و نقش ها</h3>
            <p class="intro-copy">نمای کارکنان، مدیران، واحدها، نقش ها و فعالیت های ثبت شده.</p>
          </div>
        </article>

        <article v-for="item in users" :key="item.name" class="panel user-card">
          <div class="user-avatar">{{ item.name.slice(0, 1) }}</div>
          <div>
            <strong>{{ item.name }}</strong>
            <p>{{ item.role }} | {{ item.department }}</p>
            <small>{{ item.kpi }}</small>
          </div>
        </article>
      </section>

      <section v-if="activeView === 'settings'" class="module-grid">
        <article class="panel module-intro span-2">
          <div>
            <p class="eyebrow">Settings</p>
            <h3>تنظیمات سازمان</h3>
            <p class="intro-copy">برندینگ، امنیت، اعلان ها، نشست ها و محدودیت های دسترسی.</p>
          </div>
        </article>

        <article class="panel setting-card">
          <strong>امنیت</strong>
          <p>احراز هویت دو مرحله ای، مدیریت نشست ها، لاگ فعالیت و Role Based Access Control</p>
        </article>
        <article class="panel setting-card">
          <strong>برندینگ</strong>
          <p>رنگ سازمان، فونت، لوگو و هویت بصری پورتال سازمانی</p>
        </article>
        <article class="panel setting-card">
          <strong>اعلان ها</strong>
          <p>اعلان درون برنامه ای، ایمیل، پوش و تنظیمات اولویت پیام ها</p>
        </article>
        <article class="panel setting-card">
          <strong>یکپارچه سازی</strong>
          <p>ERP، CRM، انبار، حسابداری و سرویس ذخیره سازی اسناد</p>
        </article>
      </section>
    </main>

    <nav class="mobile-nav">
      <button
        v-for="item in mobileNavItems"
        :key="item.id"
        :class="['mobile-nav-item', activeView === item.id && 'is-active']"
        @click="item.id === 'more' ? (mobileMenuOpen = !mobileMenuOpen) : setView(item.id)"
      >
        <span class="material-symbols-outlined">{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </button>
    </nav>

    <div v-if="previewMode" class="modal-backdrop" @click.self="closePreview">
      <div class="modal-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">Preview</p>
            <h3>پیش نمایش درخواست</h3>
          </div>
          <button class="ghost-btn" @click="closePreview">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <div class="preview-stack">
          <div class="preview-card">
            <span>عنوان</span>
            <strong>{{ requestForm.title || '---' }}</strong>
          </div>
          <div class="preview-card">
            <span>واحد</span>
            <strong>{{ departmentLabel(requestForm.department) || '---' }}</strong>
          </div>
          <div class="preview-card">
            <span>مدیر</span>
            <strong>{{ managerLabel(requestForm.manager) || '---' }}</strong>
          </div>
          <div class="preview-card">
            <span>اولویت</span>
            <strong>{{ priorityLabel(requestForm.priority) }}</strong>
          </div>
          <div class="preview-card span-full">
            <span>توضیحات</span>
            <p>{{ requestForm.description || 'توضیحی ثبت نشده است.' }}</p>
          </div>
        </div>

        <div class="form-actions">
          <button class="secondary-btn" @click="closePreview">بستن</button>
          <div class="spacer"></div>
          <button class="primary-btn" @click="submitRequest">تایید و ارسال</button>
        </div>
      </div>
    </div>
  </div>
</template>
