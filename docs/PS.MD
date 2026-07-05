# Workflow Hub

## Product Structure, Flows, and Page Schematic

این سند ساختار محصول، فلوهای اصلی کاربر، ناوبری و نقشه صفحات را بر اساس وضعیت واقعی frontend و store توضیح می دهد.

---

## 1. نقشه کلی محصول

```text
Login
  |
  v
Dashboard
  |-- Requests
  |-- Expenses
  |-- Approvals
  |-- Reports
  |-- Users
  `-- Settings
```

### مسیرهای اصلی frontend

- `/login`
- `/dashboard`
- `/requests`
- `/expenses`
- `/approvals`
- `/reports`
- `/users`
- `/settings`

### الگوی ناوبری

- کاربر بعد از ورود وارد `Dashboard` می شود
- شل اصلی برنامه شامل `AppSidebar` و `AppTopNav` است
- جزییات و فرم های ایجاد بیشتر به صورت modal باز می شوند، نه صفحه جدا

---

## 2. ساختار تجربه کاربری

### الگوی اصلی UI

محصول از یک الگوی modal-first استفاده می کند:

- صفحات برای مرور و فهرست
- modal برای ایجاد
- modal برای جزییات
- dashboard برای اقدام سریع

### modal های اصلی

- `RequestComposerModal`
- `RequestDetailModal`
- `ExpenseComposerModal`
- `ExpenseDetailModal`
- `DocumentComposerModal`
- `ApprovalDetailModal`
- `UserComposerModal`
- `SignatureComposerModal`

---

## 3. شمای ناوبری و وضعیت جلسه

```text
User opens app
  |
  +-- no token --> /login
  |
  `-- token exists --> restoreSession()
                         |
                         +-- /bootstrap
                         +-- optional /reports
                         `-- render role-based UI
```

### رفتار session

- توکن در `localStorage` با کلید `workflow-hub-token` نگهداری می شود
- اگر `401` دریافت شود، session پاک می شود
- بعد از login، داده های پایه با `bootstrap` بارگذاری می شوند

---

## 4. Page Map

### 4.1 Login Page

هدف:

- شروع امن و سریع جلسه کاربر

اجزای صفحه:

- پنل برند
- فرم ایمیل و رمز
- نمایش خطا
- CTA ورود

فلو:

1. کاربر ایمیل و رمز را وارد می کند
2. `login()` در store اجرا می شود
3. توکن ذخیره می شود
4. `loadBootstrapData(true)` اجرا می شود
5. کاربر به `/dashboard` هدایت می شود

---

### 4.2 Dashboard Page

هدف:

- نمایش خلاصه عملیاتی روز
- ارائه صف اقدام
- ایجاد مسیر سریع به ثبت درخواست

دو حالت اصلی:

- داشبورد مدیریتی
- داشبورد کاری

بخش ها:

- `PageHeader`
- Hero / stage panel
- Quick focus ribbon
- Operational snapshot
- Highlighted stats
- Action queue

منطق نقش:

- اگر نقش کاربر `admin`, `executive_manager`, `manager` باشد، نمای مدیریتی رندر می شود
- در غیر این صورت نمای شخصی و کاری نمایش داده می شود

فلوهای خروجی:

- باز کردن جزییات درخواست
- باز کردن جزییات هزینه
- باز کردن جزییات تاییدیه
- باز کردن فرم ثبت درخواست

---

### 4.3 Requests Page

هدف:

- نمایش فهرست درخواست ها
- دسترسی سریع به جزییات و مسیر اقدام

ساختار:

- کارت های آماری
- جدول درخواست ها

ستون ها:

- شماره
- عنوان
- ثبت کننده
- مدیر مسئول
- وضعیت
- اولویت
- تاریخ
- عملیات

فلو:

1. کاربر فهرست را می بیند
2. روی `مشاهده جزییات` کلیک می کند
3. `RequestDetailModal` باز می شود
4. در صورت مجاز بودن، تایید یا رد از modal انجام می شود

---

### 4.4 Request Composer Modal

هدف:

- ثبت درخواست جدید

فیلدها:

- عنوان
- بخش
- ارجاع به مدیر
- ارجاع به مدیران دیگر
- تاریخ
- اولویت
- توضیحات
- پیوست

اکشن های فعلی فرم:

- `ارجاع`
- `تایید`
- `رد`

نکته مهم:

در پیاده سازی فعلی، فرم ایجاد درخواست با سه action مختلف کار می کند و action مستقیما روی status اولیه درخواست اثر می گذارد.

---

### 4.5 Request Detail Modal

هدف:

- نمایش جزییات یک درخواست
- نمایش timeline
- انجام تایید یا رد برای افراد مجاز

ورودی داده:

- `/requests/<code>`

خروجی های کاربر:

- approve request
- reject request

---

### 4.6 Expenses Page

هدف:

- نمایش فهرست هزینه ها و خلاصه مالی

بخش ها:

- چهار کارت خلاصه: روز، هفته، ماه، سال
- جدول هزینه ها

ستون ها:

- عنوان
- مبلغ
- نوع
- ثبت کننده
- تاریخ
- وضعیت
- فاکتور
- عملیات

فلو:

1. کاربر فهرست را می بیند
2. در صورت وجود، فاکتور را باز می کند
3. جزییات هزینه را باز می کند
4. اگر مجاز باشد تایید یا رد می کند

---

### 4.7 Expense Composer Modal

فیلدها:

- شرح
- مبلغ
- تاریخ هزینه
- بخش
- فایل فاکتور

خروجی:

- ثبت هزینه جدید

---

### 4.8 Expense Detail Modal

نمایش:

- مشخصات هزینه
- فایل فاکتور
- وضعیت
- عملیات تایید یا رد برای نقش های مجاز

---

### 4.9 Approvals Page

هدف:

- مدیریت صف تایید اسناد
- مشاهده تاریخچه تاییدها

بخش ها:

- کارت های آماری
- صف بررسی
- جدول تاریخچه تاییدها

در صف بررسی هر کارت شامل:

- عنوان سند
- نوع سند
- بخش
- وضعیت
- دانلود فایل
- جزییات و اقدام

فلو:

1. کاربر وارد صف بررسی می شود
2. در صورت نیاز فایل را دانلود می کند
3. وارد جزییات سند می شود
4. در صورت نداشتن امضا، امضای دیجیتال را ثبت می کند
5. سند را تایید یا رد می کند

---

### 4.10 Document Composer Modal

هدف:

- ایجاد سند جدید برای گردش تایید

فیلدها:

- عنوان
- توضیحات
- بخش
- نوع سند
- ریسک
- گیرندگان تایید
- فایل

قید مهم:

- حداقل یک مدیر باید انتخاب شود

---

### 4.11 Approval Detail Modal

هدف:

- نمایش preview و metadata سند
- نمایش وضعیت ارجاع جاری
- ارائه دکمه های تایید، رد، دانلود و مشاهده

ورودی:

- `/approvals/<code>`

وابستگی:

- اگر کاربر امضای ذخیره شده نداشته باشد، برای approve باید ابتدا Signature modal را تکمیل کند

---

### 4.12 Signature Composer Modal

هدف:

- ثبت یا به روزرسانی امضای دیجیتال کاربر مدیریتی

فلو:

1. `GET /approvals/signature`
2. رندر pad یا امضای موجود
3. `POST /approvals/signature`
4. بازگشت به جریان تایید سند

---

### 4.13 Reports Page

هدف:

- ارائه نما و خروجی از سه دسته داده اصلی

تب های اصلی:

- درخواست ها
- هزینه ها
- تاییدیه ها

قابلیت ها:

- جابجایی بین تب ها
- مشاهده rows
- دریافت CSV

فلو:

1. صفحه `loadReports(true)` را فراخوانی می کند
2. داده summary و catalog گزارش ها دریافت می شود
3. کاربر تب را انتخاب می کند
4. کاربر خروجی CSV را دانلود می کند

---

### 4.14 Users Page

هدف:

- مشاهده ساختار کاربران
- جستجو و فیلتر سریع
- مشاهده جزییات هر کاربر

بخش ها:

- کارت های آماری
- فیلتر متنی
- فیلتر دسته ای
- فیلتر حروف الفبا
- جدول یا لیست سبک کاربران
- modal جزییات

دسترسی:

- فقط برای کسانی که `canAccessUsers` یا `canManageUsers` دارند

---

### 4.15 User Composer Modal

هدف:

- ایجاد کاربر جدید

فیلدها:

- نام کامل
- ایمیل
- رمز
- نقش دسترسی
- بخش
- مدیر مستقیم
- عنوان شغلی

نکته:

- ایجاد کاربر در عمل فقط برای `admin` مجاز است

---

### 4.16 Settings Page

هدف:

- مدیریت تنظیمات پایه سازمان
- مدیریت دسترسی کاربران به هر بخش

بخش ها:

- پروفایل سازمان
- خلاصه دسترسی ها
- جدول دسترسی بخش ها
- modal انتخاب کاربران مجاز برای هر بخش

بخش های قابل تنظیم:

- `users`
- `approvals`
- `expenses`
- `reports`

فلو:

1. ادمین یک بخش را باز می کند
2. کاربران سازمان را فیلتر و انتخاب می کند
3. دسترسی ذخیره می شود
4. لیست مجازهای آن بخش به روز می شود

---

## 5. فلوهای end-to-end

### 5.1 فلو کامل درخواست

```text
Dashboard or Requests
  -> Open Request Composer
  -> Fill form
  -> Submit
  -> POST /requests
  -> Bootstrap refresh
  -> Request appears in list
  -> Open detail
  -> Approve/Reject if allowed
```

### 5.2 فلو کامل هزینه

```text
Expenses
  -> Open Expense Composer
  -> Fill form
  -> POST /expenses
  -> Bootstrap refresh
  -> Open detail
  -> Approve/Reject if manager-level user
```

### 5.3 فلو کامل تایید سند

```text
Approvals
  -> Open Document Composer
  -> Choose managers
  -> POST /approvals/documents
  -> Document enters approval queue
  -> Assignee opens detail
  -> Ensure signature exists
  -> POST /approvals/<code>/approve
  -> Signed file generated
  -> Download protected file
```

### 5.4 فلو مدیریت دسترسی

```text
Settings
  -> Open section access modal
  -> Select allowed users
  -> POST /settings/profile
  -> SectionAccessGrant updated
  -> Access rules change immediately
```

---

## 6. شمای نمایش داده در frontend

### داده های پایه store

```text
currentUser
stats
chartData
pipeline
requests
expenses
approvals
users
reports
activities
expenseSummary
approvalMetrics
settings
directories
```

### دایرکتوری های مورد استفاده فرم ها

- `departments`
- `managers`
- `users`

این داده ها از `bootstrap` می آیند و منبع اصلی option های فرم هستند.

---

## 7. قواعد UX مبتنی بر کد فعلی

- صفحه ها برای مرور داده اند، modal ها برای عملیات
- جزییات request, expense, approval به صورت lazy load باز می شوند
- بعد از هر عملیات مهم، `loadBootstrapData(true)` اجرا می شود
- فایل ها با مسیر محافظت شده دانلود یا preview می شوند
- نقش کاربر مستقیما روی متن و ساختار داشبورد اثر می گذارد

---

## 8. شکاف های محصولی فعلی

- برای request و expense هنوز صفحه مستقل detail وجود ندارد و modal محور هستند
- reports فعلا فقط CSV export دارند
- users هنوز edit/delete ندارد
- settings هنوز تنظیمات عمیق برندینگ، امنیت پیشرفته یا audit explorer ندارد
- notification center، جستجوی سراسری و command palette در کد فعلی وجود ندارند

---

## 9. جمع بندی ساختاری

ساختار فعلی محصول ساده اما درست لایه بندی شده است:

- یک shell ثابت
- چند صفحه اصلی برای مرور
- چند modal عملیاتی برای create/detail/action
- یک store مرکزی برای session، data hydration و عملیات API

این الگو برای توسعه بعدی مناسب است چون هم تجربه کاربری را جمع و جور نگه می دارد، هم قرارداد صفحه ها و عملیات ها را از هم جدا می کند.
