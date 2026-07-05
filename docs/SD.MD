# Workflow Hub

## Software Design and System Architecture

این سند معماری فنی، مدل داده، API، قراردادهای frontend/backend و فلوهای اجرایی سیستم را بر اساس کد فعلی پروژه توضیح می دهد.

---

## 1. خلاصه فنی

### پشته واقعی پروژه

Frontend:

- Vue 3
- Vue Router
- Vite

Backend:

- Django 4.2
- PyMySQL
- PyJWT
- Passlib

Persistence:

- MySQL

File Storage:

- local filesystem via `MEDIA_ROOT`

Authentication:

- Bearer JWT

---

## 2. معماری کلان

```text
[Browser / Vue App]
        |
        | HTTP + Bearer Token
        v
[Django API /api/v1]
        |
        +-- Auth and Access Rules
        +-- Business Logic
        +-- File Signing / Downloads
        |
        +--> [MySQL]
        |
        `--> [Local Media Storage]
```

### اصل طراحی فعلی

- frontend thin نیست، اما orchestration-heavy است
- backend منبع حقیقت برای auth، visibility، serialization و state transitions است
- frontend با `bootstrap` یک snapshot عملیاتی می گیرد و UI را روی همان می سازد

---

## 3. ساختار repository

```text
backend/
  config/
  workflow/
    access.py
    document_signing.py
    models.py
    security.py
    seed.py
    services.py
    urls.py
    views.py

frontend/
  src/
    components/
    pages/
    router/
    stores/
    utils/
```

---

## 4. اجزای backend

### 4.1 `views.py`

مسئول:

- تعریف endpoint ها
- auth gating
- parse request
- validate payload
- ایجاد و به روزرسانی مدل ها
- فراخوانی serialization/services

### 4.2 `services.py`

مسئول:

- serialization
- aggregation
- bootstrap payload
- metrics
- report export
- helper های فرمت بندی و media url

### 4.3 `access.py`

مسئول:

- منطق نقش ها
- visibility کاربران
- کنترل دسترسی بخشی

### 4.4 `document_signing.py`

مسئول:

- درج امضای دیجیتال روی فایل سند
- تولید فایل نهایی امضاشده

### 4.5 `security.py`

مسئول:

- ساخت JWT
- decode JWT
- hash/verify password

---

## 5. اجزای frontend

### 5.1 `workflowHub.js`

Store مرکزی برنامه است و مسئول:

- session state
- bootstrap hydration
- form states
- modal states
- selected entity state
- API calls
- protected file open/download
- action flows

### 5.2 `router/index.js`

مسئول:

- route map
- guard بر اساس وجود token

### 5.3 `App.vue`

مسئول:

- shell اصلی برنامه
- mount شدن sidebar/topnav
- نگهداری modal های سراسری
- اجرای `restoreSession()` در شروع

---

## 6. شمای مدل داده

### 6.1 مدل های پایه سازمانی

```text
Organization
Department
User
OrganizationMembership
OrganizationPreference
SectionAccessGrant
UserSignature
```

### 6.2 مدل های عملیاتی

```text
Request
RequestAttachment
RequestTimeline

Expense

Document
ApprovalAssignment

AuditLog
```

---

## 7. روابط اصلی داده

```text
Organization 1---* OrganizationMembership *---1 User
Department   1---* User
Department   1---* Request
Department   1---* Expense
Department   1---* Document

User 1---* Request (requester)
User 1---* Request (manager)
User *---* Request (assigned_managers)

Request 1---* RequestAttachment
Request 1---* RequestTimeline

User 1---* Expense

User 1---* Document (owner)
Document 1---* ApprovalAssignment *---1 User (approver)

User 1---1 UserSignature
User 1---* AuditLog
```

---

## 8. Enumerations و state machines

### 8.1 UserRole

- `admin`
- `executive_manager`
- `manager`
- `employee`

### 8.2 RequestStatus

- `draft`
- `submitted`
- `under_review`
- `approved`
- `rejected`
- `closed`

### 8.3 ExpenseStatus

- `pending`
- `under_review`
- `approved`
- `needs_document`
- `rejected`

### 8.4 DocumentStatus

- `pending`
- `waiting_signature`
- `approved`
- `rejected`
- `archived`

### 8.5 ApprovalAssignmentStatus

- `pending`
- `approved`
- `rejected`

---

## 9. سیاست دسترسی

### 9.1 منطق نقش

```text
is_manager(user) := role in {admin, executive_manager, manager}
```

### 9.2 منطق visibility

- اگر کاربر manager-level باشد، همه کاربران سازمان را می بیند
- اگر employee باشد، فقط خود را می بیند

### 9.3 منطق section access

```text
admin -> always allowed
explicit grant exists -> only granted users allowed
no grant exists:
  users -> denied
  reports -> denied
  approvals -> allowed
  expenses -> allowed
```

### 9.4 منطق تایید درخواست

کاربر می تواند request را approve/reject کند اگر:

- status در `submitted` یا `under_review` باشد
- و یکی از موارد زیر برقرار باشد:
  - مدیر اصلی باشد
  - در `assigned_managers` باشد
  - `admin` یا `executive_manager` باشد

### 9.5 منطق تایید سند

کاربر می تواند سند را approve/reject کند اگر:

- manager-level باشد
- به بخش approvals دسترسی داشته باشد
- assignment مربوط به خودش روی document وجود داشته باشد

---

## 10. API Surface

### Health and Auth

- `GET /api/v1/health`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Bootstrap

- `GET /api/v1/bootstrap`

### Requests

- `GET /api/v1/requests`
- `POST /api/v1/requests`
- `GET /api/v1/requests/<request_code>`
- `POST /api/v1/requests/<request_code>/approve`
- `POST /api/v1/requests/<request_code>/reject`

### Expenses

- `GET /api/v1/expenses`
- `POST /api/v1/expenses`
- `GET /api/v1/expenses/summary`
- `GET /api/v1/expenses/<expense_code>`
- `POST /api/v1/expenses/<expense_code>/approve`
- `POST /api/v1/expenses/<expense_code>/reject`

### Users

- `GET /api/v1/users`
- `POST /api/v1/users`

### Reports

- `GET /api/v1/reports`
- `GET /api/v1/reports/<report_key>/export`

### Approvals

- `GET /api/v1/approvals`
- `GET /api/v1/approvals/metrics`
- `GET /api/v1/approvals/signature`
- `POST /api/v1/approvals/signature`
- `POST /api/v1/approvals/documents`
- `GET /api/v1/approvals/<document_code>`
- `GET /api/v1/approvals/<document_code>/download`
- `POST /api/v1/approvals/<document_code>/approve`
- `POST /api/v1/approvals/<document_code>/reject`

### Settings

- `GET /api/v1/settings`
- `GET /api/v1/settings/profile`
- `POST /api/v1/settings/profile`

---

## 11. قراردادهای مهم payload

### 11.1 Login response

```json
{
  "access_token": "jwt",
  "token_type": "bearer",
  "user": { "...": "..." }
}
```

### 11.2 Bootstrap payload

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
insights
expenseSummary
approvalMetrics
settingsCards
directories
```

### 11.3 Request serialized shape

فیلدهای مهم:

- `id`
- `title`
- `owner`
- `manager`
- `managerAssignees`
- `managerAssigneeIds`
- `priority`
- `status`
- `department`
- `deadline`
- `createdAt`
- `description`
- `attachmentsCount`
- `canApprove`

### 11.4 Expense serialized shape

- `id`
- `title`
- `description`
- `amount`
- `amountRaw`
- `category`
- `owner`
- `status`
- `progress`
- `department`
- `submittedAt`
- `invoiceName`
- `invoiceUrl`

### 11.5 Approval serialized shape

- `id`
- `title`
- `owner`
- `type`
- `status`
- `department`
- `uploadedAt`
- `risk`
- `summary`
- `assignees`
- `previewUrl`
- `downloadUrl`
- `previewKind`
- `signedSignature`
- `decisionNote`
- `bucket`
- `canApprove`

---

## 12. Bootstrap-first data strategy

### ایده

به جای اینکه frontend برای هر widget یک endpoint جدا بزند، backend یک payload نسبتاً کامل از snapshot سیستم می دهد.

### مزایا

- بارگذاری اولیه سریع تر برای UI
- ساده شدن store
- هماهنگی بیشتر بین dashboard و page lists

### هزینه ها

- payload بزرگ تر
- coupling بیشتر بین frontend و backend serialization
- نیاز به refresh کامل بعد از action های اصلی

---

## 13. جریان های فنی اصلی

### 13.1 ورود

```text
POST /auth/login
  -> verify password
  -> create JWT
  -> return current user

frontend
  -> save token
  -> GET /bootstrap
  -> hydrate store
```

### 13.2 ثبت درخواست

```text
frontend
  -> FormData
  -> POST /requests

backend
  -> validate manager / assignees / deadline / action
  -> create Request
  -> create timeline rows
  -> save attachments
  -> audit log
```

### 13.3 تایید درخواست

```text
POST /requests/<code>/approve
  -> visibility check
  -> permission check
  -> status = approved
  -> timeline append
  -> audit log
```

### 13.4 ثبت هزینه

```text
frontend FormData
  -> POST /expenses

backend
  -> validate payload
  -> save invoice file
  -> create Expense
  -> audit log
```

### 13.5 تایید سند با امضای دیجیتال

```text
POST /approvals/<code>/approve
  -> ensure approver assignment exists
  -> ensure signature exists
  -> mark assignment approved
  -> sign document file
  -> update document status
```

### 13.6 دانلود فایل محافظت شده

```text
frontend downloadProtectedFile()
  -> authorized fetch
  -> blob
  -> temporary object URL

backend /download
  -> access check
  -> file existence check
  -> FileResponse
```

---

## 14. طراحی فایل و media

### فایل های ذخیره شده

- پیوست های request
- فاکتور expense
- فایل سند approval

### روش ذخیره

- نام یکتا با `uuid4`
- ذخیره در `MEDIA_ROOT`

### نکته مهم

download و preview از طریق URL مستقیم عمومی انجام نمی شوند؛ frontend URL های نسبی را به origin backend resolve می کند و سپس با authorization fetch می گیرد.

---

## 15. گزارش گیری

### report catalog

Backend برای سه report اصلی catalog تولید می کند:

- requests
- expenses
- approvals

### export

- فرمت فعلی فقط `csv`
- نام فایل شامل report key و تاریخ روز است

---

## 16. داشبورد و aggregation

Backend در `build_bootstrap_payload()` داده های زیر را محاسبه می کند:

- active requests
- approval metrics
- month total
- year total
- expense chart for last 7 days
- request pipeline
- activities feed
- expense summary cards

این یعنی dashboard فعلی derived view از داده های عملیاتی است، نه ماژول تحلیلی مستقل.

---

## 17. خطاها و handling

### backend

- خطاها به صورت JSON با فیلد `detail` برمی گردند
- `401` برای token نامعتبر
- `403` برای نبود دسترسی
- `404` برای موجود نبودن entity
- `409` برای conflict state
- `422` برای validation issue

### frontend

- `authorizedFetch()` متن `detail` را استخراج می کند
- در `401`، session پاک می شود
- `state.lastError` برای نمایش خطا در UI استفاده می شود

---

## 18. initialization و seed

### startup behavior

در backend مکانیزم `startup_ready()` وجود دارد:

- در صورت نیاز migration اجرا می شود
- membership های سازمانی ایجاد می شوند
- اگر DB خالی باشد seed demo data اجرا می شود

### نتیجه

این پروژه local-first است و برای بالا آمدن سریع محیط توسعه طراحی شده است.

---

## 19. محدودیت های معماری فعلی

- store بسیار مرکزی است و با بزرگ شدن محصول نیاز به modularization دارد
- `bootstrap` payload با توسعه بیشتر ممکن است سنگین شود
- endpoint های edit/delete برای بسیاری از entity ها هنوز وجود ندارند
- audit log explorer در UI کامل نشده است
- event-driven notifications یا background jobs در معماری فعلی دیده نمی شود

---

## 20. پیشنهادهای فنی برای فاز بعد

- شکستن `workflowHub.js` به چند store ماژولی
- افزودن DTO/schema tests برای serialization
- جداسازی service layer مربوط به requests/expenses/approvals
- افزودن update endpoints برای users/settings entities
- اضافه کردن pagination و filtering در backend list endpoints
- اضافه کردن report formats beyond CSV
- اضافه کردن object storage abstraction برای media

---

## 21. جمع بندی

معماری فعلی پروژه برای یک سامانه داخلی سازمانی سبک تا متوسط مناسب است:

- backend منبع حقیقت است
- frontend تجربه کاربری modal-first و dashboard-driven می سازد
- access control هم نقش محور است، هم بخش محور
- approval flow از فایل خام تا فایل امضاشده را end-to-end پوشش می دهد

مهم ترین ارزش معماری فعلی این است که جریان های حیاتی محصول همین حالا به صورت واقعی و قابل ردیابی در کد پیاده شده اند، نه صرفاً در سطح UI mock.
