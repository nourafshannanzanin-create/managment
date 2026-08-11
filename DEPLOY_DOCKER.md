# Docker Deploy For `carnomand.ir`

این پروژه برای سرور به صورت Docker آماده شده و این بخش‌ها را بالا می‌آورد:

- `db`: MySQL
- `backend`: Django + Gunicorn
- `frontend`: Vue build داخل Nginx (صفحه اول = لندینگ `/`)
- `gateway-nginx`: ورودی داخلی برای SPA، API و آپلودها

ورودی داخلی روی `127.0.0.1:18090` است تا با سایت‌های دیگر روی `80/443` تداخل نداشته باشد. دامنه `carnomand.ir` از nginx اصلی سرور به این gateway وصل می‌شود.

> مهم: ریشه دامنه (`/`) لندینگ است و نباید به `/login` ریدایرکت شود. ورود فقط از CTAهای لندینگ به `/login` می‌رود.

## 1. آماده‌سازی env

```bash
cd /mnt/newvolume/PRG/carnomand
cp -n .env.production.example .env.production
nano .env.production
```

حداقل این مقدارها را تنظیم کنید:

```env
MYSQL_ROOT_PASSWORD=strong-root-password
WORKFLOW_SECRET_KEY=very-long-random-secret
WORKFLOW_MYSQL_PASSWORD=strong-db-password
WORKFLOW_ALLOWED_HOSTS=carnomand.ir,www.carnomand.ir,127.0.0.1,localhost,backend,gateway-nginx
WORKFLOW_FRONTEND_ORIGINS=https://carnomand.ir,https://www.carnomand.ir,http://carnomand.ir,http://www.carnomand.ir
WORKFLOW_CSRF_TRUSTED_ORIGINS=https://carnomand.ir,https://www.carnomand.ir,http://carnomand.ir,http://www.carnomand.ir
WORKFLOW_AUTO_SEED_DB=false
WORKFLOW_NESHAN_SERVICE_KEY=service.679d0dde3d6d42a898f33ecc2a3f2fdd
WORKFLOW_NESHAN_REVERSE_URL=https://api.neshan.org/v5/reverse
VITE_API_BASE_URL=/api/v1
VITE_NESHAN_SERVICE_KEY=service.679d0dde3d6d42a898f33ecc2a3f2fdd
VITE_NESHAN_REVERSE_URL=https://api.neshan.org/v5/reverse
```

## 1.1 تنظیم پنل نشان (الزامی برای آدرس‌یابی)

در پنل توسعه‌دهندگان نشان، روی همین API Key:

1. سرویس **تبدیل نقطه به آدرس (Reverse Geocoding)** را فعال کنید.
2. در Whitelist دامنه این‌ها را بگذارید (بدون `https://`):
   - `carnomand.ir`
   - `www.carnomand.ir`
3. محدودیت IP را برای مرورگر خالی بگذارید یا فقط IP ثابت سرور را برای پروکسی بک‌اند اضافه کنید.
4. بعد از تغییر دامنه/کلید، حتماً فرانت را دوباره `--build` کنید تا `VITE_NESHAN_*` داخل باندل برود.

تست بعد از دیپلوی (از مرورگر روی دامنه، نه از IP سرور):

- تنظیمات → لوکیشن ورود و خروج → کلیک روی نقشه
- باید پیام «آدرس از سرویس نشان دریافت شد» بیاید

## 2. بالا آوردن Docker

```bash
cd /mnt/newvolume/PRG/carnomand
DOCKER_BUILDKIT=1 docker compose --env-file .env.production up -d --build
```

وضعیت:

```bash
docker compose --env-file .env.production ps
docker compose --env-file .env.production logs -f --tail=100 db backend frontend gateway-nginx
```

تست داخلی (لندینگ باید ۲۰۰ بدهد، نه ریدایرکت به لاگین):

```bash
curl -I http://127.0.0.1:18090/
curl -I http://127.0.0.1:18090/healthz
curl -I http://127.0.0.1:18090/login
curl http://127.0.0.1:18090/api/v1/health
```

انتظار برای `/`:
- `HTTP/1.1 200`
- بدون `Location: /login`

## 2.1 اگر backend unhealthy شد

لاگ را ببینید:

```bash
docker compose --env-file .env.production logs --tail=200 backend
docker compose --env-file .env.production ps
```

موارد رایج:
- migrate طول می‌کشد → healthcheck با `start_period` صبر می‌کند؛ دوباره `--build` بزنید.
- `ALLOWED_HOSTS` بدون `127.0.0.1` → در `.env.production` این‌ها را داشته باشید: `carnomand.ir,www.carnomand.ir,127.0.0.1,localhost,backend,gateway-nginx`
- `WORKFLOW_SECURE_SSL_REDIRECT` باید `false` باشد (TLS روی nginx خارجی است).

بازیابی سریع:

```bash
DOCKER_BUILDKIT=1 docker compose --env-file .env.production up -d --build backend
docker compose --env-file .env.production up -d
```


```bash
sudo mkdir -p /var/www/certbot
sudo cp /mnt/newvolume/PRG/carnomand/deploy/nginx/carnomand.ir.http.conf /etc/nginx/sites-available/carnomand.ir.conf
sudo ln -sf /etc/nginx/sites-available/carnomand.ir.conf /etc/nginx/sites-enabled/carnomand.ir.conf
sudo nginx -t
sudo systemctl reload nginx
```

SSL:

```bash
sudo certbot certonly --webroot -w /var/www/certbot -d carnomand.ir -d www.carnomand.ir
sudo cp /mnt/newvolume/PRG/carnomand/deploy/nginx/carnomand.ir.ssl.conf /etc/nginx/sites-available/carnomand.ir.conf
sudo nginx -t
sudo systemctl reload nginx
```

## 4. حجم‌ها و داده‌ها

- `docker-data/mysql`
- `docker-data/uploads`
- `docker-data/staticfiles`

## 5. آپدیت‌های بعدی

```bash
cd /mnt/newvolume/PRG/carnomand
git pull
DOCKER_BUILDKIT=1 docker compose --env-file .env.production up -d --build
```

بعد از بیلد، کش مرورگر را یک‌بار Hard Refresh کنید تا `index.html` جدید (لندینگ) لود شود.

## 6. نکات

- API فرانت از مسیر نسبی `/api/v1` استفاده می‌کند.
- روت‌های Vue با `try_files ... /index.html` سرو می‌شوند؛ `/` لندینگ است و `/login` صفحه ورود.
- اگر هنوز لاگین می‌بینید، احتمالاً بیلد قدیمی در کانتینر است یا `index.html` کش شده — دوباره `--build` بزنید.
- لوکیشن ورود/خروج با نقشه + Reverse نشان کار می‌کند؛ بدون وایت‌لیست دامنه، آدرس موقت می‌آید ولی ثبت مختصات همچنان ذخیره می‌شود.
- Geolocation روی دامنه HTTPS پایدارتر از HTTP/IP است؛ برای موبایل حتماً SSL دامنه را فعال کنید.
- متغیرهای `VITE_*` فقط در زمان `docker compose build` اعمال می‌شوند؛ تغییر `.env.production` بدون `--build` روی فرانت اثر ندارد.
