# سند جامع طراحی و توسعه ماژول Tasking کارنومند

**محصول:** کارنومند — سامانه مدیریت عملیات سازمانی  
**ماژول جدید:** Tasking / مدیریت تسک و ظرفیت کاری کارکنان  
**نوع سند:** Product + UX + Business Logic + Data Model + API + Acceptance Criteria  
**نسخه:** 1.0  
**هدف سند:** تحویل مستقیم به Agent توسعه‌دهنده برای پیاده‌سازی کامل، داینامیک، رسپانسیو و منطبق با معماری و Design System فعلی کارنومند

---

## 0) دستور اجرایی برای Agent

این ماژول نباید به‌صورت یک صفحه جدا و غیرهمگون به پروژه اضافه شود. باید کاملاً داخل ساختار فعلی کارنومند ادغام شود و از همان الگوهای موجود پروژه برای موارد زیر استفاده کند:

- Authentication و Session فعلی
- Organization / مجموعه فعلی
- User، Role، Department، Position و Direct Manager فعلی
- Permission / Access Control فعلی
- الگوی API، Serializer/DTO، Error Handling و Pagination فعلی
- سیستم Notification فعلی، اگر وجود دارد
- File/Cloud attachment فعلی
- Audit Trail و تاریخچه عملیات فعلی
- Design Tokens، رنگ‌ها، تایپوگرافی، Radius، Shadow، Spacing، Button، Input، Modal، Drawer، Table و Badge فعلی
- RTL فارسی و تاریخ/زمان فعلی سامانه
- ساختار Responsive فعلی

**ممنوع:** ساخت Theme جدید، رنگ مستقل، Permission موازی، User Table موازی، Organization مستقل، سیستم فایل جدا، تاریخ‌ساز جدا یا منطق احراز هویت جدید.

در تمام نقاطی که داده‌ای در سیستم فعلی موجود است، باید از همان منبع حقیقت (Single Source of Truth) استفاده شود.

---

# 1) هدف کسب‌وکاری ماژول

ماژول Tasking باید مشکل واقعی «مدیریت کار روزانه، ظرفیت کاری، ارجاع، نظارت، زمان صرف‌شده و ارزیابی انجام کار» را داخل شرکت حل کند.

این ماژول قرار نیست فقط To-Do List باشد. باید یک **Operational Task & Workforce Capacity System** باشد که بتواند:

1. هر کارمند بداند امروز دقیقاً چه کارهایی، با چه اولویتی و در چه ترتیبی باید انجام دهد.
2. تسک‌ها براساس ساعت کاری، ظرفیت قابل برنامه‌ریزی، اولویت، Deadline و زمان تخمینی به روزهای کاری تخصیص داده شوند.
3. مدیر بتواند بدون Micromanagement وضعیت واقعی کار تیم را ببیند.
4. تسک ارجاع‌شده قبل از ورود به برنامه کاری شخص، قابلیت پذیرش/رد یا درخواست توضیح داشته باشد.
5. کاربر بتواند Start / Pause / Resume / Complete کند و زمان واقعی ثبت شود.
6. ناظر یا مدیر مسئول نتیجه را تأیید یا برای اصلاح برگرداند.
7. تمام فعالیت‌ها قابل گزارش، Audit و پیگیری باشند.
8. مکالمات مرتبط با هر تسک داخل همان Task Context باقی بمانند.
9. ظرفیت افراد کمتر یا بیشتر از حد مطلوب به‌صورت مدیریتی قابل مشاهده باشد.
10. سیستم در Desktop، Tablet و Mobile واقعاً کاربردی باشد.

---

# 2) تصمیم‌های پایه و قواعد قطعی

## 2.1 ظرفیت هدف و سقف برنامه‌ریزی

برای رفع ابهام بین 80% و 90%، دو مقدار جدا تعریف شود:

- **Target Utilization = 80%** به‌صورت پیش‌فرض
- **Maximum Planned Utilization = 90%** به‌صورت پیش‌فرض

هر دو مقدار در تنظیمات مجموعه قابل تغییر باشند، مثلاً:

- Target: بین 50% تا 95%
- Maximum: بین Target تا 100%

هدف 80% یعنی برنامه روزانه تا این حد «نرمال» تلقی می‌شود. بازه 80 تا 90 درصد «فشرده ولی مجاز» است. بیشتر از 90 درصد «Over Capacity» محسوب می‌شود و نیاز به تصمیم آگاهانه دارد.

### مثال
اگر ساعت کاری خالص یک کارمند 8 ساعت باشد:

- ظرفیت هدف: 6 ساعت و 24 دقیقه
- سقف برنامه‌ریزی: 7 ساعت و 12 دقیقه

برای گزارش روزانه:

- کمتر از 80% = Under Planned
- 80% تا 90% = Healthy / Target Met
- 90% تا 100% = High Load
- بیشتر از 100% = Overloaded

تمام این Thresholdها باید Configuration-driven باشند، نه Hard-coded.

---

## 2.2 زمان کاری قابل برنامه‌ریزی

ظرفیت هر روز فقط از `working_minutes` محاسبه نشود؛ باید این موارد نیز در نظر گرفته شود:

- ساعت کاری تعریف‌شده برای مجموعه
- برنامه اختصاصی کارمند، اگر Override دارد
- روزهای کاری هفته
- تعطیلات رسمی/تعطیلی سازمانی تعریف‌شده
- مرخصی تاییدشده، در صورت وجود Integration با Requests/Attendance
- شیفت نیمه‌وقت یا ساعت کاری خاص کارمند
- Break غیرقابل برنامه‌ریزی، اگر مدیر آن را در تنظیمات لحاظ کند

فرمول پیشنهادی:

`effective_work_minutes = scheduled_work_minutes - approved_leave_minutes - blocked_calendar_minutes`

`target_task_minutes = effective_work_minutes * target_utilization_percent`

`max_planned_minutes = effective_work_minutes * max_utilization_percent`

---

## 2.3 تقسیم تسک بین روزها

یک Task واحد باید بتواند دارای چند **Task Segment / Allocation** باشد.

مثال:

- امروز 70% ظرفیت هدف پر شده است.
- Task جدید معادل 20% یک روز است.
- برای رسیدن به 80%، فقط 10% امروز آزاد است.
- 10% باقی‌مانده باید اولین Slot مناسب روز کاری بعد قرار بگیرد.

در UI همچنان یک Task واحد دیده می‌شود ولی کنار آن نمایش داده شود:

- «بخشی از تسک امروز»
- «ادامه: فردا»

و در جزئیات:

- کل زمان تخمینی: 96 دقیقه
- برنامه امروز: 48 دقیقه
- برنامه فردا: 48 دقیقه

Segmentها برای گزارش و Timer نیز باید قابل تفکیک باشند، ولی Task Entity واحد باقی بماند.

---

## 2.4 اولویت‌بندی پویا

ترتیب Taskها فقط `created_at` نباشد.

Priority Levels:

1. Critical / بحرانی
2. High / بالا
3. Medium / متوسط
4. Normal / عادی
5. Low / پایین

رتبه‌بندی Scheduler باید به‌صورت کلی این عوامل را در نظر بگیرد:

- Priority
- Due Date / Deadline proximity
- Explicit manual pin
- Blocker state
- Assignment accepted time
- Task age
- Dependency readiness
- Overdue status
- Sequence lock در صورت نیاز

اگر بعد از 10 Task یک Task با اولویت High یا Critical ایجاد شود، Scheduler باید آن را به اولین جای ممکن منتقل کند؛ مگر این‌که Task فعلی در حال اجرا باشد یا Dependency اجازه ندهد.

**Task در حال اجرا نباید به‌صورت ناگهانی با Reorder خودکار متوقف شود.** Reorder از Slot بعدی اعمال شود.

---

# 3) معماری اطلاعات ماژول در پنل کاربر

در Sidebar / Navigation اصلی پنل، آیتم جدید:

**تسکینگ**

با Badge شمارنده فقط در صورت وجود آیتم نیازمند اقدام:

- ارجاع جدید
- درخواست Review
- تسک برگشتی
- Mention خوانده‌نشده

صفحه Tasking دارای Header ثابت و سه بخش سطح اول باشد:

1. **کارهای من**
2. **ارجاع‌ها**
3. **نظارت**

در بخش «کارهای من» زیرتب‌ها:

- امروز
- پیش‌رو
- در حال انجام
- در انتظار بررسی
- برگشتی / نیازمند اصلاح
- بسته‌شده
- همه

در بخش «ارجاع‌ها» زیرتب‌ها:

- نیازمند پاسخ
- پذیرفته‌شده
- ردشده / بازگردانده‌شده
- همه ارجاع‌ها

در بخش «نظارت» زیرتب‌ها:

- نیازمند بررسی
- در حال انجام تیم
- تأخیرها
- تکمیل‌شده
- همه تحت نظارت

**مدیر مستقیم:** همه Taskهای کارمندان مستقیم او به‌صورت خودکار در «نظارت» قابل مشاهده باشند، حتی اگر در Task ناظر دستی تعیین نشده باشد؛ مشروط به Permission سازمانی.

---

# 4) نقش‌ها و Permission Matrix

از Role System موجود استفاده شود و Permissionهای Granular جدید اضافه شوند.

پیشنهاد Permission Keys:

- `tasking.view_own`
- `tasking.create_own`
- `tasking.create_for_others`
- `tasking.assign`
- `tasking.accept_assignment`
- `tasking.reject_assignment`
- `tasking.edit_own_unstarted`
- `tasking.edit_assigned`
- `tasking.change_estimate`
- `tasking.start_pause`
- `tasking.complete`
- `tasking.review`
- `tasking.observe`
- `tasking.comment`
- `tasking.attach_file`
- `tasking.reorder_manual`
- `tasking.override_capacity`
- `tasking.view_team`
- `tasking.view_department`
- `tasking.view_org`
- `tasking.view_reports`
- `tasking.export_reports`
- `tasking.manage_settings`

### پیش‌فرض پیشنهادی

**کارمند**
- مشاهده Taskهای خود
- ساخت Task شخصی
- قبول/رد ارجاع
- اجرای Timer
- ثبت Completion
- Chat و Attachment روی Taskهای دارای دسترسی

**مدیر**
- تمام موارد کارمند
- ساخت/ارجاع برای اعضای مجاز
- مشاهده تیم مستقیم
- Review و Approve/Reject
- تنظیم Reorder محدود
- گزارش تیم

**مدیر ارشد / مدیرعامل**
- مشاهده گسترده‌تر طبق Scope
- گزارش واحد/سازمان
- Capacity Override در صورت Permission

**HQ**
- فقط در صورتی که معماری فعلی HQ اجازه داده، پشتیبانی پلتفرمی و مشاهده کنترل‌شده؛ دسترسی به محتوای Task باید طبق سیاست Privacy محصول باشد.

---

# 5) تنظیمات مجموعه — Tasking Settings

مسیر پیشنهادی:

`تنظیمات مجموعه > تسکینگ و ظرفیت کاری`

صفحه Settings باید بخش‌بندی شود.

## 5.1 برنامه کاری

فیلدها:

- فعال/غیرفعال بودن Tasking برای مجموعه
- Timezone مجموعه
- روزهای کاری هفته
- ساعت شروع هر روز
- ساعت پایان هر روز
- Break duration
- آیا Break از ظرفیت کم شود؟
- امکان تعریف ساعت متفاوت برای هر روز
- امکان Override در سطح کارمند
- شروع هفته در گزارش‌ها

## 5.2 ظرفیت برنامه‌ریزی

- Target Utilization % — پیش‌فرض 80
- Max Planned Utilization % — پیش‌فرض 90
- اجازه Overbooking توسط مدیر؟ بله/خیر
- Overbooking نیازمند Reason؟ بله/خیر
- هشدار Under Planned از چه درصدی؟ پیش‌فرض 80
- هشدار Overload از چه درصدی؟ پیش‌فرض 100

## 5.3 زمان‌بندی و اولویت

- Scheduler Mode: Automatic / Assisted / Manual
- Allow Task Splitting Across Days
- Minimum Segment Duration، مثال 15 دقیقه
- Round estimate to: 5 / 10 / 15 / 30 دقیقه
- Auto-prioritize overdue tasks
- Auto-prioritize critical tasks
- Auto-move high priority to top
- Respect manually pinned tasks
- Auto schedule only working days

## 5.4 ارجاع و پذیرش

- Task assignment requires acceptance: On/Off
- Assignment acceptance timeout، مثلا 4 ساعت کاری
- بعد از Timeout: remind / notify manager / auto-accept / no action
- Assignee can reject assignment: On/Off
- Rejection reason required: On/Off

## 5.5 Review

- Completion requires reviewer approval: On/Off
- Default reviewer:
  - Direct Manager
  - Task Observer
  - Task Creator
  - Custom rule
- اگر چند Reviewer وجود دارند:
  - Any one approval
  - All approvals
  - Sequential approval

## 5.6 Timer

- Timer required for Task completion؟
- Allow multiple active timers for one user؟ پیش‌فرض No
- Allow manual time entry؟
- Require reason for manual correction؟
- Auto pause timer outside working hours؟
- Idle timeout، اگر سیستم چنین قابلیت قابل‌اعتمادی دارد؛ در غیر این صورت نسازید.

## 5.7 نمایش و گزارش

- نمایش utilization برای کارمند خودش
- نمایش utilization همکاران
- نمایش time estimate برای همکاران
- گزارش روزانه / هفتگی / ماهانه
- Retention policy برای Task Chat و Attachments، اگر محصول نیاز دارد

---

# 6) Data Model پیشنهادی

نام مدل‌ها را با Convention پروژه تطبیق دهید.

## 6.1 Task

فیلدهای اصلی:

- `id`
- `organization_id`
- `code` — مثال `TSK-1405-002841`
- `title`
- `description`
- `category_id` nullable
- `department_id` nullable
- `project_id` nullable، فقط اگر مفهوم Project در سیستم وجود دارد
- `creator_id`
- `owner_id` — مسئول اصلی اجرای Task
- `direct_manager_id_snapshot` — Snapshot برای Audit، نه منبع مجوز دائمی
- `priority`
- `status`
- `estimated_minutes`
- `original_estimated_minutes`
- `remaining_estimated_minutes`
- `actual_minutes`
- `due_at` nullable
- `start_not_before` nullable
- `scheduled_start_at` nullable
- `scheduled_end_at` nullable
- `completed_at` nullable
- `closed_at` nullable
- `review_required`
- `review_status`
- `reviewer_rule`
- `is_pinned`
- `is_recurring`
- `recurrence_rule` nullable
- `source_type` — self / assigned / request / system / recurring
- `source_reference_id` nullable
- `confidentiality_level` — normal / restricted / confidential در صورت نیاز محصول
- `created_at`
- `updated_at`
- `deleted_at` یا archive strategy مطابق پروژه
- `version` برای optimistic concurrency

## 6.2 TaskAssignment

برای پشتیبانی از ارجاع رسمی:

- `id`
- `task_id`
- `assignee_id`
- `assigned_by_id`
- `status`: pending / accepted / rejected / cancelled
- `assigned_at`
- `responded_at`
- `response_reason`
- `previous_assignee_id` nullable

اگر فقط یک Owner نهایی داریم، Assignment History جدا نگه داشته شود.

## 6.3 TaskObserver

- `task_id`
- `user_id`
- `observer_type`: explicit / direct_manager / department_manager / reviewer / mentioned
- `can_review`
- `can_comment`
- `can_view_time`
- timestamps

**توجه:** Direct Manager بهتر است Dynamic Permission باشد، ولی برای Audit می‌توان relation snapshot هم نگه داشت.

## 6.4 TaskAllocation / TaskSegment

- `id`
- `task_id`
- `user_id`
- `work_date`
- `planned_minutes`
- `sequence`
- `segment_status`
- `scheduled_start_time` nullable
- `scheduled_end_time` nullable
- `is_over_capacity`
- `created_by_scheduler`
- `locked_by_user`
- timestamps

## 6.5 TaskTimeEntry

هر Start/Pause به Entry تبدیل شود:

- `id`
- `task_id`
- `user_id`
- `allocation_id` nullable
- `started_at`
- `ended_at` nullable
- `duration_seconds`
- `entry_type`: timer / manual / adjustment
- `created_by_id`
- `adjustment_reason` nullable
- `is_active`
- `device/session metadata` فقط اگر سیاست امنیتی اجازه می‌دهد

Constraint بسیار مهم:

- به‌صورت پیش‌فرض هر user فقط یک active time entry در کل Tasking داشته باشد.

## 6.6 TaskReview

- `id`
- `task_id`
- `reviewer_id`
- `status`: pending / approved / changes_requested / rejected
- `comment`
- `reviewed_at`
- `iteration_no`

## 6.7 TaskComment

- `id`
- `task_id`
- `author_id`
- `parent_id` nullable برای Reply
- `body`
- `message_type`: comment / system_event / review_note
- `created_at`
- `edited_at`
- `deleted_at`

## 6.8 TaskMention

- `comment_id`
- `mentioned_user_id`
- `read_at`

## 6.9 TaskAttachment

در صورت وجود File System فعلی از Entity Attachment عمومی استفاده شود. در غیر این صورت:

- task_id
- uploader_id
- file reference
- original_name
- size
- mime_type
- visibility
- created_at

## 6.10 TaskDependency

برای نسخه کامل حرفه‌ای:

- `task_id`
- `depends_on_task_id`
- relation: blocks / related

Task blocked نباید به‌صورت عادی Start شود مگر Override مجاز.

## 6.11 TaskActivity / Audit Event

هر تغییر مهم ثبت شود:

- task_created
- assigned
- assignment_accepted
- assignment_rejected
- priority_changed
- estimate_changed
- scheduled
- started
- paused
- resumed
- completed_submitted
- review_approved
- review_changes_requested
- reopened
- observer_added
- observer_removed
- due_date_changed
- comment_added
- attachment_added
- cancelled

فیلدها:

- actor
- timestamp
- before snapshot یا diff
- after snapshot یا diff
- metadata

---

# 7) State Machine قطعی

Task Statusهای پیشنهادی:

1. `DRAFT`
2. `PENDING_ACCEPTANCE`
3. `SCHEDULED`
4. `UPCOMING`
5. `IN_PROGRESS`
6. `PAUSED`
7. `BLOCKED`
8. `PENDING_REVIEW`
9. `CHANGES_REQUESTED`
10. `COMPLETED`
11. `CANCELLED`
12. `OVERDUE` بهتر است Flag مشتق‌شده باشد، نه Status مستقل

### Transitionهای مجاز

- DRAFT -> PENDING_ACCEPTANCE
- DRAFT -> SCHEDULED، برای self task یا assignment بدون acceptance
- PENDING_ACCEPTANCE -> SCHEDULED، با Accept
- PENDING_ACCEPTANCE -> CANCELLED/REASSIGN، با Reject طبق سیاست
- SCHEDULED/UPCOMING -> IN_PROGRESS
- IN_PROGRESS -> PAUSED
- PAUSED -> IN_PROGRESS
- IN_PROGRESS/PAUSED -> PENDING_REVIEW
- PENDING_REVIEW -> COMPLETED
- PENDING_REVIEW -> CHANGES_REQUESTED
- CHANGES_REQUESTED -> SCHEDULED یا UPCOMING با همان Task و iteration جدید
- COMPLETED فقط با Permission خاص Reopen شود

تمام Transitionها باید Server-side validate شوند.

---

# 8) منطق Scheduler و Capacity Engine

این بخش مهم‌ترین Business Logic ماژول است.

## 8.1 ورودی Scheduler

برای یک User و بازه تاریخ:

- Work schedule
- Day capacity
- Existing allocations
- Active leave / unavailable periods
- Accepted tasks
- Priority
- Due date
- Remaining estimate
- Dependencies
- Pinned order
- Manual locked allocations

## 8.2 خروجی Scheduler

لیست Segmentهای روزانه با:

- Task
- Date
- Planned minutes
- Sequence
- Utilization before/after
- Spillover indication

## 8.3 الگوریتم پایه

1. Taskهای غیرقابل اجرا را حذف/Skip کن:
   - cancelled
   - completed
   - pending acceptance
   - blocked by dependency
2. Taskهای locked/pinned را در جای معتبر نگه دار.
3. باقی Taskها را بر اساس Priority Score مرتب کن.
4. از نزدیک‌ترین روز کاری شروع کن.
5. برای هر روز `target_remaining_minutes` را محاسبه کن.
6. Task را تا جای ممکن در ظرفیت هدف قرار بده.
7. اگر بخشی باقی ماند و splitting فعال است، remainder را به اولین روز کاری بعد منتقل کن.
8. اگر Task به دلیل Deadline باید زودتر انجام شود، می‌تواند تا سقف `max_planned_minutes` وارد همان روز شود و UI حالت High Load نشان دهد.
9. بالاتر از max فقط در صورت manual override با ثبت reason.
10. بعد از هر Task Creation/Edit/Acceptance/Priority Change/Estimate Change/Leave Change، Recompute کنترل‌شده انجام شود.

## 8.4 Priority Score پیشنهادی

از Formula قابل تنظیم یا ثابت نسخه اول استفاده شود:

- Critical: +1000
- High: +700
- Medium: +400
- Normal: +200
- Low: +50
- Overdue: +800
- Due today: +500
- Due tomorrow: +300
- Pinned: +2000
- Age bonus: محدود و تدریجی

**تأکید:** این Score فقط برای Sort است و نباید در UI به کاربر به شکل عدد خام نشان داده شود.

## 8.5 تغییر زمان تخمینی

اگر کاربر/مدیر estimate را تغییر دهد:

- اگر Task شروع نشده: reschedule کامل remainder
- اگر Task شروع شده: actual elapsed حفظ شود و فقط remaining estimate تغییر کند
- اگر estimate کاهش یابد: Slotهای آزاد شده به Task بعدی تخصیص یابد
- اگر افزایش یابد: remainder ممکن است به روز بعد Spill شود
- Activity Event ثبت شود
- در صورت تغییر بزرگ، مثلاً بیش از 30%، Reason اجباری شود (قابل تنظیم)

---

# 9) صفحه اصلی «تسکینگ» — Desktop

## 9.1 Header

المان‌ها:

- عنوان: «تسکینگ»
- توضیح کوتاه: «برنامه روزانه، زمان اجرا و وضعیت کارهای شما»
- Date Navigator:
  - روز قبل
  - امروز
  - روز بعد
  - Date picker
- CTA اصلی: «+ تسک جدید»
- Search
- Filter button
- View toggle در صورت نیاز: List / Compact Timeline

## 9.2 Daily Capacity Summary

در ابتدای «امروز» یک Summary Bar بسیار واضح:

- ساعت کاری امروز: 8:00
- ظرفیت هدف: 6:24
- برنامه‌ریزی‌شده: 5:40
- انجام‌شده واقعی: 3:12
- باقی‌مانده برنامه: 2:28
- Utilization: 71%

Progress Bar چند وضعیت:

- زیر Target
- Target reached
- Near max
- Over capacity

رنگ‌ها باید از Semantic Tokens پروژه استفاده شوند؛ Color hard-code ممنوع.

## 9.3 Quick Stats

حداکثر 4 Metric کوچک:

- کارهای امروز
- زمان باقی‌مانده
- نیازمند بررسی/پاسخ
- تکمیل امروز

## 9.4 Task List Row

هر ردیف Task شامل:

- Priority Dot
- Task code
- عنوان
- Status Badge
- Project/Department/Category کوچک در صورت وجود
- Assignee Avatar + name در صفحات مدیریتی
- Observer indicator
- Estimated time
- Planned segment time today
- Actual tracked time
- Due date با حالت نسبی و تاریخ دقیق در tooltip/detail
- Spillover badge: «ادامه فردا»
- Mention/unread count
- Attachment indicator
- Timer indicator
- Action buttons:
  - Start / Resume
  - Pause
  - Complete
  - More menu

Click روی بخش اصلی Row -> **Task Detail Modal/Drawer** باز شود.

### نمایش تاریخ

در لیست:
- «امروز، ۱۴:۳۰»
- «فردا»
- «۲ روز دیگر»
- «۳ روز عقب‌افتاده»

در Detail همیشه تاریخ کامل نیز نشان داده شود:
- `چهارشنبه ۲۱ مرداد ۱۴۰۵، ساعت ۱۴:۳۰`

در لایه داده، Timestamp استاندارد UTC ذخیره و در UI براساس Timezone مجموعه نمایش داده شود.

---

# 10) Mobile UX

در Mobile جدول استفاده نشود. Taskها به Card Row فشرده تبدیل شوند.

## ساختار هر Card

ردیف 1:
- Priority Dot
- عنوان
- Status

ردیف 2:
- زمان تخمینی
- Due
- «ادامه فردا» در صورت Split

ردیف 3:
- Progress / Timer

ردیف 4:
- CTA اصلی Contextual:
  - شروع
  - توقف
  - ادامه
  - ارسال برای بررسی

More actions در Bottom Sheet.

Header موبایل:

- عنوان
- Date selector compact
- دکمه +
- Filter

زیرتب‌ها Horizontal scroll یا Segmented Control قابل لمس.

Task Detail در Mobile بهتر است Full-height Drawer/Bottom Sheet باشد، نه Modal کوچک وسط صفحه.

Touch targets حداقل 44px.

---

# 11) Modal «افزودن تسک»

Modal باید چند بخش واضح داشته باشد، نه یک فرم شلوغ.

## 11.1 اطلاعات اصلی

### فیلدهای اجباری

- عنوان تسک `title`
- مسئول انجام `assignee`
- اولویت `priority`
- زمان تخمینی `estimated_duration`

### فیلدهای پیشنهادی

- توضیحات کامل
- بخش / Department
- دسته‌بندی
- پروژه، اگر وجود دارد
- تاریخ شروع مجاز
- Deadline
- ناظر/ناظران
- وابستگی‌ها
- Attachment
- Tags

## 11.2 انتخاب مسئول

Company Member Picker با:

- Search
- Avatar
- نام و نام خانوادگی
- سمت
- بخش
- وضعیت فعال
- ظرفیت امروز، مثلاً «72% پر» فقط برای افراد دارای Permission دیدن ظرفیت

فیلتر:

- اعضای بخش من
- زیردستان مستقیم
- همه افراد مجاز

کاربر غیرفعال قابل انتخاب نباشد.

## 11.3 ناظر

- Multi select
- پیشنهاد خودکار Direct Manager مسئول
- گزینه «مدیر مستقیم مسئول به‌صورت خودکار ناظر باشد»
- Reviewer می‌تواند از Observer جدا باشد.

## 11.4 زمان تخمینی

UX مناسب:

- Hours + Minutes
- Quick chips: 15m / 30m / 1h / 2h / 4h
- نمایش معادل ظرفیت:
  - «این تسک حدود 12.5% از یک روز کاری 8 ساعته است.»

## 11.5 Scheduling Preview

قبل از ثبت، یک Preview کوچک و بسیار مهم:

مثال:

> زمان تخمینی: 2 ساعت  
> ظرفیت امروز دامون: 1 ساعت آزاد تا Target  
> برنامه پیشنهادی: 1 ساعت امروز + 1 ساعت فردا

اگر High Priority باعث جابه‌جایی Taskها شود:

> «این تسک با اولویت بالا، قبل از 3 تسک عادی قرار می‌گیرد.»

## 11.6 Acceptance

اگر برای فرد دیگری ساخته می‌شود و سیاست Acceptance فعال است:

- Badge: «نیازمند تأیید مسئول»
- بعد از Create وارد Pending Assignment می‌شود، نه برنامه قطعی.

## 11.7 CTAها

- ثبت تسک
- ثبت و ایجاد تسک بعدی، فقط برای مدیر/Power user
- انصراف

Validation پیام‌ها فارسی، دقیق و inline باشند.

---

# 12) «ارجاع‌ها» و شمارنده

در Tab تسکینگ Badge شمارنده‌ای نمایش داده شود:

`ارجاع‌ها 3`

این Count فقط Pending action را بشمارد.

## Row ارجاع

- عنوان
- ارجاع‌دهنده
- بخش
- اولویت
- estimate
- deadline
- زمان ارجاع
- خلاصه توضیح
- Scheduling impact preview

CTAها:

- «پذیرفتن»
- «رد کردن»
- «مشاهده جزئیات»

### Accept

با Accept:

1. assignment status = accepted
2. owner تثبیت می‌شود
3. Scheduler اجرا می‌شود
4. Task در «کارهای من» قرار می‌گیرد
5. Creator و Observerها Notification می‌گیرند
6. Activity ثبت می‌شود

### Reject Modal

فیلد:

- دلیل رد — اجباری اگر setting روشن است
- پیشنهاد ارجاع به فرد دیگر، فقط اگر Permission دارد

CTA:
- «رد ارجاع»

---

# 13) بخش «نظارت»

این بخش باید برای Manager واقعاً کاربردی باشد، نه صرفاً list تکراری.

## 13.1 منابع ورود Task به نظارت

Task در صورتی برای یک نفر در بخش نظارت ظاهر شود که:

- explicit observer است
- reviewer است
- direct manager صاحب Task است و policy اجازه می‌دهد
- department manager است و scope دارد
- mention شده ولی فقط mention به‌تنهایی Task را وارد «نظارت دائمی» نکند؛ در Notification باشد مگر کاربر Follow کند

## 13.2 کارت Summary

- نیازمند بررسی: 5
- در حال انجام: 18
- عقب‌افتاده: 3
- برگشتی: 2

## 13.3 فیلترها

- کارمند
- بخش
- وضعیت
- اولویت
- Deadline
- Under/Over capacity
- نیازمند Review
- فقط Direct Reports

## 13.4 Row مدیریتی

علاوه بر Task fields:

- Owner
- Progress by time
- Estimate vs actual
- planned date
- current timer state
- Review status

---

# 14) Task Detail Modal / Drawer

کلیک روی هر Task باید Detail را باز کند.

Desktop:
- Modal بزرگ یا Right-side Drawer مطابق Pattern پروژه

Mobile:
- Full screen / full-height sheet

## 14.1 Header

- Priority Dot + Priority label
- Task title
- Task code
- Status
- More menu
- Close

## 14.2 Quick Info

- مسئول
- سازنده
- ناظرها
- Reviewer
- بخش
- Category/Project
- Created at
- Due date
- Estimated time
- Actual time
- Remaining estimate
- برنامه امروز / روزهای بعد

## 14.3 Actions

Context-aware:

- Start
- Pause
- Resume
- Complete & Send for Review
- Edit Estimate
- Reassign
- Add Observer
- Change Priority
- Change Due Date
- Cancel

Action نامعتبر نباید نمایش داده شود یا Disabled با دلیل واضح باشد.

## 14.4 Description

Rich text محدود و امن یا Textarea formatting مطابق امکانات پروژه.

## 14.5 Scheduling Section

Timeline روزهای تخصیص:

- امروز — 45 دقیقه
- فردا — 1 ساعت
- شنبه — 30 دقیقه

برای هر Segment:
- planned duration
- status
- actual tracked

## 14.6 Activity Timeline

نمونه:

- 09:20 — تسک توسط علی رضایی ایجاد شد.
- 09:21 — به دامون ارجاع شد.
- 09:34 — ارجاع پذیرفته شد.
- 10:02 — اجرای تسک شروع شد.
- 10:48 — اجرای تسک متوقف شد؛ 46 دقیقه ثبت شد.
- 12:10 — زمان تخمینی از 90 به 120 دقیقه تغییر کرد.

## 14.7 Chat داخلی

در پایین یا Tab جدا:

- پیام‌ها
- Reply
- Mention `@`
- Attachment
- timestamp
- read/unread
- system event separator

افراد مجاز:

- owner
- creator
- observers
- reviewers
- managers with scope

هر Comment باید server-authorized باشد.

---

# 15) Timer UX و منطق واقعی زمان

## 15.1 شروع

با Start:

- اگر Timer فعال دیگری وجود ندارد -> شروع
- اگر وجود دارد -> Modal:

> «در حال حاضر تایمر «بررسی قرارداد فروش» فعال است. برای شروع این تسک، تایمر فعلی متوقف شود؟»

CTA:
- توقف قبلی و شروع این تسک
- انصراف

## 15.2 نمایش Timer

در Row:

- `00:37:12`
- Status: «در حال اجرا»

در Header global پنل نیز پیشنهاد می‌شود یک compact active timer نمایش داده شود تا کاربر در صفحات دیگر هم Task فعال را ببیند، اگر با معماری محصول سازگار است.

## 15.3 توقف

Pause فقط TimeEntry را می‌بندد و Task به PAUSED می‌رود.

## 15.4 تغییر زمان

Modal «ویرایش زمان تخمینی»:

- زمان اولیه
- زمان مصرف‌شده
- زمان باقی‌مانده پیشنهادی
- estimate جدید
- reason

## 15.5 Manual Time Entry

اگر فعال است:

- تاریخ
- از ساعت
- تا ساعت یا duration
- توضیح
- reason

نباید overlap نامعتبر با TimeEntryهای موجود ایجاد کند مگر policy اجازه دهد.

---

# 16) پایان Task و Review Flow

## 16.1 Complete Modal

وقتی کارمند «پایان / ارسال برای بررسی» را می‌زند:

- خلاصه زمان:
  - تخمین: 2h
  - واقعی: 2h 18m
- توضیح نتیجه / Delivery note
- Attachment نهایی اختیاری/اجباری بر اساس Task
- Checklist در صورت وجود
- CTA: «ارسال برای بررسی»

Status -> `PENDING_REVIEW`

## 16.2 Review Modal برای مدیر/ناظر

نمایش:

- عنوان
- Description
- Delivery note
- Attachments
- Estimate vs Actual
- Timeline
- Chat اخیر

CTA:

- تأیید و بستن
- درخواست اصلاح

### تأیید

- Review approved
- Task -> COMPLETED
- closed_at ثبت شود
- Allocationهای باقیمانده آزاد شوند
- Report update شود

### درخواست اصلاح

Modal:

- دلیل اصلاح — اجباری
- اولویت اصلاح
- estimate اضافی پیشنهادی یا حفظ زمان فعلی
- Deadline جدید اختیاری

بعد:

- iteration_no + 1
- status -> CHANGES_REQUESTED سپس schedule شود
- Task با **همان هویت، عنوان، attachments، chat و history** برگردد
- در برنامه کارمند در اولین Slot معتبر مطابق Priority قرار گیرد
- اگر قبلاً جای مشخصی داشته و هنوز منطقی است، Scheduler تلاش کند relative priority آن را حفظ کند
- Reason prominently داخل Task نمایش داده شود

**Task جدید کپی نشود.** همان Task با Iteration جدید ادامه یابد.

---

# 17) وضعیت‌های لیست «کارهای من»

## امروز
Segmentهای امروز + Task فعال

## پیش‌رو
Taskهای برنامه‌ریزی‌شده روزهای آینده

## در حال انجام
IN_PROGRESS + PAUSED + BLOCKED قابل اقدام

## در انتظار بررسی
PENDING_REVIEW

## برگشتی
CHANGES_REQUESTED

## بسته‌شده
COMPLETED + CANCELLED با Filter

## همه
تمام Taskهای کاربر با Search/Filter/Pagination

---

# 18) Filters و Search

Search روی:

- عنوان
- Code
- توضیح محدود
- Creator
- Assignee
- Department
- Tag

Filters:

- Status
- Priority
- Date range
- Due status
- Assignee
- Observer
- Department
- Created by
- Has attachment
- Has unread messages
- Overdue
- Split across days
- Review required

Filter state بهتر است در URL Query نگه‌داری شود تا قابل Share/Back navigation باشد.

---

# 19) Notificationها

Notificationهای مهم:

- Task به شما ارجاع شد
- Assignment پذیرفته شد
- Assignment رد شد
- در Task منشن شدید
- Task شما توسط مدیر تغییر اولویت گرفت
- Deadline تغییر کرد
- Task نزدیک Deadline است
- Task Overdue شد
- کارمند Task را برای Review ارسال کرد
- Task تأیید شد
- Task برای اصلاح برگشت
- Comment جدید روی Task
- ظرفیت روز از Max عبور کرد

Notification باید Deep Link مستقیم به Task داشته باشد.

Spam Control:

- تغییرات کوچک Scheduler نباید Notification جدا بدهد.
- Mention، Assignment و Review همیشه High relevance هستند.

---

# 20) گزارش‌ها — تب جدید «تسکینگ»

مسیر:

`گزارشات > تسکینگ`

## 20.1 Header Report

- Date range
- Department
- User
- Status
- Priority
- Export CSV

## 20.2 KPI Cards

- تعداد کارکنان فعال در بازه
- Target met users
- Under target users
- High load users
- Overloaded users
- Task completion rate
- Average estimate accuracy
- Overdue tasks
- Pending reviews

## 20.3 Capacity Distribution

چهار گروه کلیک‌پذیر:

### کمتر از حد هدف
مثلاً 12 نفر

### در محدوده هدف
مثلاً 28 نفر

### بار کاری بالا
مثلاً 6 نفر

### بیش از ظرفیت
مثلاً 3 نفر

کلیک روی هر گروه -> Drilldown Drawer/Table.

## 20.4 Drilldown هر کارمند

- نام
- سمت
- بخش
- ساعت کاری موثر
- Planned minutes
- Target minutes
- Actual tracked
- Utilization %
- Completed count
- Pending count
- Overdue count
- Rework count
- Estimate accuracy

کلیک -> User Task Report Detail

## 20.5 User Task Report Detail

### Summary

- روزهای کاری
- میانگین utilization
- total planned
- total actual
- task completion
- overdue
- rework

### Daily Rows

برای هر روز:

- ظرفیت
- planned
- actual
- utilization
- Task count
- status

Expand day -> Taskهای همان روز با:

- title
- priority
- planned segment
- actual
- result
- reviewer

## 20.6 Estimate Accuracy

فرمول پایه:

`accuracy_variance = (actual_minutes - estimated_minutes) / estimated_minutes`

گزارش:

- کمتر از estimate
- نزدیک estimate، مثلاً ±15%
- بیشتر از estimate

این KPI برای برنامه‌ریزی استفاده شود، نه قضاوت کور عملکرد فرد؛ UI wording باید خنثی باشد.

## 20.7 Under Planned Detail

وقتی مدیر روی «کمتر از 80%» می‌زند، نشان داده شود:

- چه کسانی
- چند درصد
- دلیل احتمالی از داده‌ها:
  - Task کافی تخصیص داده نشده
  - مرخصی / ساعت کاری کمتر
  - Pending acceptance
  - Blocked tasks
  - No estimate

سیستم نباید علت روانی/عملکردی حدس بزند.

---

# 21) ارتباط با ماژول‌های فعلی کارنومند

## Users & Structure

- Assignee، Manager، Department، Position از داده واقعی Users/Structure
- تغییر مدیر مستقیم باید permission visibility آینده را تغییر دهد
- History گذشته نباید از بین برود

## Attendance

اگر Attendance فعال است:

- ساعات کاری/حضور می‌تواند در گزارش Actual Presence کنار Task Time نمایش داده شود
- Task Timer به‌تنهایی جای Attendance نیست
- عدم حضور نباید خودکار به معنای عدم کار فرض شود مگر Business Rule مشخص

## Requests

قابلیت پیشنهادی فاز بعد:

- تبدیل Request approved به Task
- source reference حفظ شود

## Approvals

از Pattern تأیید/رد و Reason موجود reuse شود.

## Cloud / Attachments

Task Attachment از همان فایل سرویس استفاده کند.

## Reports

Export Pattern و permissionها با Reports فعلی یکسان باشد.

## Support

کاملاً جدا از Tasking domain باقی بماند.

---

# 22) تاریخ شمسی، زمان و Timezone

الزامی:

- Backend Timestampها UTC
- Organization timezone منبع نمایش
- UI Persian/Jalali مطابق استاندارد فعلی پروژه
- Scheduler باید بر مبنای روز محلی Organization کار کند
- DST اگر timezone آن را دارد، از timezone library معتبر استفاده شود
- «امروز» از زمان Local مجموعه محاسبه شود، نه Browser time خام

نمایش تاریخ باید Hybrid باشد:

- Friendly relative text در list
- Full Jalali date/time در detail

---

# 23) Empty / Loading / Error States

## Empty Today

> «برای امروز هنوز تسکی برنامه‌ریزی نشده است.»

CTA در صورت Permission:
- «افزودن تسک»

## No Assignment

> «ارجاع جدیدی نیازمند پاسخ شما نیست.»

## Loading

Skeleton مطابق Component موجود.

## Error

- Retry
- خطای انسانی و قابل فهم
- Technical details فقط log شوند

## Offline / network interruption

Timer نباید صرفاً با setInterval مرورگر منبع حقیقت باشد. Start timestamp روی Server ثبت شود و UI elapsed را از زمان سرور محاسبه کند. در reconnect باید state بازسازی شود.

---

# 24) Concurrency و جلوگیری از Bug

این بخش اجباری است.

## Race Conditions مهم

- دو بار Start سریع
- Start همزمان از دو Tab
- مدیر Task را Reassign کند در حالی که کارمند Timer فعال دارد
- Review همزمان توسط دو Reviewer
- Estimate change همزمان با Scheduler
- User deactivated while task active

راهکار:

- Transaction server-side
- row locking یا optimistic version
- idempotency برای action endpoints حساس
- unique constraint برای active timer per user
- deterministic Scheduler

Client state نباید منبع حقیقت Business State باشد.

---

# 25) API Design پیشنهادی

Endpointها را با REST/architecture پروژه تطبیق دهید.

## Task

- `GET /tasking/tasks`
- `POST /tasking/tasks`
- `GET /tasking/tasks/:id`
- `PATCH /tasking/tasks/:id`
- `POST /tasking/tasks/:id/cancel`

## Assignment

- `GET /tasking/assignments/pending`
- `POST /tasking/tasks/:id/accept`
- `POST /tasking/tasks/:id/reject`
- `POST /tasking/tasks/:id/reassign`

## Timer

- `POST /tasking/tasks/:id/start`
- `POST /tasking/tasks/:id/pause`
- `POST /tasking/tasks/:id/resume`
- `GET /tasking/timer/active`
- `POST /tasking/time-entries/manual`
- `PATCH /tasking/time-entries/:id`

## Completion/Review

- `POST /tasking/tasks/:id/submit-review`
- `POST /tasking/tasks/:id/approve`
- `POST /tasking/tasks/:id/request-changes`

## Chat

- `GET /tasking/tasks/:id/comments`
- `POST /tasking/tasks/:id/comments`
- `PATCH /tasking/comments/:id`
- `DELETE /tasking/comments/:id`

## Scheduling

- `GET /tasking/schedule?date=...`
- `POST /tasking/schedule/recalculate`
- `PATCH /tasking/allocations/:id`

## Reports

- `GET /reports/tasking/summary`
- `GET /reports/tasking/users`
- `GET /reports/tasking/users/:id`
- `GET /reports/tasking/tasks`
- `GET /reports/tasking/export.csv`

## Settings

- `GET /organizations/:id/tasking-settings`
- `PATCH /organizations/:id/tasking-settings`

تمام Endpointها باید Organization scoping قطعی داشته باشند.

---

# 26) Response DTO حداقلی برای Task List

برای جلوگیری از N+1 و Payload سنگین، List DTO از Detail جدا باشد.

نمونه مفهومی:

```json
{
  "id": 2841,
  "code": "TSK-1405-2841",
  "title": "بررسی پیش‌فاکتور تجهیزات",
  "priority": "high",
  "status": "in_progress",
  "assignee": {
    "id": 18,
    "name": "دامون رضایی",
    "avatar": null
  },
  "estimated_minutes": 120,
  "actual_minutes": 46,
  "remaining_minutes": 74,
  "today_planned_minutes": 60,
  "spillover_minutes": 60,
  "due_at": "2026-08-13T13:00:00Z",
  "has_unread_comments": true,
  "unread_count": 2,
  "active_timer": {
    "started_at": "2026-08-12T08:32:00Z"
  }
}
```

---

# 27) Performance Requirements

- Task list paginated یا virtualized در حجم بالا
- Queryها index مناسب روی:
  - organization_id
  - owner_id
  - status
  - due_at
  - work_date
  - reviewer_id / observer relations
- N+1 ممنوع
- Reportهای سنگین aggregation backend
- Scheduler برای کل Organization در هر request اجرا نشود؛ scope محدود به users/tasks impacted
- Background job برای recalculationهای گسترده، در صورتی که queue موجود است
- cache فقط جایی که consistency حفظ می‌شود

هدف UX:

- initial Tasking page under normal load سریع و بدون blocking report queries
- action feedback optimistic فقط اگر rollback امن است

---

# 28) Security Requirements

- Organization isolation در تمام Queryها
- Object-level authorization
- هیچ Task ID خام نباید دسترسی cross-org بدهد
- Attachment download signed/protected طبق سیستم فعلی
- Rich text sanitize
- Mention فقط کاربران مجاز سازمان
- Audit برای تغییرات حساس
- Permission check در Backend، نه فقط UI
- export گزارش permission جدا داشته باشد
- confidential tasks scope محدودتر داشته باشند اگر این قابلیت فعال شد

---

# 29) Accessibility و UX Quality

- Keyboard navigation
- Focus trap صحیح در Modal/Drawer
- Label برای form fields
- Error inline
- Color تنها نشانه Priority/Status نباشد؛ متن/آیکون هم باشد
- Contrast مطابق design system
- Screen-reader label برای Timer buttons
- RTL کامل
- اعداد و زمان‌ها خوانا و یکنواخت

---

# 30) Design System Rules

Agent باید قبل از ساخت UI، Componentهای موجود پروژه را inventory کند و reuse کند:

- Button
- IconButton
- Input
- Select
- UserPicker
- DatePicker
- TimePicker
- Modal
- Drawer
- Tabs
- Badge
- Avatar
- Tooltip
- Dropdown Menu
- Table/List
- Progress
- Toast
- Skeleton
- EmptyState

اگر Component موجود نیست، Component جدید generic بسازد، نه page-specific duplicate.

### Priority Dot

کنار هر Task یک دایره کوچک Semantic باشد و همراه Label یا Tooltip:

- بحرانی
- بالا
- متوسط
- عادی
- پایین

فقط به رنگ اتکا نشود.

### UI Style

- مدرن، خلوت، سازمانی و حرفه‌ای
- Data density کنترل‌شده
- whitespace کافی
- Borderهای ظریف
- Shadow کم
- انیمیشن‌های کوتاه و کاربردی
- بدون gradient و decoration غیرضروری مگر design system فعلی دارد

---

# 31) Microcopy پیشنهادی فارسی

## CTAها

- تسک جدید
- شروع
- توقف
- ادامه
- پایان و ارسال برای بررسی
- پذیرفتن ارجاع
- رد ارجاع
- تأیید و بستن
- درخواست اصلاح
- تغییر زمان تخمینی
- ارجاع مجدد
- افزودن ناظر

## Status Labels

- نیازمند پذیرش
- برنامه‌ریزی‌شده
- پیش‌رو
- در حال انجام
- متوقف‌شده
- مسدود
- در انتظار بررسی
- نیازمند اصلاح
- تکمیل‌شده
- لغوشده
- عقب‌افتاده

## Capacity

- کمتر از ظرفیت هدف
- در محدوده هدف
- بار کاری بالا
- بیش از ظرفیت

---

# 32) Edge Cases اجباری

1. Task صفر دقیقه ایجاد نشود.
2. estimate بسیار بزرگ مثلاً 80 ساعت بتواند چند روز تقسیم شود.
3. Task با Deadline قبل از start date خطا دهد.
4. Assignee inactive خطا دهد.
5. Reviewer و Assignee یک نفر است؛ policy تعیین کند مجاز است یا نه. پیش‌فرض بهتر: Review by self مجاز نباشد اگر Review required.
6. کارمند Assignment را رد می‌کند؛ Task بدون owner گم نشود و به creator/manager برگردد.
7. روز آینده تعطیل است؛ Spillover به اولین روز کاری بعد برود.
8. فرد فردا مرخص است؛ Spillover skip شود.
9. Deadline امروز ولی ظرفیت پر است؛ High Load warning و manager override.
10. Task در حال اجرا deadline تغییر می‌کند؛ timer قطع نشود.
11. Task در حال اجرا priority پایین می‌شود؛ timer قطع نشود.
12. User browser بسته می‌شود؛ Timer سرور ادامه دارد تا Pause/Policy action.
13. Double click روی Start، یک TimeEntry بسازد.
14. Complete با active timer: ابتدا time entry بسته شود و سپس submit review.
15. Review reject چندبار؛ history iteration حفظ شود.
16. Task completed در گزارش بعد از تغییر مدیر همچنان history صحیح داشته باشد.
17. حذف/غیرفعال شدن user، Taskها reassign workflow داشته باشند.
18. حذف Department باعث orphan task نشود؛ historical label snapshot یا nullable-safe.
19. Comment edit history در صورت policy لازم.
20. timezone تغییر Organization، timestamps خام تغییر نکنند؛ فقط display/schedule آینده recompute شود.

---

# 33) تست‌های Acceptance حیاتی

## AC-01 ظرفیت پایه

Given ساعت کاری 8 ساعت و Target=80%  
When هیچ مرخصی وجود ندارد  
Then target task capacity = 384 دقیقه.

## AC-02 تقسیم Task

Given امروز 336 دقیقه از 384 دقیقه پر است  
And Task جدید 96 دقیقه است  
When Task accepted می‌شود  
Then 48 دقیقه امروز و 48 دقیقه روز کاری بعد Allocation شود.

## AC-03 اولویت بالا

Given 10 Task عادی schedule شده‌اند  
When Task High جدید accepted می‌شود  
Then قبل از اولین Task شروع‌نشده عادی قرار گیرد.

## AC-04 عدم جابه‌جایی Task فعال

Given Task A در حال اجراست  
When Task Critical جدید اضافه می‌شود  
Then A قطع یا Pause نشود و Critical اولین Task بعدی شود.

## AC-05 Assignment

Given acceptance required  
When مدیر Task را به کارمند ارجاع می‌دهد  
Then تا Accept در برنامه قطعی کارمند وارد نشود و Badge ارجاع +1 شود.

## AC-06 Timer uniqueness

Given User روی Task A Timer فعال دارد  
When Start Task B را می‌زند  
Then سیستم باید Stop A + Start B confirmation بگیرد یا action را reject کند؛ دو Timer فعال ایجاد نشود.

## AC-07 Review rejection

Given Task submit review شده  
When Reviewer «درخواست اصلاح» با Reason می‌زند  
Then همان Task با iteration جدید به برنامه کارمند برگردد و تمام History/Chat حفظ شود.

## AC-08 Report threshold

Given سه کارمند utilization 65%, 82%, 107% دارند  
Then report آنها را به‌ترتیب Under Target، Target Met، Overloaded دسته‌بندی کند.

## AC-09 Organization isolation

User از Organization A نباید با Task ID متعلق به Organization B هیچ اطلاعاتی دریافت کند؛ response 404/403 طبق convention پروژه.

## AC-10 Mobile

در عرض 320px هیچ horizontal overflow عمومی در Task page وجود نداشته باشد؛ همه actionهای اصلی قابل لمس باشند.

---

# 34) سناریوی کامل واقعی

1. مدیر در Settings ساعت کاری را شنبه تا چهارشنبه 08:00-16:00 و Target=80% تعریف می‌کند.
2. کارمند دامون امروز 5 ساعت Task دارد.
3. مدیر Task «تهیه گزارش قراردادها» با estimate=2h و priority=High برای دامون می‌سازد.
4. سیستم قبل از ثبت Preview می‌دهد که 1h24m تا Target امروز آزاد است و 36m به فردا منتقل می‌شود.
5. Task به ارجاع‌های دامون می‌رود.
6. دامون Accept می‌کند.
7. Scheduler آن را بالاتر از Taskهای عادی قرار می‌دهد، بدون قطع Task در حال اجرا.
8. دامون Start می‌زند؛ Timer آغاز می‌شود.
9. در میانه کار Pause می‌کند؛ 43m ثبت می‌شود.
10. در Chat، ناظر را mention می‌کند و فایل می‌فرستد.
11. دوباره Resume می‌کند.
12. estimate را با دلیل از 2h به 2h30m افزایش می‌دهد؛ Scheduler remainder را recompute می‌کند.
13. Task را تمام و برای Review ارسال می‌کند.
14. مدیر Review می‌کند و Reason اصلاح می‌دهد.
15. Task با iteration 2 و همان Context به صف کار دامون برمی‌گردد.
16. دامون اصلاح می‌کند و مجدد Submit می‌کند.
17. مدیر Approve می‌کند.
18. Task Closed می‌شود.
19. گزارش‌ها planned، actual، rework و utilization را ثبت می‌کنند.

---

# 35) قابلیت‌های تکمیلی پیشنهادی که ارزش واقعی دارند

این موارد در معماری از ابتدا در نظر گرفته شوند، حتی اگر برخی در Phase 2 فعال شوند.

## 35.1 Checklist داخل Task

برای Taskهای چندمرحله‌ای:

- item
- done
- done_by
- done_at

## 35.2 Recurring Tasks

مثلاً:
- هر روز 9 صبح
- هر شنبه
- آخر هر ماه

از template Task instance ساخته شود.

## 35.3 Blocked Reason

کاربر بتواند Task را Blocked کند با:

- منتظر پاسخ شخص
- منتظر فایل
- منتظر تصمیم
- وابسته به Task دیگر
- دلیل دیگر

این داده در گزارش Manager بسیار مفید است.

## 35.4 Follow / Watch

کاربر مجاز بتواند Task را Follow کند و Notification مهم بگیرد، بدون Observer رسمی شدن.

## 35.5 Saved Filters

مدیر بتواند Filterهایی مثل «تسک‌های عقب‌افتاده تیم فروش» ذخیره کند.

## 35.6 Bulk Actions برای مدیر

در صفحات مدیریتی:

- تغییر Priority
- Reassign
- Add observer
- Shift due date

با Permission و confirmation.

---

# 36) چیزهایی که نباید در نسخه اول باعث شلوغی شوند

- Kanban پیچیده به‌عنوان View اصلی
- Gantt سنگین
- Gamification غیرسازمانی
- امتیازدهی خام کارمند صرفاً بر مبنای Timer
- AI تصمیم‌گیر خودکار بدون داده کافی
- drag & drop آزاد که قوانین Scheduler را دور بزند

اگر بعداً Kanban اضافه شد، باید View روی همان Task Model باشد، نه سیستم جدا.

---

# 37) Implementation Order پیشنهادی

## Phase 1 — Foundation

- Data model
- Permissions
- Settings
- Task CRUD
- Assignment
- Observer/manager visibility
- Basic list UI

## Phase 2 — Scheduler

- Capacity calculation
- Daily allocations
- Split across days
- Priority ordering
- date navigation

## Phase 3 — Execution

- Timer
- Pause/resume
- estimate change
- completion

## Phase 4 — Review & Collaboration

- Review approve/changes requested
- Chat
- Mention
- Attachments
- Activity timeline

## Phase 5 — Reports

- utilization report
- drilldown
- export
- estimate accuracy

## Phase 6 — Hardening

- edge cases
- concurrency
- mobile QA
- performance
- security
- accessibility

---

# 38) Definition of Done

این Feature فقط وقتی «تمام» محسوب می‌شود که:

- تمام state transitionها backend validated باشند.
- Task creation و assignment روی داده واقعی Organization/User انجام شود.
- ظرفیت روزانه بر اساس Settings واقعی محاسبه شود.
- Split Task بین روزها واقعاً کار کند.
- Priority reorder deterministic باشد.
- Timer server-backed باشد.
- Review rejection همان Task را با History کامل برگرداند.
- Chat و Mention object-level permission داشته باشند.
- Report کمتر از Target و بیشتر از Capacity drilldown کامل داشته باشد.
- Desktop/Tablet/Mobile QA شده باشد.
- RTL و Jalali صحیح باشد.
- هیچ horizontal overflow جدی در Mobile وجود نداشته باشد.
- Loading/Empty/Error states کامل باشند.
- Race conditionهای اصلی تست شده باشند.
- تست‌های unit/integration برای Scheduler نوشته شده باشند.
- APIها organization-scoped باشند.
- هیچ رنگ/Component ناسازگار با Design System فعلی وارد نشده باشد.
- N+1های اصلی برطرف شده باشند.
- Activity/Audit برای عملیات حساس ثبت شود.

---

# 39) Checklist نهایی برای Agent قبل از Merge

- [ ] بررسی کامل Componentهای موجود قبل از ساخت Component جدید
- [ ] reuse User/Organization/Role/Department data
- [ ] ایجاد migrations با rollback امن
- [ ] indexهای دیتابیس
- [ ] Permission backend
- [ ] Task state machine tests
- [ ] Capacity calculation tests
- [ ] Split allocation tests
- [ ] Priority ordering tests
- [ ] Deadline/holiday/leave tests
- [ ] Assignment accept/reject tests
- [ ] Timer concurrency tests
- [ ] Review iteration tests
- [ ] Comment/Mention authorization tests
- [ ] Reports aggregation tests
- [ ] RTL QA
- [ ] Jalali/date QA
- [ ] Mobile 320/375/430px QA
- [ ] Tablet QA
- [ ] Desktop QA
- [ ] slow network/loading/error QA
- [ ] cross-organization security tests
- [ ] accessibility basics
- [ ] performance profiling برای list و report
- [ ] هیچ TODO بحرانی باقی نمانده باشد

---

# 40) خروجی نهایی مورد انتظار از توسعه

در پایان، کارنومند باید یک ماژول Tasking داشته باشد که تجربه آن چنین باشد:

کارمند وارد پنل می‌شود و بدون سردرگمی می‌بیند امروز چه کارهایی، با چه اولویت و چه میزان زمان باید انجام دهد. تسک‌های جدید بر اساس ظرفیت واقعی روز و روزهای آینده قرار می‌گیرند. اگر Task سنگین‌تر از ظرفیت باقی‌مانده باشد، به‌صورت منطقی بین روزها تقسیم می‌شود. Taskهای مهم جای درست خود را پیدا می‌کنند. ارجاع‌های دیگران ابتدا قابل پذیرش هستند. کاربر اجرای واقعی را با Timer ثبت می‌کند. مدیر بدون ورود به پیام‌رسان یا فایل پراکنده می‌تواند وضعیت، زمان، تأخیر، بار کاری و خروجی Task را ببیند. پایان Task نیازمند Review می‌تواند تأیید یا برای اصلاح بازگردانده شود و هیچ سابقه‌ای از بین نمی‌رود. مکالمه و فایل در Context همان Task باقی می‌ماند. گزارش مدیریتی نیز نشان می‌دهد چه کسانی کمتر از ظرفیت هدف، در محدوده مطلوب، پرکار یا بیش از ظرفیت برنامه‌ریزی شده‌اند و با یک کلیک جزئیات دقیق روز و Taskهایشان در دسترس است.

این ماژول باید «مدیریت کار واقعی داخل شرکت» را حل کند، نه فقط نمایش یک لیست Task.
