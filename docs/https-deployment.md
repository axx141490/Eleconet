# 生产 HTTPS 部署方案（www.elecone.chat）

## 架构概览

```
Internet
   │  443/80
   ▼
 Nginx (反向代理 + SSL 终止)
   ├── /api  → backend:8000
   └── /     → frontend:3000

Certbot (自动续签 Let's Encrypt 证书)
```

---

## 一、新增文件结构

```
rag-knowledge-base/
├── nginx/
│   ├── conf.d/
│   │   └── app.conf          # Nginx 配置
│   └── certbot/
│       ├── conf/             # Let's Encrypt 证书存放位置（volume）
│       └── www/              # ACME challenge webroot（volume）
├── init-letsencrypt.sh       # 首次签发证书脚本（只跑一次）
└── docker-compose.yml        # 新增 nginx + certbot 服务
```

---

## 二、`nginx/conf.d/app.conf`

```nginx
# ① HTTP → 仅用于 ACME challenge 和重定向
server {
    listen 80;
    server_name www.elecone.chat;

    # Certbot webroot challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # 其余全部跳转 HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

# ② HTTPS
server {
    listen 443 ssl;
    server_name www.elecone.chat;

    ssl_certificate     /etc/letsencrypt/live/www.elecone.chat/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.elecone.chat/privkey.pem;

    # 推荐安全参数
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    ssl_session_cache   shared:SSL:10m;
    ssl_session_timeout 10m;

    # 上传文件大小限制（按需调整）
    client_max_body_size 100M;

    # 后端 API
    location /api/ {
        proxy_pass         http://backend:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;

        # SSE / 流式响应
        proxy_buffering    off;
        proxy_read_timeout 300s;
    }

    # 前端
    location / {
        proxy_pass         http://frontend:3000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;

        # WebSocket 支持（Vite HMR 或 WS）
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
    }
}
```

---

## 三、`docker-compose.yml` 新增服务

```yaml
services:
  # ...原有 backend / frontend 服务不变...

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/certbot/conf:/etc/letsencrypt
      - ./nginx/certbot/www:/var/www/certbot
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

  certbot:
    image: certbot/certbot
    volumes:
      - ./nginx/certbot/conf:/etc/letsencrypt
      - ./nginx/certbot/www:/var/www/certbot
    # 每 12 小时尝试续签（证书快到期才会实际续签）
    entrypoint: >
      /bin/sh -c "trap exit TERM;
      while :; do
        certbot renew --webroot -w /var/www/certbot --quiet;
        sleep 12h & wait $${!};
      done"
    restart: unless-stopped
```

---

## 四、`init-letsencrypt.sh`（首次签发证书，只跑一次）

```bash
#!/bin/bash
DOMAIN="www.elecone.chat"
EMAIL="your@email.com"          # 替换为你的邮箱

# 先用临时自签名证书让 Nginx 能启动
mkdir -p ./nginx/certbot/conf/live/$DOMAIN
openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
  -keyout ./nginx/certbot/conf/live/$DOMAIN/privkey.pem \
  -out    ./nginx/certbot/conf/live/$DOMAIN/fullchain.pem \
  -subj "/CN=localhost"

# 启动 nginx（此时用的是假证书）
docker compose up -d nginx

# 删除假证书
rm -rf ./nginx/certbot/conf/live

# 正式签发 Let's Encrypt 证书
docker compose run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  --email $EMAIL --agree-tos --no-eff-email \
  -d $DOMAIN

# 重载 nginx 使用真证书
docker compose exec nginx nginx -s reload

echo "HTTPS 配置完成！"
```

---

## 五、CORS 更新（`backend/app/main.py`）

```python
# 将 origins 改为生产域名
allow_origins=[
    "https://www.elecone.chat",
    "http://localhost:3000",   # 本地开发保留
]
```

---

## 六、部署步骤

```bash
# 1. 确保域名 DNS 已解析到服务器 IP
# 2. 服务器防火墙开放 80 和 443 端口

# 3. 首次签发证书
chmod +x init-letsencrypt.sh
./init-letsencrypt.sh

# 4. 正式启动所有服务
docker compose up -d

# 5. 验证
curl -I https://www.elecone.chat
```

---

## 七、证书续签

Certbot 容器已配置每 12 小时自动尝试续签，**无需人工干预**。Let's Encrypt 证书有效期 90 天，到期前 30 天内会自动续签成功。
