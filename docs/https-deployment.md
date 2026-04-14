# 生产 HTTPS 部署方案（eleconet.cn）

## 架构概览

```
Internet
   │  443/80
   ▼
 Nginx (反向代理 + SSL 终止)
   ├── /api  → backend:8000
   └── /     → frontend:3000

证书：acme.sh + 阿里云 DNS 验证（ZeroSSL 签发，自动续签）
```

---

## 一、文件结构

```
rag-knowledge-base/
├── nginx/
│   ├── conf.d/
│   │   └── app.conf          # Nginx 配置
│   └── certbot/
│       ├── conf/             # SSL 证书存放（volume 挂载）
│       └── www/              # webroot（保留备用）
└── docker-compose.yml
```

---

## 二、`nginx/conf.d/app.conf`

```nginx
# HTTP → 重定向到 HTTPS
server {
    listen 80;
    server_name eleconet.cn www.eleconet.cn;

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
    server_name eleconet.cn www.eleconet.cn;

    ssl_certificate     /etc/letsencrypt/live/eleconet.cn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/eleconet.cn/privkey.pem;

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

> 证书使用 acme.sh 在宿主机签发，不依赖 certbot Docker 服务。

---

## 四、证书签发（acme.sh + 阿里云 DNS）

### 背景

certbot 插件方案因系统 Python 版本过旧（3.6）及 certbot-dns-alidns 包缺失等问题均失败，
最终改用 **acme.sh**，纯 shell 脚本，原生支持阿里云 DNS API，无 Python 依赖。

### 4.1 创建阿里云 RAM 访问密钥

1. 登录阿里云控制台 → RAM 访问控制 → 用户 → 创建用户
2. 勾选「OpenAPI 调用访问」，保存 AccessKey ID 和 Secret
3. 为该用户附加权限策略：`AliyunDNSFullAccess`

### 4.2 安装 acme.sh

```bash
curl https://get.acme.sh | sh -s email=kyrenlee2025@outlook.com
source ~/.bashrc
```

### 4.3 签发证书

```bash
# 设置阿里云 AccessKey（替换为真实值）
export Ali_Key="你的AccessKeyId"
export Ali_Secret="你的AccessKeySecret"

# 签发（同时覆盖裸域名和 www）
~/.acme.sh/acme.sh --issue \
  --dns dns_ali \
  -d eleconet.cn \
  -d www.eleconet.cn
```

成功后证书位于：`/root/.acme.sh/eleconet.cn_ecc/`

### 4.4 安装证书到 Nginx volume 路径

```bash
mkdir -p /home/rag-knowledge-base/nginx/certbot/conf/live/eleconet.cn

~/.acme.sh/acme.sh --install-cert \
  -d eleconet.cn \
  --fullchain-file /home/rag-knowledge-base/nginx/certbot/conf/live/eleconet.cn/fullchain.pem \
  --key-file       /home/rag-knowledge-base/nginx/certbot/conf/live/eleconet.cn/privkey.pem \
  --reloadcmd      "docker compose -f /home/rag-knowledge-base/docker-compose.yml exec nginx nginx -s reload"
```

> 必须使用 `--fullchain-file` 而非 `--cert-file`，否则浏览器无法验证中间 CA，导致 SSL 错误。

acme.sh 会自动将续签命令写入 crontab，无需手动配置。

---

## 五、Vite 允许生产域名访问

Vite 默认只响应 localhost 的请求，通过 Nginx 代理后 Host 头变为生产域名会返回 403。

在 `frontend/vite.config.js` 中添加 `allowedHosts`：

```js
server: {
  port: 3000,
  allowedHosts: ['eleconet.cn', 'www.eleconet.cn'],
  proxy: {
    '/api': {
      target: 'http://backend:8000',
      changeOrigin: true,
    },
  },
},
```

---

## 六、启动服务

```bash
cd /home/rag-knowledge-base

# 首次启动（或拉取代码更新后）
docker compose up -d

# 仅重启前端（修改 vite.config.js 后）
docker compose restart frontend

# 验证 HTTPS
curl -I https://www.eleconet.cn
```

---

## 七、证书续签

acme.sh 安装时已自动写入 crontab，每天检查并在到期前 30 天自动续签，无需人工干预。

查看续签任务：

```bash
crontab -l | grep acme
```

---

## 八、CORS 配置（`backend/app/main.py`）

```python
allow_origins=[
    "https://eleconet.cn",
    "https://www.eleconet.cn",
    "http://localhost:3000",
    "http://localhost:5173",
]
```
