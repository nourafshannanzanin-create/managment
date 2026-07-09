#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="/mnt/newvolume/PRG/managment"
HTTP_CONF_SRC="$PROJECT_DIR/deploy/nginx/carnomand.ir.http.conf"
NGINX_CONF_DST="/etc/nginx/sites-available/carnomand.ir.conf"
NGINX_CONF_LINK="/etc/nginx/sites-enabled/carnomand.ir.conf"
CERTBOT_ROOT="/var/www/certbot"

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root: sudo bash $0"
  exit 1
fi

mkdir -p "$CERTBOT_ROOT"
cp "$HTTP_CONF_SRC" "$NGINX_CONF_DST"
ln -sfn "$NGINX_CONF_DST" "$NGINX_CONF_LINK"

nginx -t
systemctl reload nginx

echo
echo "HTTP routing for carnomand.ir is active."
echo "Next step:"
echo "  sudo certbot certonly --webroot -w $CERTBOT_ROOT -d carnomand.ir"
