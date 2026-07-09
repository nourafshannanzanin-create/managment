# Docker Deploy For `carnomand.ir`

این پروژه برای همین سرور به صورت Docker آماده شده و همه بخش‌ها را بالا می‌آورد:

- `db`: MySQL 8.4
- `backend`: Django + Gunicorn
- `frontend`: Vue/Vite build شده داخل Nginx
- `gateway-nginx`: ورودی داخلی برای SPA، API و فایل‌های آپلود

معماری این استقرار برای همین سرور عمدا روی `127.0.0.1:18090` بسته شده تا با سایت‌های فعلی روی `80/443` تداخل نداشته باشد. دامنه `carnomand.ir` باید از nginx اصلی سرور به این gateway وصل شود.

## 1. آماده‌سازی env

```bash
cd /mnt/newvolume/PRG/managment
cp -n .env.production.example .env.production
nano .env.production
```

حداقل این مقدارها را عوض کنید:

```env
MYSQL_ROOT_PASSWORD=strong-root-password
WORKFLOW_SECRET_KEY=very-long-random-secret
WORKFLOW_MYSQL_PASSWORD=strong-db-password
WORKFLOW_ALLOWED_HOSTS=carnomand.ir,www.carnomand.ir,127.0.0.1,localhost,backend,gateway-nginx
WORKFLOW_FRONTEND_ORIGINS=https://carnomand.ir,https://www.carnomand.ir,http://carnomand.ir,http://www.carnomand.ir
WORKFLOW_CSRF_TRUSTED_ORIGINS=https://carnomand.ir,https://www.carnomand.ir,http://carnomand.ir,http://www.carnomand.ir
WORKFLOW_AUTO_SEED_DB=false
```

اگر می‌خواهید بار اول با داده نمونه بالا بیاید، `WORKFLOW_AUTO_SEED_DB=true` بگذارید.

## 2. بالا آوردن Docker

```bash
cd /mnt/newvolume/PRG/managment
DOCKER_BUILDKIT=1 docker compose --env-file .env.production up -d --build
```

اگر MySQL قبلا با تنظیمات خراب initialize شده و `db` بالا نمی‌آید، یک‌بار reset تمیز انجام دهید:

```bash
cd /mnt/newvolume/PRG/managment
sudo docker compose --env-file .env.production down -v
sudo docker volume rm workflow-hub_workflow_mysql_data 2>/dev/null || true
sudo DOCKER_BUILDKIT=1 docker compose --env-file .env.production up -d --build
```

برای دیدن وضعیت:

```bash
docker compose --env-file .env.production ps
docker compose --env-file .env.production logs -f --tail=100 db backend frontend gateway-nginx
```

تست داخلی:

```bash
curl -I http://127.0.0.1:18090/healthz
curl -I http://127.0.0.1:18090/login
curl http://127.0.0.1:18090/api/v1/health
```

## 3. اتصال دامنه در nginx اصلی سرور

فعلا `80/443` این سرور توسط nginx اصلی گرفته شده‌اند. برای همین باید دامنه `carnomand.ir` را به `127.0.0.1:18090` وصل کنید.

اول فایل HTTP برای bootstrap و certbot:

```bash
sudo mkdir -p /var/www/certbot
sudo cp /mnt/newvolume/PRG/managment/deploy/nginx/carnomand.ir.http.conf /etc/nginx/sites-available/carnomand.ir.conf
sudo ln -sf /etc/nginx/sites-available/carnomand.ir.conf /etc/nginx/sites-enabled/carnomand.ir.conf
sudo nginx -t
sudo systemctl reload nginx
```

گرفتن SSL:

```bash
sudo certbot certonly --webroot -w /var/www/certbot -d carnomand.ir -d www.carnomand.ir
```

بعد فایل SSL نهایی:

```bash
sudo cp /mnt/newvolume/PRG/managment/deploy/nginx/carnomand.ir.ssl.conf /etc/nginx/sites-available/carnomand.ir.conf
sudo nginx -t
sudo systemctl reload nginx
```

اگر نمی‌خواهید `www` داشته باشید، آن را از `server_name` و فرمان certbot حذف کنید.

## 4. حجم‌ها و داده‌ها

این استقرار از volume های زیر استفاده می‌کند:

- `workflow_mysql_data`: دیتابیس
- `workflow_uploads`: فایل‌های آپلود و خروجی پردازش
- `workflow_staticfiles`: فایل‌های static بک‌اند

برای بکاپ:

```bash
docker run --rm -v workflow-hub_workflow_mysql_data:/var/lib/mysql -v "$(pwd)":/backup alpine tar czf /backup/mysql-volume-backup.tar.gz /var/lib/mysql
docker run --rm -v workflow-hub_workflow_uploads:/data -v "$(pwd)":/backup alpine tar czf /backup/uploads-volume-backup.tar.gz /data
```

## 5. آپدیت‌های بعدی

```bash
cd /mnt/newvolume/PRG/managment
git pull
DOCKER_BUILDKIT=1 docker compose --env-file .env.production up -d --build
```

## 6. نکات مهم

- `backend` هنگام start شدن، منتظر MySQL می‌ماند، migration را اجرا می‌کند و در صورت نیاز seed می‌کند.
- API از داخل فرانت با `/api/v1` صدا زده می‌شود و برای production دیگر به IP لوکال وابسته نیست.
- پردازش تصویر داخل همان کانتینر backend بالا می‌آید و نیاز به سرویس جداگانه ندارد.
- اگر بخواهید این پروژه مستقیما خودش روی `80/443` بالا بیاید، باید nginx اصلی سرور یا سایت‌های دیگر را جابه‌جا کنید.
