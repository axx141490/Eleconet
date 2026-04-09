#!/bin/bash
set -e

DOMAIN="www.elecone.chat"
EMAIL="your@email.com"          # 替换为你的邮箱

echo ">>> [1/5] 创建临时自签名证书，让 Nginx 能首次启动..."
mkdir -p ./nginx/certbot/conf/live/$DOMAIN
openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
  -keyout ./nginx/certbot/conf/live/$DOMAIN/privkey.pem \
  -out    ./nginx/certbot/conf/live/$DOMAIN/fullchain.pem \
  -subj "/CN=localhost"

echo ">>> [2/5] 启动 Nginx（使用临时证书）..."
docker compose up -d nginx

echo ">>> [3/5] 等待 Nginx 就绪..."
sleep 5

echo ">>> [4/5] 删除临时证书，签发 Let's Encrypt 正式证书..."
rm -rf ./nginx/certbot/conf/live

docker compose run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  --email "$EMAIL" --agree-tos --no-eff-email \
  -d "$DOMAIN"

echo ">>> [5/5] 重载 Nginx 使用正式证书..."
docker compose exec nginx nginx -s reload

echo ""
echo "✅ HTTPS 配置完成！访问 https://$DOMAIN 验证。"
