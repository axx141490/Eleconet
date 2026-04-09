# 生产 HTTPS 部署方案（elecone.chat）

## 架构概览

```
Internet
   │  443/80
   ▼
 Nginx (反向代理 + SSL 终止)
   ├── /api  → backend:8000
   └── /     → frontend:3000

证书签发：Let's Encrypt + 阿里云 DNS 验证（certbot-dns-alidns）
```

---

## 一、文件结构

```
rag-knowledge-base/
├── nginx/
│   ├── conf.d/
│   │   └── app.conf          # Nginx 配置
│   └── certbot/
│       ├── conf/             # Let's Encrypt 证书（volume 挂载）
│       └── www/              # webroot（保留备用）
└── docker-compose.yml
```

---

## 二、`nginx/conf.d/app.conf`

```nginx
# HTTP → 重定向到 HTTPS
server {
    listen 80;
    server_name elecone.chat www.elecone.chat;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS
server {
    listen 443 ssl;
    server_name elecone.chat www.elecone.chat;

    ssl_certificate     /etc/letsencrypt/live/elecone.chat/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/elecone.chat/privkey.pem;

    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    ssl_session_cache   shared:SSL:10m;
    ssl_session_timeout 10m;

    client_max_body_size 100M;

    # 后端 API
    location /api/ {
        proxy_pass         http://backend:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
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
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
    }
}
```

---

## 三、`docker-compose.yml` nginx 服务

```yaml
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
```

> certbot 不再作为 Docker 服务运行，改为宿主机直接安装，用阿里云 DNS 插件签发和续签。

---

## 四、证书签发（阿里云 DNS 验证）

### 4.1 创建阿里云 RAM 访问密钥

1. 登录阿里云控制台 → RAM 访问控制 → 用户 → 创建用户
2. 勾选「OpenAPI 调用访问」，保存 AccessKey ID 和 Secret
3. 为该用户附加权限策略：`AliyunDNSFullAccess`

### 4.2 安装 certbot 及阿里云插件

```bash
pip3 install certbot certbot-dns-alidns
```

### 4.3 配置凭证文件

```bash
mkdir -p ~/.secrets/certbot
cat > ~/.secrets/certbot/alidns.ini << EOF
dns_alidns_access_key = 你的AccessKeyId
dns_alidns_access_key_secret = 你的AccessKeySecret
EOF
chmod 600 ~/.secrets/certbot/alidns.ini
```

### 4.4 签发证书

```bash
certbot certonly \
  --authenticator dns-alidns \
  --dns-alidns-credentials ~/.secrets/certbot/alidns.ini \
  --dns-alidns-propagation-seconds 60 \
  -d elecone.chat -d www.elecone.chat \
  --email kyrenlee2025@outlook.com --agree-tos --no-eff-email
```

成功后证书位于宿主机：`/etc/letsencrypt/live/elecone.chat/`

### 4.5 将证书同步到 Docker volume 路径

```bash
cp -rL /etc/letsencrypt/live  ./nginx/certbot/conf/live
cp -r  /etc/letsencrypt/archive ./nginx/certbot/conf/archive
```

> `-L` 参数展开符号链接，确保实际证书文件被复制。

---

## 五、启动服务

```bash
# 首次启动
docker compose up -d

# 验证
curl -I https://www.elecone.chat
```

---

## 六、证书续签

Let's Encrypt 证书有效期 90 天，设置 cron 自动续签：

```bash
# 编辑 crontab
crontab -e

# 添加以下内容（每天凌晨 2 点检查）
0 2 * * * certbot renew --quiet && \
  cp -rL /etc/letsencrypt/live /home/rag-knowledge-base/nginx/certbot/conf/live && \
  cp -r  /etc/letsencrypt/archive /home/rag-knowledge-base/nginx/certbot/conf/archive && \
  docker compose -f /home/rag-knowledge-base/docker-compose.yml exec nginx nginx -s reload
```

---

## 七、CORS 配置（`backend/app/main.py`）

```python
allow_origins=[
    "https://elecone.chat",
    "https://www.elecone.chat",
    "http://localhost:3000",
]
```
