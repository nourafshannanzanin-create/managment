# ماژول ورود و خروج پرسنل

این پوشه نسخه قابل انتقال ماژول ورود و خروج است و هر دو صفحه را دارد:

- صفحه ادمین/مدیر: `frontend/src/views/manager/AttendanceView.vue`
- صفحه کارمند با لینک عمومی: `frontend/src/views/attendance/WorkerAttendancePunchView.vue`
- API و مدل‌ها: `backend/apps/workers/`
- محدودیت رایگان ۵ نیرو و خرید آپشن: `backend/apps/auth/feature_access.py`
- گزارش ورود و خروج: `backend/apps/reports/views.py`

## اتصال سریع

1. فایل‌های `frontend/src` را در پروژه Vue مقصد کپی کن.
2. routeهای داخل `frontend/router.attendance-snippet.js` را به router مقصد اضافه کن.
3. آیتم منو `attendanceNavigationItem` را برای نقش‌های `admin` و `manager` اضافه کن.
4. فایل‌های `backend/apps/workers` را به Django app مقصد اضافه کن و `apps.workers` را در `INSTALLED_APPS` بگذار.
5. snippet داخل `backend/urls.attendance-snippet.py` را به URL اصلی پروژه وصل کن.
6. migrationهای `backend/apps/workers/migrations` را اجرا کن.
7. اگر پروژه مقصد سیستم خرید آپشن دارد، feature key با مقدار `attendance` را نگه دار؛ اگر ندارد، `worker_has_attendance_access` در `feature_access.py` را ساده کن تا همیشه `True` برگرداند.

## وابستگی‌های فرانت

این ماژول به Vue 3، Vue Router، Pinia و Axios نیاز دارد. فایل `services/api.js` با مسیر پایه `/api` تنظیم شده و CSRF را برای Django می‌فرستد.

## وابستگی‌های بک‌اند

بک‌اند بر پایه Django REST Framework است و به مدل‌های کاربر و tenant پروژه اصلی وابسته است:

- `settings.AUTH_USER_MODEL`
- مدل tenant با نام `cw_auth.CarWash`
- فیلدهای کاربر: `role`, `tenant`, `phone`, `full_name`, `is_deleted`

اگر سایت مقصد tenant یا wallet ندارد، باید importهای `apps.auth.models.CarWashFeaturePurchase` و منطق خرید آپشن را با ساختار همان سایت تطبیق بدهی.
