تو یک Senior UI/UX Designer و Frontend Architect حرفه‌ای هستی.

من یک سامانه سازمانی فارسی و RTL دارم با موضوع:

«سامانه مدیریت درخواست‌ها، هزینه‌ها و تایید اسناد سازمانی»

تکنولوژی پروژه:

Frontend:
Next.js + TypeScript + Tailwind CSS + Shadcn UI

هدف:
کل رابط کاربری سایت باید با یک سیستم دیزاین کاملاً حرفه‌ای، مدرن، لوکس، گرم، سازمانی و فارسی‌محور بازطراحی شود.

نکته بسیار مهم:
الان فقط صفحه اول یا بخشی از سایت تغییر کرده است.
تو باید کل سایت را یکپارچه بازطراحی کنی، نه فقط صفحه اول.

تمام صفحات، همه ماژول‌ها، همه کارت‌ها، جدول‌ها، فرم‌ها، مودال‌ها، منوها، داشبوردها، فیلترها، دکمه‌ها، وضعیت‌ها، نمودارها، صفحه ورود، صفحه درخواست‌ها، صفحه هزینه‌ها، صفحه اسناد، صفحه گزارشات و صفحه تنظیمات باید دقیقاً با همین سیستم دیزاین هماهنگ شوند.

---

## 1. پالت رنگی اصلی سایت

کل رنگ سایت باید بر اساس این پالت باشد:

Primary Navy:
#2E4374

Secondary Indigo:
#4B527E

Muted Lavender:
#7C81AD

Warm Sand:
#E5C3A6

معادل RGB:

rgb(46, 67, 116)
rgb(75, 82, 126)
rgb(124, 129, 173)
rgb(229, 195, 166)

از این به بعد هیچ رنگ آبی SaaS عمومی، خاکستری سرد، بنفش تند، سبز نئونی، قرمز خام یا رنگ‌های بی‌ربط نباید در UI استفاده شود.

---

## 2. هویت بصری مورد انتظار

استایل نهایی باید این حس را منتقل کند:

* سازمانی
* قابل اعتماد
* مدرن
* لوکس
* گرم
* آرام
* رسمی اما انسانی
* فارسی‌محور
* مدیریتی
* premium enterprise

مرجع طراحی:

Warm Persian Enterprise Interface

نه:

* SaaS آبی جنریک
* داشبورد سرد و بی‌روح
* طراحی بیش از حد استارتاپی
* تم Material خام
* UI شلوغ و رنگارنگ
* فرم‌های تیز و خشک

---

## 3. تعریف Design Tokens

ابتدا کل رنگ‌ها را به صورت توکن مرکزی تعریف کن تا هیچ رنگی hardcode نشود.

پیشنهاد توکن‌ها:

```css
:root {
  --color-primary: #2E4374;
  --color-secondary: #4B527E;
  --color-muted: #7C81AD;
  --color-accent: #E5C3A6;

  --color-background: #F7F1EB;
  --color-surface: #FFFFFF;
  --color-surface-soft: #FBF5EF;
  --color-surface-warm: #F4ECE4;

  --color-border: rgba(46, 67, 116, 0.12);
  --color-border-strong: rgba(46, 67, 116, 0.18);

  --color-text: #1F2A44;
  --color-text-secondary: #4B527E;
  --color-text-muted: #7C81AD;

  --color-success-bg: #EEF1EA;
  --color-success-text: #3F5F4A;

  --color-warning-bg: #F5E4D4;
  --color-warning-text: #2E4374;

  --color-danger-bg: #F4DFDB;
  --color-danger-text: #8F3B3B;
}
```

در Tailwind نیز همین رنگ‌ها را به theme extend منتقل کن.

تمام رنگ‌های قبلی پروژه باید حذف یا جایگزین شوند.

---

## 4. قوانین کلی UI

کل سایت باید card-driven باشد.

یعنی ساختار صفحات باید بر پایه کارت‌ها، پنل‌ها و سکشن‌های نرم باشد.

قوانین کلی:

* پس‌زمینه اصلی صفحات: کرم روشن و گرم
* کارت‌ها: سفید یا warm soft
* مرزها: بسیار نرم و کم‌کنتراست
* گوشه‌ها: گرد و مدرن
* سایه‌ها: بسیار لطیف
* فاصله‌گذاری: باز، مرتب و سازمانی
* فرم‌ها: کاملاً RTL و فارسی‌محور
* ناوبری: pill-based
* جدول‌ها: تمیز، گرم، قابل خواندن
* مودال‌ها: بزرگ، نرم، premium
* موبایل: touch-friendly و تک‌ستونه

---

## 5. Typography

فونت اصلی پروژه باید Vazirmatn باشد.

هیچ فونت دیگری مثل IRANSansX، Yekan Bakh یا فونت‌های نامرتبط استفاده نشود مگر اینکه قبلاً در پروژه نصب شده باشد.

قواعد تایپوگرافی:

* تیتر صفحه: 28px تا 32px، ضخیم، سرمه‌ای
* تیتر سکشن: 22px تا 24px
* عنوان کارت: 18px تا 20px
* متن اصلی: 15px تا 16px
* توضیحات و meta: 12px تا 14px
* اعداد آماری: بزرگ، bold و با رنگ Primary
* line-height باز و خوانا
* همه متن‌ها RTL و راست‌چین باشند

---

## 6. Radius System

تمام کامپوننت‌ها باید گوشه گرد داشته باشند.

مقادیر پیشنهادی:

```css
--radius-xs: 8px;
--radius-sm: 10px;
--radius-md: 16px;
--radius-lg: 22px;
--radius-xl: 30px;
--radius-full: 9999px;
```

قواعد:

* input ها: 16px
* button ها: 16px یا pill
* card ها: 22px
* modal ها: 30px
* chip ها: کاملاً pill

از گوشه‌های تیز استفاده نکن.

---

## 7. Button System

### Primary Button

استایل:

* background: #2E4374
* color: white
* radius: 16px یا 9999px
* padding مناسب
* shadow نرم
* hover: کمی روشن‌تر یا gradient بین #2E4374 و #4B527E
* active: کمی scale یا کاهش shadow

نمونه حس:
دکمه باید رسمی، قوی و premium باشد.

### Secondary Button

استایل:

* background: white یا #FBF5EF
* color: #2E4374
* border: rgba(46, 67, 116, 0.14)
* hover: warm sand tint

### Ghost Button

استایل:

* بدون پس‌زمینه سنگین
* رنگ متن: #4B527E
* hover: #F4ECE4
* مناسب عملیات‌های کم‌اهمیت

### Danger Button

استایل:

* background: #F4DFDB
* color: #8F3B3B
* border ملایم
* بدون قرمز تند

---

## 8. Cards

همه کارت‌ها باید با این زبان طراحی بازسازی شوند.

Card Base:

```css
background: #FFFFFF;
border: 1px solid rgba(46, 67, 116, 0.10);
border-radius: 22px;
box-shadow: 0 18px 45px rgba(46, 67, 116, 0.06);
```

قوانین کارت:

* padding باز
* title واضح
* subtitle کم‌رنگ
* icon داخل container گرد
* hover نرم
* بدون border ضخیم
* بدون shadow تیز
* بدون رنگ‌های سرد

کارت‌های آماری داشبورد باید شامل:

* آیکن گرد با tint رنگی
* عدد بزرگ
* عنوان کوتاه
* توضیح یا روند تغییر
* رنگ اصلی بر اساس پالت

---

## 9. Dashboard

داشبورد باید بسیار حرفه‌ای طراحی شود.

المان‌ها:

* Header خوش‌ساخت با عنوان، توضیح و action اصلی
* کارت‌های آماری برای:

  * درخواست‌های فعال
  * درخواست‌های تایید شده
  * درخواست‌های رد شده
  * اسناد در انتظار بررسی
  * هزینه ماه
  * هزینه سال
* نمودار هزینه‌ها
* نمودار وضعیت درخواست‌ها
* لیست آخرین درخواست‌ها
* لیست آخرین اسناد
* بخش اعلان‌های اخیر

طراحی داشبورد باید شبیه پنل مدیریتی لوکس باشد، نه صفحه خام.

چیدمان دسکتاپ:

* Grid چندستونه
* کارت‌های آماری در بالا
* نمودارها در وسط
* فعالیت‌های اخیر در پایین یا کنار

چیدمان موبایل:

* تک‌ستونه
* کارت‌ها پشت سر هم
* جدول‌ها تبدیل به list card شوند

---

## 10. Navigation

ناوبری دسکتاپ باید top navigation باشد، نه sidebar کلاسیک.

قوانین:

* nav container سفید یا glass warm
* آیتم‌ها pill-based
* active item:

  * background: #2E4374
  * color: white
* inactive item:

  * color: #7C81AD
* hover:

  * background: #F4ECE4
  * color: #2E4374

موبایل:

* floating segmented navigation
* پایین صفحه یا بالای محتوا
* touch-friendly
* pill item
* active state واضح با primary navy

---

## 11. Forms

تمام فرم‌ها باید بازطراحی شوند.

قوانین:

* label بیرون input باشد
* input ها RTL باشند
* border نرم
* focus با رنگ #2E4374
* placeholder با #7C81AD
* error state با dusty red
* field group ها داخل کارت یا soft panel باشند
* فرم‌ها خلوت، خوانا و لوکس باشند

Input Base:

```css
background: #FFFFFF;
border: 1px solid rgba(46, 67, 116, 0.12);
border-radius: 16px;
color: #1F2A44;
```

Focus:

```css
border-color: #2E4374;
box-shadow: 0 0 0 4px rgba(46, 67, 116, 0.10);
```

---

## 12. Tables

جدول‌ها باید برای زبان فارسی و داده‌های سازمانی خوانا باشند.

قوانین جدول:

* header با background گرم:
  #F4ECE4 یا #FBF5EF
* متن header سرمه‌ای
* ردیف‌ها سفید
* divider بسیار نرم
* hover row با tint گرم
* action buttons کم‌نویز
* status badge ها pill باشند

در موبایل:

جدول‌های سنگین باید به card list تبدیل شوند.

هر row موبایل باید تبدیل شود به یک کارت با:

* عنوان
* وضعیت
* متادیتا
* تاریخ
* عملیات

---

## 13. Status Badges

همه وضعیت‌ها باید هماهنگ با پالت باشند.

Approved / تایید شده:

```css
background: #EEF1EA;
color: #3F5F4A;
```

Pending / در انتظار بررسی:

```css
background: #F4ECE4;
color: #4B527E;
```

Rejected / رد شده:

```css
background: #F4DFDB;
color: #8F3B3B;
```

Draft / پیش‌نویس:

```css
background: #FBF5EF;
color: #7C81AD;
```

Urgent / فوری:

```css
background: #F5E4D4;
color: #2E4374;
```

همه badge ها باید rounded-full باشند.

---

## 14. Modals & Dialogs

مودال‌ها باید حس premium داشته باشند.

قواعد:

* radius: 30px
* background: #FFFFFF یا #FBF5EF
* overlay: rgba(46, 67, 116, 0.25)
* backdrop blur
* padding باز
* header واضح
* footer با action buttons منظم
* در موبایل: bottom-sheet behavior

از مودال‌های مربعی و خشک استفاده نکن.

---

## 15. Page Layout

تمام صفحات باید ساختار حرفه‌ای داشته باشند:

هر صفحه شامل:

1. Page Header
2. Summary Cards
3. Filter Panel
4. Main Content Card
5. Empty State / Loading State / Error State

Page Header:

* عنوان صفحه
* توضیح کوتاه
* دکمه اصلی سمت مخالف
* آیکن یا badge مرتبط

Filter Panel:

* soft surface
* rounded
* فیلدهای مرتب
* دکمه جستجو یا اعمال فیلتر
* دکمه پاک کردن فیلتر

---

## 16. Modules To Redesign

کل این صفحات و ماژول‌ها باید با سیستم دیزاین جدید هماهنگ شوند:

### Login Page

* پس‌زمینه warm gradient
* کارت ورود وسط صفحه
* فرم RTL
* دکمه primary
* لینک فراموشی رمز
* حالت ورود با ایمیل و موبایل
* حس امن و سازمانی

### Dashboard

* کارت‌های آماری
* نمودارها
* لیست فعالیت‌ها
* اعلان‌ها
* گزارش خلاصه

### Requests Module

صفحات:

* لیست درخواست‌ها
* ثبت درخواست جدید
* جزئیات درخواست
* گردش کار درخواست
* تایید / رد درخواست

باید شامل:

* جدول حرفه‌ای
* فیلترها
* کارت جزئیات
* timeline گردش کار
* status badge
* attachment section

### Expenses Module

صفحات:

* داشبورد هزینه‌ها
* ثبت هزینه
* لیست هزینه‌ها
* جزئیات هزینه

باید شامل:

* کارت هزینه امروز، هفته، ماه، سال
* نمودار هزینه
* دسته‌بندی هزینه
* فاکتور پیوست
* وضعیت بررسی

### Documents Module

صفحات:

* لیست اسناد
* بارگذاری سند
* نمایش سند
* تایید سند
* رد سند

باید شامل:

* preview فایل
* کارت اطلاعات سند
* action buttons
* approve / reject panel
* توضیحات مدیر

### Reports Module

صفحات:

* گزارش درخواست‌ها
* گزارش هزینه‌ها
* گزارش اسناد
* خروجی PDF / Excel / CSV

باید شامل:

* filter advanced
* report cards
* chart area
* export buttons
* table clean

### Settings Module

صفحات:

* مدیریت کاربران
* مدیریت نقش‌ها
* تنظیمات امنیتی
* لاگ فعالیت‌ها

باید شامل:

* user cards
* role badges
* permission matrix
* security toggles
* audit log table

---

## 17. Empty / Loading / Error States

هیچ صفحه‌ای نباید خام یا ناقص دیده شود.

برای هر بخش باید state طراحی شود:

Empty State:

* آیکن نرم
* متن دوستانه اما رسمی
* action button

Loading State:

* skeleton warm
* بدون spinner خام

Error State:

* کارت خطا با رنگ dusty red
* پیام واضح
* دکمه تلاش مجدد

---

## 18. Icons

آیکن‌ها باید:

* خطی
* نرم
* هماهنگ با پالت
* داخل container گرد استفاده شوند
* بیش از حد رنگارنگ نباشند

رنگ آیکن اصلی:

#2E4374

آیکن ثانویه:

#7C81AD

background آیکن:

#F4ECE4 یا rgba(229, 195, 166, 0.35)

---

## 19. Shadows

سایه‌ها باید بسیار نرم و premium باشند.

نمونه:

```css
box-shadow: 0 18px 45px rgba(46, 67, 116, 0.06);
box-shadow: 0 12px 30px rgba(46, 67, 116, 0.08);
box-shadow: 0 8px 20px rgba(46, 67, 116, 0.05);
```

از shadow های تیز، مشکی و سنگین استفاده نکن.

---

## 20. Responsive Design

کل سایت باید برای این سایزها درست باشد:

* Desktop
* Laptop
* Tablet
* Mobile

قواعد:

Desktop:

* grid چندستونه
* کارت‌های آماری کنار هم
* جدول کامل

Tablet:

* grid دو ستونه
* فیلترها جمع‌وجور
* spacing کمتر اما خوانا

Mobile:

* تک‌ستونه
* کارت‌های بزرگ‌تر
* جدول تبدیل به کارت
* دکمه‌ها full width در فرم‌ها
* nav شناور و لمسی

---

## 21. Dark Mode

اگر Dark Mode وجود دارد، باید با همین پالت طراحی شود.

Dark Mode نباید مشکی خام باشد.

پیشنهاد:

```css
--dark-bg: #171B2E;
--dark-surface: #202642;
--dark-surface-soft: #283050;
--dark-primary: #E5C3A6;
--dark-text: #F7F1EB;
--dark-muted: #B8BCD8;
--dark-border: rgba(229, 195, 166, 0.14);
```

Dark Mode باید حس navy warm premium داشته باشد.

---

## 22. Professional UI Improvements

این موارد را به طراحی اضافه کن:

* Page transition نرم
* Hover state برای کارت‌ها
* Micro-interaction برای دکمه‌ها
* Breadcrumb در صفحات داخلی
* Timeline برای گردش کار
* Activity log برای عملیات‌ها
* Notification center
* Search bar حرفه‌ای
* Advanced filters
* Export buttons
* Upload area با drag & drop
* File preview card
* Confirmation modal برای حذف، رد و تایید
* Toast notification هماهنگ با پالت

---

## 23. ممنوعیت‌ها

این موارد نباید اتفاق بیفتد:

* فقط صفحه اول تغییر کند
* رنگ‌ها فقط در hero تغییر کنند
* کامپوننت‌ها هنوز رنگ قدیمی داشته باشند
* جدول‌ها طراحی خام داشته باشند
* فرم‌ها با border خاکستری سرد باشند
* sidebar کلاسیک اضافه شود
* فونت فارسی تغییر کند
* radius ها حذف شوند
* دکمه‌ها رنگ آبی جنریک داشته باشند
* از Tailwind color های خام مثل blue-500، gray-200، red-500 استفاده شود
* رنگ‌ها به صورت hardcode در کامپوننت‌ها پخش شوند
* موبایل خراب شود
* RTL ناقص باشد

---

## 24. خروجی مورد انتظار

در پایان باید:

1. کل سیستم Theme مرکزی داشته باشد.
2. همه رنگ‌ها از Design Tokens خوانده شوند.
3. همه صفحات با پالت جدید هماهنگ باشند.
4. UI کاملاً RTL و فارسی‌محور باشد.
5. همه کارت‌ها، فرم‌ها، جدول‌ها، مودال‌ها و دکمه‌ها unified باشند.
6. صفحه اول، داشبورد، درخواست‌ها، هزینه‌ها، اسناد، گزارشات، تنظیمات و لاگین همگی بازطراحی شوند.
7. UI نهایی باید حس یک نرم‌افزار سازمانی premium و مدرن بدهد.

---

## 25. دستور اجرایی

ابتدا پروژه را کامل بررسی کن.

سپس:

1. فایل‌های theme، globals، tailwind config و shadcn variables را اصلاح کن.
2. تمام hardcoded colors را پیدا و جایگزین کن.
3. layout اصلی را با background و navigation جدید هماهنگ کن.
4. همه کامپوننت‌های پایه را بازطراحی کن:

   * Button
   * Input
   * Select
   * Textarea
   * Card
   * Badge
   * Table
   * Modal
   * Tabs
   * Dropdown
   * Toast
   * Upload
   * Date Picker
5. سپس تک‌تک صفحات را با همین کامپوننت‌ها بازسازی کن.
6. هیچ صفحه‌ای را نیمه‌کاره رها نکن.
7. خروجی باید production-ready، responsive و تمیز باشد.

نتیجه نهایی باید یک UI کاملاً یکپارچه، حرفه‌ای، لوکس، مدرن، گرم، فارسی و سازمانی باشد که تمام رنگ‌هایش بر اساس این پالت ساخته شده‌اند:

#2E4374
#4B527E
#7C81AD
#E5C3A6
