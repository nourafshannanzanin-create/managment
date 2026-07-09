#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="/mnt/newvolume/PRG/managment"
SSL_CONF_SRC="$PROJECT_DIR/deploy/nginx/carnomand.ir.ssl.conf"
NGINX_CONF_DST="/etc/nginx/sites-available/carnomand.ir.conf"
NGINX_CONF_LINK="/etc/nginx/sites-enabled/carnomand.ir.conf"
CERT_PATH="/etc/letsencrypt/live/carnomand.ir/fullchain.pem"
KEY_PATH="/etc/letsencrypt/live/carnomand.ir/privkey.pem"

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root: sudo bash $0"
  exit 1
fi

if [[ ! -f "$CERT_PATH" || ! -f "$KEY_PATH" ]]; then
  echo "SSL certificate not found for carnomand.ir."
  echo "Run certbot first:"
  echo "  sudo certbot certonly --webroot -w /var/www/certbot -d carnomand.ir"
  exit 1
fi

cp "$SSL_CONF_SRC" "$NGINX_CONF_DST"
ln -sfn "$NGINX_CONF_DST" "$NGINX_CONF_LINK"

nginx -t
systemctl reload nginx

echo
echo "HTTPS routing for carnomand.ir is active."
