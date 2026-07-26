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
```

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

## 3. اتصال دامنه در nginx اصلی سرور

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
