<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

const signupTo = { path: '/login', query: { signup: '1' } }
const loginTo = '/login'
const logoSrc = '/logo/green.webp'

const painPoints = [
  ['۰۱', 'ارجاع بدون مسیر مشخص', 'درخواست ثبت می‌شود، اما مشخص نیست پیش چه کسی است و چه تصمیمی گرفته شده.'],
  ['۰۲', 'سابقه تصمیم ناقص', 'علت رد، ارجاع مجدد و زمان اقدام‌ها بین پیام‌ها و فایل‌های پراکنده گم می‌شود.'],
  ['۰۳', 'هزینه بدون سند کافی', 'فاکتورها پراکنده‌اند و جمع‌بندی روز، ماه و سال به‌موقع در دسترس نیست.'],
  ['۰۴', 'تأیید سند به‌صورت دستی', 'فایل بین مدیران می‌چرخد و نسخه نهایی امضاشده سخت پیدا می‌شود.'],
  ['۰۵', 'دسترسی نامتناسب', 'بعضی افراد بیش از نیاز می‌بینند؛ بعضی به بخش ضروری‌شان دسترسی ندارند.'],
  ['۰۶', 'گزارش‌گیری زمان‌بر', 'برای خروجی مدیریتی، داده دوباره و دستی از چند جا جمع می‌شود.'],
]

const pillars = [
  ['RQ', 'درخواست‌ها', 'ثبت، ارجاع، تأیید یا رد، همراه با تاریخچه تصمیم‌ها.', 'mint'],
  ['EX', 'هزینه‌ها', 'ثبت مبلغ و فاکتور، بررسی مدیریتی و خلاصه دوره‌ای.', 'gold'],
  ['SG', 'تأیید اسناد', 'ارسال سند، امضای دیجیتال و دریافت نسخه نهایی.', 'blue'],
  ['RP', 'گزارش و دسترسی', 'خروجی CSV، نقش‌ها و کنترل دسترسی بخشی.', 'rose'],
]

const modules = [
  ['۰۱', 'ثبت درخواست', 'عنوان، پیوست، اولویت و ارجاع به مدیر یا کارمند؛ با تأیید، رد و ارجاع مجدد.'],
  ['۰۲', 'ثبت و تأیید سند', 'ارسال PDF یا تصویر برای چند تأییدکننده، ثبت امضا روی فایل و دانلود نسخه نهایی.'],
  ['۰۳', 'ثبت هزینه', 'مبلغ، شرح، فاکتور و مسیر بررسی مدیریتی؛ با خلاصه روز، هفته، ماه و سال.'],
  ['۰۴', 'ورود و خروج', 'لینک اختصاصی حضور برای هر نفر و گزارش بازه‌ای ورود و خروج.'],
  ['۰۵', 'تفکیک دسترسی', 'ترکیب نقش سازمانی و مجوز ماژول؛ هر فرد فقط بخش مجاز را می‌بیند.'],
  ['۰۶', 'گزارش‌ها', 'گزارش تفکیکی درخواست، هزینه، تأییدیه و کاربران با خروجی CSV.'],
  ['۰۷', 'پاداش و جریمه', 'ثبت مبلغ پاداش یا جریمه روی کاربر، در پرونده پرسنلی همان مجموعه.'],
  ['۰۸', 'کاربران و ساختار', 'ایجاد کاربر، مدیر مستقیم، بخش، سمت و فعال یا غیرفعال‌سازی.'],
  ['۰۹', 'کیف پول', 'مانده، واریز، برداشت و پیگیری تراکنش‌های عملیاتی مجموعه.'],
  ['۱۰', 'پشتیبانی', 'تیکت، مکالمه، پیوست و پیگیری درخواست‌های فنی یا مالی.'],
]

const features = [
  ['۰۱', 'Dashboard', 'داشبورد عملیاتی', 'وضعیت روز، صف اقدام و پرونده‌های قابل پیگیری را متناسب با نقش خود ببینید.'],
  ['۰۲', 'Requests', 'مدیریت درخواست', 'ثبت با پیوست، ارجاع چندنفره، تأیید یا رد، و تایم‌لاین کامل تصمیم‌ها.'],
  ['۰۳', 'Approvals', 'تأیید اسناد', 'چند تأییدکننده، امضای دیجیتال روی فایل و دانلود امن نسخه نهایی.'],
  ['۰۴', 'Expenses', 'کنترل هزینه', 'فاکتور، مبلغ، ارجاع مدیریتی و خلاصه دوره‌ای هزینه‌ها.'],
  ['۰۵', 'Reports', 'گزارش مدیریتی', 'فیلتر داده درخواست، هزینه، تأییدیه و کاربران و دریافت خروجی CSV.'],
  ['۰۶', 'Access', 'کنترل دسترسی', 'نقش سازمانی به‌همراه مجوز بخشی برای ماژول‌های حساس.'],
  ['۰۷', 'Wallet', 'کیف پول', 'مانده، واریز، برداشت و دفتر تراکنش با مسیر پشتیبانی.'],
  ['۰۸', 'Support', 'پشتیبانی', 'تیکت، گفتگو، پیوست و امتیاز پس از بسته‌شدن.'],
  ['۰۹', 'Attendance', 'حضور و غیاب', 'ثبت ورود و خروج با لینک اختصاصی و گزارش بازه‌ای.'],
  ['۱۰', 'Cloud', 'فضای اسناد', 'بارگذاری، پیش‌نمایش و دانلود اسناد متصل به مسیر تأیید.'],
  ['۱۱', 'HQ', 'مدیریت مجموعه‌ها', 'فعال‌سازی سازمان، پشتیبانی چندمجموعه و کنترل سطح پلتفرم.'],
  ['۱۲', 'Users', 'مدیریت کاربران', 'کاربر، مدیر مستقیم، بخش، سمت، پاداش، جریمه و وضعیت فعالیت.'],
]

const steps = [
  ['۱', 'ثبت پرونده', 'درخواست، هزینه یا سند را با اطلاعات، پیوست و گیرنده‌ها ثبت کنید.'],
  ['۲', 'ارجاع به مسئول', 'پرونده در صف اقدام افراد مجاز قرار می‌گیرد.'],
  ['۳', 'ثبت تصمیم', 'تأیید، رد با علت، ارجاع مجدد یا امضا در همان مسیر انجام می‌شود.'],
  ['۴', 'خروجی و پیگیری', 'وضعیت به‌روز می‌ماند و در گزارش‌ها قابل استخراج است.'],
]

const roles = [
  ['ک', 'کارمند', 'اجرای روزانه', 'ثبت درخواست و هزینه، پیگیری پرونده، حضور و تیکت'],
  ['م', 'مدیر', 'تصمیم عملیاتی', 'تأیید، رد، ارجاع، امضا و بررسی هزینه'],
  ['ا', 'مدیر ارشد', 'نظارت گسترده‌تر', 'دسترسی مدیریتی وسیع‌تر روی داده‌های سازمان'],
  ['ع', 'مدیرعامل', 'حاکمیت مجموعه', 'کاربران، تنظیمات، مجوزها و گزارش‌ها'],
  ['HQ', 'سطح پلتفرم', 'مدیریت کلان', 'مجموعه‌ها، ثبت‌نام، پشتیبانی و عملیات مالی'],
]

const faqs = [
  ['کارنومند برای چه سازمان‌هایی مناسب است؟', 'برای مجموعه‌هایی که درخواست داخلی، تأیید سند، هزینه و گزارش مدیریتی دارند و می‌خواهند این کارها از پیام‌رسان و فایل‌های پراکنده خارج شود.'],
  ['ثبت‌نام مجموعه چطور انجام می‌شود؟', 'از صفحه ورود، اطلاعات مدیر و مدارک مجموعه ارسال می‌شود. پس از بررسی HQ، حساب مجموعه فعال می‌گردد.'],
  ['آیا امضا روی خود فایل اعمال می‌شود؟', 'بله. پس از ثبت امضا و تأیید سند، امضا روی فایل درج می‌شود و نسخه نهایی از مسیر محافظت‌شده قابل دانلود است.'],
  ['آیا همه کاربران همه بخش‌ها را می‌بینند؟', 'خیر. علاوه بر نقش، دسترسی بخشی برای ماژول‌هایی مثل هزینه، گزارش، کاربران و تنظیمات قابل تعریف است.'],
  ['گزارش‌ها چه خروجی‌ای دارند؟', 'گزارش‌های تفکیکی درخواست، هزینه، تأییدیه و کاربران با فیلتر و خروجی CSV در دسترس است.'],
  ['چرا کاربر حذف نمی‌شود؟', 'به‌جای حذف، غیرفعال‌سازی انجام می‌شود تا سابقه پرونده‌ها و تصمیم‌ها حفظ شود.'],
]

const mobileNavOpen = ref(false)
const headerScrolled = ref(false)
const pageReady = ref(false)
const openFaq = ref(0)

let revealObserver = null
let scrollRaf = 0

function closeMobileNav() {
  mobileNavOpen.value = false
}

function toggleMobileNav() {
  mobileNavOpen.value = !mobileNavOpen.value
}

function onScroll() {
  if (scrollRaf) return
  scrollRaf = window.requestAnimationFrame(() => {
    headerScrolled.value = window.scrollY > 18
    scrollRaf = 0
  })
}

function onResize() {
  if (window.innerWidth > 1100 && mobileNavOpen.value) {
    mobileNavOpen.value = false
  }
}

function setFaq(index) {
  openFaq.value = openFaq.value === index ? -1 : index
}

function setupReveals(root) {
  const nodes = root?.querySelectorAll('[data-reveal]')
  if (!nodes?.length) return

  if (!('IntersectionObserver' in window)) {
    nodes.forEach((node) => node.classList.add('is-revealed'))
    return
  }

  revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return
        entry.target.classList.add('is-revealed')
        revealObserver?.unobserve(entry.target)
      })
    },
    { threshold: 0.12, rootMargin: '0px 0px -6% 0px' },
  )

  nodes.forEach((node) => revealObserver.observe(node))
}

onMounted(() => {
  document.title = 'کارنومند | سامانه مدیریت گردش‌کار سازمانی'
  document.documentElement.classList.add('landing-active')
  document.body.classList.add('landing-active')
  pageReady.value = true
  onScroll()
  window.addEventListener('scroll', onScroll, { passive: true })
  window.addEventListener('resize', onResize, { passive: true })
  setupReveals(document.querySelector('.landing-page'))
})

onUnmounted(() => {
  document.documentElement.classList.remove('landing-active')
  document.body.classList.remove('landing-active')
  document.body.classList.remove('landing-nav-lock')
  document.title = 'کارنومند'
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('resize', onResize)
  if (scrollRaf) window.cancelAnimationFrame(scrollRaf)
  revealObserver?.disconnect()
})

watch(mobileNavOpen, (open) => {
  document.body.classList.toggle('landing-nav-lock', open)
})
</script>

<template>
  <div class="landing-page" :class="{ 'is-nav-open': mobileNavOpen, 'is-ready': pageReady, 'is-scrolled': headerScrolled }">
    <main>
      <section class="hero-shell" id="top">
        <div class="hero-aurora hero-aurora-one" />
        <div class="hero-aurora hero-aurora-two" />
        <div class="hero-aurora hero-aurora-three" />
        <div class="hero-orb hero-orb-one" />
        <div class="hero-orb hero-orb-two" />
        <div class="hero-grid" />
        <div class="hero-noise" aria-hidden="true" />

        <header class="site-header" :class="{ 'is-scrolled': headerScrolled }">
          <div class="site-header-inner">
            <a class="brand brand-title" href="#top" aria-label="کارنومند، صفحه اصلی" @click="closeMobileNav">
              <img class="brand-logo" :src="logoSrc" alt="" width="44" height="44" decoding="async" />
              <span class="brand-copy"><strong>کارنومند</strong><small>گردش‌کار سازمانی</small></span>
            </a>

            <nav class="desktop-nav" aria-label="منوی اصلی">
              <a href="#solution">راهکار</a>
              <a href="#modules">ماژول‌ها</a>
              <a href="#features">قابلیت‌ها</a>
              <a href="#workflow">نحوه کار</a>
              <a href="#faq">پرسش‌های متداول</a>
            </nav>

            <div class="header-actions">
              <RouterLink class="panel-login" :to="loginTo">ورود به پنل
                <svg class="dir-arrow" aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" /></svg>
              </RouterLink>
              <RouterLink class="header-signup" :to="signupTo">ثبت‌نام</RouterLink>
              <button
                class="mobile-nav-toggle"
                type="button"
                :aria-expanded="mobileNavOpen"
                aria-controls="landing-mobile-nav"
                aria-label="منو"
                @click="toggleMobileNav"
              >
                <span /><span /><span />
              </button>
            </div>
          </div>
        </header>

        <nav
          id="landing-mobile-nav"
          class="mobile-nav"
          aria-label="منوی موبایل"
          :class="{ 'is-open': mobileNavOpen }"
        >
          <a href="#solution" @click="closeMobileNav">راهکار</a>
          <a href="#modules" @click="closeMobileNav">ماژول‌ها</a>
          <a href="#features" @click="closeMobileNav">قابلیت‌ها</a>
          <a href="#workflow" @click="closeMobileNav">نحوه کار</a>
          <a href="#faq" @click="closeMobileNav">پرسش‌های متداول</a>
          <RouterLink class="button button-primary" :to="signupTo" @click="closeMobileNav">ثبت‌نام مجموعه</RouterLink>
          <RouterLink class="button button-ghost" :to="loginTo" @click="closeMobileNav">ورود به پنل</RouterLink>
        </nav>

        <div class="hero-content page-wrap">
          <div class="hero-copy hero-enter">
            <p class="brand-hero-mark">کارنومند</p>
            <div class="eyebrow"><span class="live-dot" /> سامانه مدیریت عملیات سازمانی</div>
            <h1>مدیریت درخواست، هزینه و تأیید اسناد<span>در یک پنل سازمانی</span></h1>
            <p class="hero-lead">ثبت و پیگیری درخواست‌ها، هزینه‌ها و اسناد تاییدی؛ با نقش‌بندی، امضای دیجیتال و گزارش‌گیری در یک محیط فارسی.</p>
            <div class="hero-actions">
              <RouterLink class="button button-primary" :to="signupTo">ثبت‌نام مجموعه
                <svg class="dir-arrow" aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" /></svg>
              </RouterLink>
              <a class="button button-ghost" href="#modules">مشاهده ماژول‌ها</a>
            </div>
            <p class="hero-microcopy">
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="m6.5 12.5 3.5 3.5 7.5-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
              پس از ارسال مدارک و بررسی پشتیبانی، حساب مجموعه فعال می‌شود.
            </p>
            <div class="hero-trust"><span>رابط فارسی RTL</span><i /><span>دسترسی نقش‌محور</span><i /><span>امضای دیجیتال روی فایل</span></div>
          </div>

          <div class="hero-visual hero-enter hero-enter-delay" aria-label="نمایی از داشبورد عملیاتی کارنومند">
            <div class="visual-halo" />
            <div class="dashboard-float dashboard-float-top">
              <span class="float-icon float-icon-green">
                <svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="m6.5 12.5 3.5 3.5 7.5-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
              </span>
              <span><small>وضعیت سند</small><strong>امضا تکمیل شد</strong></span>
            </div>
            <div class="dashboard-frame">
              <div class="dashboard-topbar">
                <div class="window-dots"><i /><i /><i /></div>
                <div class="dash-search">جستجو در کارنومند...</div>
                <div class="dash-avatar">د</div>
              </div>
              <div class="dashboard-body">
                <aside class="dash-sidebar">
                  <div class="mini-brand">
                    <img class="brand-logo brand-logo-sm" :src="logoSrc" alt="" width="28" height="28" decoding="async" />
                  </div>
                  <span class="side-item side-item-active"><b /> نمای روز</span>
                  <span class="side-item"><b /> درخواست‌ها</span>
                  <span class="side-item"><b /> تأییدیه‌ها</span>
                  <span class="side-item"><b /> هزینه‌ها</span>
                  <span class="side-item"><b /> گزارشات</span>
                  <span class="side-item side-item-bottom"><b /> تنظیمات</span>
                </aside>
                <div class="dash-main">
                  <div class="dash-heading">
                    <span><small>صبح بخیر، دامون</small><strong>نمای روز سازمان</strong></span>
                    <button type="button">+ درخواست جدید</button>
                  </div>
                  <div class="stat-row">
                    <div class="mini-stat"><span class="stat-glyph glyph-green">↗</span><small>نیازمند اقدام</small><strong>۸</strong></div>
                    <div class="mini-stat"><span class="stat-glyph glyph-blue">✓</span><small>تأیید شده</small><strong>۲۴</strong></div>
                    <div class="mini-stat"><span class="stat-glyph glyph-gold">◷</span><small>در حال بررسی</small><strong>۱۲</strong></div>
                  </div>
                  <div class="dash-lower">
                    <div class="dash-list">
                      <div class="widget-title"><strong>صف اقدام من</strong><span>مشاهده همه</span></div>
                      <div class="request-row"><span class="request-badge high">بالا</span><span class="request-copy"><strong>تأیید پیش‌فاکتور تجهیزات</strong><small>واحد فناوری · امروز</small></span><span class="row-arrow">‹</span></div>
                      <div class="request-row"><span class="request-badge medium">متوسط</span><span class="request-copy"><strong>صورت‌جلسه همکاری فروش</strong><small>واحد بازرگانی · دیروز</small></span><span class="row-arrow">‹</span></div>
                      <div class="request-row"><span class="request-badge low">عادی</span><span class="request-copy"><strong>درخواست مرخصی ساعتی</strong><small>منابع انسانی · ۲ روز پیش</small></span><span class="row-arrow">‹</span></div>
                    </div>
                    <div class="dash-chart">
                      <div class="widget-title"><strong>وضعیت پرونده‌ها</strong><span>این ماه</span></div>
                      <div class="donut"><div><strong>۷۶٪</strong><small>تعیین تکلیف</small></div></div>
                      <div class="chart-key"><span><i class="key-green" /> تأیید</span><span><i class="key-gold" /> بررسی</span><span><i class="key-gray" /> سایر</span></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="dashboard-float dashboard-float-bottom">
              <span class="float-icon float-icon-gold">↗</span>
              <span><small>درخواست جدید</small><strong>به مدیر ارجاع شد</strong></span>
            </div>
          </div>
        </div>
        <div class="hero-bottom-line page-wrap"><span>پرونده با وضعیت مشخص</span><span>تصمیم ثبت‌شده در سیستم</span><span>دسترسی کنترل‌شده</span></div>
      </section>

      <section class="proof-strip" aria-label="خلاصه قابلیت‌های اصلی" data-reveal>
        <div class="page-wrap proof-grid">
          <div><strong>۴</strong><span>محور اصلی عملیات</span></div>
          <div><strong>۵</strong><span>سطح نقش سازمانی</span></div>
          <div><strong>CSV</strong><span>خروجی گزارش مدیریتی</span></div>
          <div><strong>RTL</strong><span>رابط کاربری فارسی</span></div>
        </div>
      </section>

      <section class="section pain-section" id="problem" data-reveal>
        <div class="page-wrap">
          <div class="section-heading split-heading">
            <div>
              <span class="section-kicker">چالش‌های رایج</span>
              <h2>گلوگاه‌های رایج در کار روزانه</h2>
            </div>
            <p>وقتی پیگیری روی پیام‌رسان و فایل‌های محلی باشد، وضعیت پرونده مبهم می‌ماند و گزارش‌گیری زمان‌بر می‌شود.</p>
          </div>
          <div class="pain-grid">
            <article v-for="[number, title, text] in painPoints" :key="number" class="pain-card">
              <span class="pain-number">{{ number }}</span>
              <div><h3>{{ title }}</h3><p>{{ text }}</p></div>
              <span class="pain-corner">↙</span>
            </article>
          </div>
        </div>
      </section>

      <section class="section solution-section" id="solution" data-reveal>
        <div class="solution-glow" />
        <div class="page-wrap">
          <div class="section-heading solution-heading">
            <span class="section-kicker section-kicker-light">راه‌حل کارنومند</span>
            <h2>چهار محور اصلی سامانه</h2>
            <p>هر پرونده کد، وضعیت، مسئول اقدام و سابقه تصمیم دارد؛ از ثبت تا نتیجه در یک مسیر مشخص.</p>
          </div>
          <div class="pillar-grid">
            <article
              v-for="([code, title, text, color], index) in pillars"
              :key="code"
              class="pillar-card"
              :class="`pillar-${color}`"
              :style="{ '--reveal-delay': `${index * 70}ms` }"
            >
              <div class="pillar-top">
                <span class="pillar-code">{{ code }}</span>
                <span class="pillar-count">۰{{ index + 1 }}</span>
              </div>
              <h3>{{ title }}</h3>
              <p>{{ text }}</p>
              <div class="pillar-flow"><span /><i /><i /><i /></div>
            </article>
          </div>
          <div class="solution-statement">
            <span class="statement-mark">“</span>
            <p>وضعیت پرونده را در سامانه ببینید؛ نه در پیام‌های پراکنده.</p>
            <a href="#modules">فهرست ماژول‌ها
              <svg class="dir-arrow" aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" /></svg>
            </a>
          </div>
        </div>
      </section>

      <section class="section modules-section" id="modules" data-reveal>
        <div class="page-wrap">
          <div class="section-heading centered-heading">
            <span class="section-kicker">ماژول‌های سامانه</span>
            <h2>امکانات در اختیار شما</h2>
            <p>هر ماژول یک کار مشخص را پوشش می‌دهد؛ از ثبت درخواست و سند تا دسترسی، گزارش و حضور.</p>
          </div>
          <div class="module-grid">
            <article v-for="[index, title, text] in modules" :key="index" class="module-card">
              <span class="module-index">{{ index }}</span>
              <h3>{{ title }}</h3>
              <p>{{ text }}</p>
            </article>
          </div>
        </div>
      </section>

      <section class="section features-section" id="features" data-reveal>
        <div class="page-wrap">
          <div class="section-heading centered-heading">
            <span class="section-kicker">جزئیات قابلیت‌ها</span>
            <h2>هر آنچه برای یک روز کاری لازم دارید</h2>
            <p>جزئیات هر بخش برای کار روزانه، تصمیم‌گیری و گزارش‌گیری.</p>
          </div>
          <div class="feature-grid">
            <article
              v-for="[index, tag, title, text] in features"
              :key="index"
              class="feature-card"
            >
              <div class="feature-head">
                <span class="feature-index">{{ index }}</span>
                <span class="feature-tag">{{ tag }}</span>
              </div>
              <div class="feature-icon"><span /><i /><b /></div>
              <h3>{{ title }}</h3>
              <p>{{ text }}</p>
            </article>
          </div>
          <div class="inline-cta">
            <span><small>حساب مجموعه فعال است؟</small><strong>وارد پنل شوید.</strong></span>
            <RouterLink class="button button-dark" :to="loginTo">ورود به پنل
              <svg class="dir-arrow" aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" /></svg>
            </RouterLink>
          </div>
        </div>
      </section>

      <section class="section workflow-section" id="workflow" data-reveal>
        <div class="page-wrap">
          <div class="section-heading split-heading workflow-heading">
            <div>
              <span class="section-kicker">مسیر کار</span>
              <h2>از ثبت تا نتیجه در چهار مرحله</h2>
            </div>
            <p>هر اقدام در سامانه ثبت می‌شود و مسیر پرونده برای افراد مجاز قابل پیگیری می‌ماند.</p>
          </div>
          <div class="steps-grid">
            <article v-for="([step, title, text], index) in steps" :key="step" class="step-card">
              <div class="step-line">
                <span>{{ step }}</span>
                <i v-if="index < steps.length - 1" />
              </div>
              <h3>{{ title }}</h3>
              <p>{{ text }}</p>
            </article>
          </div>
        </div>
      </section>

      <section class="signature-showcase" data-reveal>
        <div class="page-wrap signature-grid">
          <div class="signature-copy">
            <span class="section-kicker section-kicker-light">تأیید اسناد</span>
            <h2>تأیید سند با امضای دیجیتال</h2>
            <p>سند برای یک یا چند مدیر ارسال می‌شود. تصمیم‌ها در تاریخچه می‌ماند و پس از تأیید، امضا روی فایل اعمال می‌شود.</p>
            <ul class="check-list">
              <li>
                <svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="m6.5 12.5 3.5 3.5 7.5-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
                تصویر یا PDF با نوع و سطح ریسک
              </li>
              <li>
                <svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="m6.5 12.5 3.5 3.5 7.5-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
                تأیید، رد با علت و ارجاع مجدد
              </li>
              <li>
                <svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="m6.5 12.5 3.5 3.5 7.5-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
                امضای دیجیتال و مهر اختیاری
              </li>
              <li>
                <svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="m6.5 12.5 3.5 3.5 7.5-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
                دانلود محافظت‌شده نسخه نهایی
              </li>
            </ul>
            <RouterLink class="text-link" :to="signupTo">ثبت‌نام مجموعه
              <svg class="dir-arrow" aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" /></svg>
            </RouterLink>
          </div>
          <div class="document-scene" aria-label="نمایش گردش امضای دیجیتال سند">
            <div class="doc-card doc-back"><span /><span /><span /></div>
            <div class="doc-card doc-main">
              <div class="doc-header">
                <img class="brand-logo brand-logo-sm" :src="logoSrc" alt="" width="28" height="28" decoding="async" />
                <span><small>صورت‌جلسه همکاری</small><strong>CNM-1405-0084</strong></span>
                <i>PDF</i>
              </div>
              <div class="doc-lines"><span class="doc-line-long" /><span /><span class="doc-line-medium" /><span /><span class="doc-line-long" /></div>
              <div class="doc-sign-area"><span><small>امضای مدیرعامل</small><strong>کـــارنــومــنــد</strong></span><i>تأیید شد</i></div>
            </div>
            <div class="sign-float">
              <span>
                <svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="m6.5 12.5 3.5 3.5 7.5-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
              </span>
              <div><small>نسخه نهایی آماده است</small><strong>دانلود فایل امضاشده</strong></div>
              <b>↓</b>
            </div>
            <div class="risk-float"><small>سطح ریسک</small><strong>متوسط</strong></div>
          </div>
        </div>
      </section>

      <section class="section access-section" id="access" data-reveal>
        <div class="page-wrap">
          <div class="section-heading centered-heading">
            <span class="section-kicker">دسترسی‌ها</span>
            <h2>نقش‌ها و محدوده دسترسی</h2>
            <p>نقش، سطح مسئولیت را مشخص می‌کند؛ دسترسی بخشی تعیین می‌کند کدام ماژول‌ها در اختیار کاربر باشد.</p>
          </div>
          <div class="roles-panel">
            <div class="roles-head"><span>نقش سازمانی</span><span>تمرکز</span><span>اقدام‌های اصلی</span></div>
            <div v-for="[mark, title, subtitle, actions] in roles" :key="title" class="role-row">
              <div class="role-name"><span class="role-mark">{{ mark }}</span><strong>{{ title }}</strong></div>
              <span class="role-subtitle">{{ subtitle }}</span>
              <span class="role-actions">{{ actions }}</span>
              <span class="role-arrow">←</span>
            </div>
          </div>
          <div class="access-note">
            <div class="access-orbit">
              <img class="brand-logo" :src="logoSrc" alt="" width="44" height="44" decoding="async" />
              <span class="orbit-dot orbit-one" />
              <span class="orbit-dot orbit-two" />
              <span class="orbit-dot orbit-three" />
            </div>
            <div>
              <strong>نقش‌محور و بخش‌محور</strong>
              <p>نقش سطح اختیار را می‌سازد؛ دسترسی بخشی محدوده ماژول‌های قابل مشاهده را محدود می‌کند.</p>
            </div>
          </div>
        </div>
      </section>

      <section class="section scenarios-section" data-reveal>
        <div class="page-wrap scenario-grid">
          <div class="section-heading scenario-copy">
            <span class="section-kicker">کاربردها</span>
            <h2>کاربرد در کارهای روزمره</h2>
            <p>هر جریان یک پرونده رسمی است؛ با مسئول مشخص، وضعیت روشن و سابقه قابل استناد.</p>
            <div class="scenario-tags">
              <span>درخواست خرید</span><span>مرخصی</span><span>هزینه واحدها</span><span>صورت‌جلسه</span>
              <span>مجوز داخلی</span><span>قرارداد داخلی</span><span>تیکت مالی</span><span>حضور نیروها</span>
            </div>
          </div>
          <div class="timeline-card">
            <div class="timeline-top"><span><small>پرونده درخواست خرید</small><strong>#CNM-2841</strong></span><i>در حال بررسی</i></div>
            <div class="timeline-progress"><span class="progress-active" /><span class="progress-active" /><span class="progress-current" /><span /></div>
            <div class="timeline-events">
              <div>
                <span class="event-mark event-done">
                  <svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="m6.5 12.5 3.5 3.5 7.5-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
                </span>
                <p><strong>درخواست ثبت شد</strong><small>امروز، ساعت ۰۹:۲۴</small></p>
              </div>
              <div>
                <span class="event-mark event-done">
                  <svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="m6.5 12.5 3.5 3.5 7.5-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
                </span>
                <p><strong>به مدیر واحد ارجاع شد</strong><small>امروز، ساعت ۰۹:۲۵</small></p>
              </div>
              <div>
                <span class="event-mark event-now">◷</span>
                <p><strong>در انتظار تصمیم مدیر</strong><small>آخرین فعالیت، ۱۲ دقیقه پیش</small></p>
              </div>
              <div class="event-muted">
                <span class="event-mark">۴</span>
                <p><strong>ثبت نتیجه نهایی</strong><small>پس از تصمیم مدیر</small></p>
              </div>
            </div>
            <div class="timeline-footer">
              <span class="mini-people"><i>م</i><i>د</i><i>ع</i></span>
              <span>۳ نفر در این پرونده</span>
              <button type="button">مشاهده جزئیات</button>
            </div>
          </div>
        </div>
      </section>

      <section class="section control-section" data-reveal>
        <div class="page-wrap">
          <div class="section-heading split-heading">
            <div>
              <span class="section-kicker">امنیت عملیاتی</span>
              <h2>کنترل‌های امنیتی و عملیاتی</h2>
            </div>
            <p>مجوز مشاهده، مسیر دریافت فایل و سابقه تصمیم‌ها در خود فرایند کار قرار گرفته است.</p>
          </div>
          <div class="control-grid">
            <article><span class="control-symbol">◎</span><h3>دسترسی دقیق</h3><p>ترکیب نقش سازمانی و مجوز ماژول برای اطلاعات حساس.</p></article>
            <article><span class="control-symbol">⌁</span><h3>اثر قابل ردیابی</h3><p>تأیید، رد و ارجاع با زمان و علت در تایم‌لاین می‌ماند.</p></article>
            <article><span class="control-symbol">▣</span><h3>فایل محافظت‌شده</h3><p>پیش‌نمایش و دانلود اسناد از مسیر کنترل‌شده سامانه.</p></article>
            <article><span class="control-symbol">◈</span><h3>حفظ تاریخچه</h3><p>غیرفعال‌سازی کاربر، بدون پاک شدن سابقه تصمیم‌ها و پرونده‌ها.</p></article>
          </div>
        </div>
      </section>

      <section class="section audience-section" data-reveal>
        <div class="page-wrap audience-panel">
          <div>
            <span class="section-kicker section-kicker-light">مخاطبان</span>
            <h2>برای چه مجموعه‌هایی مناسب است</h2>
          </div>
          <div class="audience-list">
            <span><i>۰۱</i> شرکت‌های خدماتی و اجرایی</span>
            <span><i>۰۲</i> مجموعه‌های چندواحدی</span>
            <span><i>۰۳</i> سازمان‌های پروژه‌محور</span>
            <span><i>۰۴</i> تیم‌های در حال رشد</span>
            <span><i>۰۵</i> هلدینگ‌ها و چندمجموعه‌ای‌ها</span>
          </div>
        </div>
      </section>

      <section class="section faq-section" id="faq" data-reveal>
        <div class="page-wrap faq-grid">
          <div class="section-heading faq-heading">
            <span class="section-kicker">پرسش‌های متداول</span>
            <h2>پرسش‌های پرتکرار</h2>
            <p>در صورت نیاز بیشتر، پس از ورود می‌توانید از پشتیبانی درون‌سامانه استفاده کنید.</p>
            <RouterLink class="text-link text-link-dark" :to="loginTo">ورود به پنل
              <svg class="dir-arrow" aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" /></svg>
            </RouterLink>
          </div>
          <div class="faq-list">
            <details
              v-for="([question, answer], index) in faqs"
              :key="question"
              :open="openFaq === index"
            >
              <summary @click.prevent="setFaq(index)"><span>{{ question }}</span><i /></summary>
              <p>{{ answer }}</p>
            </details>
          </div>
        </div>
      </section>

      <section class="final-cta-section" data-reveal>
        <div class="final-cta-glow" />
        <div class="final-cta-grid" />
        <div class="page-wrap final-cta-content">
          <img class="brand-logo brand-logo-lg" :src="logoSrc" alt="کارنومند" width="62" height="62" decoding="async" />
          <span class="section-kicker section-kicker-light">شروع کار</span>
          <h2>شروع کار با کارنومند</h2>
          <p>درخواست، هزینه، سند و گزارش را در یک پنل سازمانی با دسترسی کنترل‌شده مدیریت کنید.</p>
          <div class="hero-actions final-actions">
            <RouterLink class="button button-primary" :to="signupTo">ثبت‌نام مجموعه
              <svg class="dir-arrow" aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" /></svg>
            </RouterLink>
            <RouterLink class="button button-ghost" :to="loginTo">ورود به پنل</RouterLink>
          </div>
          <small>مدارک را ارسال کنید؛ پس از بررسی پشتیبانی فعال می‌شوید.</small>
        </div>
      </section>

      <footer class="site-footer">
        <div class="page-wrap footer-top">
          <a class="brand footer-brand" href="#top">
            <img class="brand-logo" :src="logoSrc" alt="کارنومند" width="44" height="44" decoding="async" />
            <span class="brand-copy"><strong>کارنومند</strong><small>گردش‌کار سازمانی</small></span>
          </a>
          <nav aria-label="پیوندهای پایین صفحه">
            <a href="#solution">راهکار</a>
            <a href="#modules">ماژول‌ها</a>
            <a href="#features">قابلیت‌ها</a>
            <a href="#workflow">نحوه کار</a>
            <a href="#faq">سؤالات متداول</a>
          </nav>
          <RouterLink class="footer-login" :to="loginTo">ورود به پنل
            <svg class="dir-arrow" aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" /></svg>
          </RouterLink>
        </div>
        <div class="page-wrap footer-bottom">
          <span>© ۱۴۰۵ کارنومند؛ تمامی حقوق محفوظ است.</span>
          <span dir="ltr">Designed By DHS Development Team</span>
        </div>
      </footer>
    </main>
  </div>
</template>

<style scoped>
.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-signup {
  display: inline-flex;
  min-height: 46px;
  padding: 0 18px;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  color: #06261f;
  background: linear-gradient(135deg, #b8f5dc, #23cb92 76%);
  font-size: 0.82rem;
  font-weight: 800;
  box-shadow: 0 10px 28px rgba(18, 196, 135, 0.22);
  transition: transform 180ms ease, box-shadow 180ms ease;
}

.header-signup:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 34px rgba(18, 196, 135, 0.32);
}

.mobile-nav-toggle {
  display: none;
  width: 44px;
  height: 44px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.08);
  padding: 0;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  cursor: pointer;
}

.mobile-nav-toggle span {
  display: block;
  width: 18px;
  height: 2px;
  border-radius: 999px;
  background: #fff;
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.landing-page.is-nav-open .mobile-nav-toggle span:nth-child(1) {
  transform: translateY(7px) rotate(45deg);
}

.landing-page.is-nav-open .mobile-nav-toggle span:nth-child(2) {
  opacity: 0;
}

.landing-page.is-nav-open .mobile-nav-toggle span:nth-child(3) {
  transform: translateY(-7px) rotate(-45deg);
}

.mobile-nav {
  display: none;
  position: fixed;
  top: 84px;
  left: 16px;
  right: 16px;
  z-index: 60;
  padding: 18px;
  border-radius: 22px;
  background: rgba(7, 26, 23, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(18px);
  flex-direction: column;
  gap: 8px;
  max-height: calc(100dvh - 100px);
  overflow: auto;
}

.mobile-nav a {
  color: rgba(255, 255, 255, 0.88);
  padding: 12px 14px;
  border-radius: 14px;
  font-weight: 700;
}

.mobile-nav a:hover {
  background: rgba(255, 255, 255, 0.06);
}

.mobile-nav .button {
  justify-content: center;
  margin-top: 4px;
}

.mobile-nav.is-open {
  display: flex;
}

@media (max-width: 1100px) {
  .mobile-nav-toggle {
    display: inline-flex;
  }

  .panel-login,
  .header-signup {
    display: none;
  }
}

@media (min-width: 1101px) {
  .mobile-nav {
    display: none !important;
  }
}
</style>
