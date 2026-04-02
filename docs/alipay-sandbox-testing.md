# 支付宝沙箱测试指南

## 前提条件

- 已有支付宝开放平台账号，沙箱应用已创建
- 本地 Docker 服务正常运行（前端 `localhost:3000`，后端 `localhost:8000`）
- 已安装 ngrok

---

## 第一步：获取沙箱密钥

### 1.1 获取 App ID

登录 [支付宝开放平台沙箱](https://open.alipay.com/develop/sandbox/app)，在"基本信息"中复制 **APPID**。

```
示例：9021000162655436
```

### 1.2 生成应用密钥对

在本地终端执行：

```bash
# 生成私钥
openssl genrsa -out app_private_key.pem 2048

# 从私钥提取公钥
openssl rsa -in app_private_key.pem -pubout -out app_public_key.pem

# 查看私钥内容（待会要填入系统）
cat app_private_key.pem

# 查看公钥内容（待会要上传到支付宝）
cat app_public_key.pem
```

### 1.3 上传公钥到支付宝沙箱

1. 沙箱控制台 → **开发信息** → 接口加签方式选择 **自定义密钥**
2. 点击"设置"→ 选择"公钥模式"
3. 将 `app_public_key.pem` 的内容粘贴进去（去掉首尾的 `-----BEGIN/END PUBLIC KEY-----` 行）
4. 保存后，支付宝会显示对应的 **支付宝公钥**，复制保存备用

---

## 第二步：配置 ngrok 内网穿透

支付宝需要回调你的服务器，本地服务必须通过 ngrok 暴露到公网。

### 2.1 安装 ngrok

```bash
# macOS
brew install ngrok

# 或直接下载：https://ngrok.com/download
```

### 2.2 注册并配置 token

前往 [ngrok.com](https://ngrok.com) 注册免费账号，复制 Authtoken：

```bash
ngrok config add-authtoken 你的authtoken
```

### 2.3 启动穿透

```bash
ngrok http 8000
```

终端输出类似：

```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8000
```

记录这个 `https://abc123.ngrok-free.app` 地址（每次重启 ngrok 地址会变）。

---

## 第三步：填写系统配置

登录 RAG 系统（管理员账号），进入 **模型配置** 页面，滚动到底部"支付配置"区块。

### 支付宝字段填写

| 字段 | 填写内容 |
|------|---------|
| App ID | 沙箱的 APPID，如 `9021000162655436` |
| 应用私钥（RSA2） | `app_private_key.pem` 的完整内容（含首尾行） |
| 支付宝公钥 | 第 1.3 步从支付宝控制台复制的公钥字符串 |
| 回调通知 URL | `https://abc123.ngrok-free.app/api/payment/callback/alipay` |
| 同步跳转 URL | 可留空，或填 `https://abc123.ngrok-free.app/pricing` |

勾选：
- ☑ **启用支付宝**
- ☑ **沙箱模式（测试用）**

点击 **保存支付配置**。

---

## 第四步：获取沙箱买家账号

沙箱支付需要用沙箱买家账号扫码，不能用真实支付宝账号。

1. 沙箱控制台左侧 → **沙箱账号**
2. 找到"买家信息"，记录**账号**和**登录密码**、**支付密码**
3. 手机下载**支付宝沙箱版 App**（仅 Android）：
   - 沙箱控制台左侧 → **沙箱工具** → 下载沙箱 App
   - 用沙箱买家账号登录

> **iOS 用户**：无法安装沙箱 App，可以使用支付宝网页版在电脑浏览器扫码完成支付。

---

## 第五步：发起测试支付

1. 打开 RAG 系统，登录一个**非管理员的 Free 用户**
2. 点击侧边栏 **升级套餐**
3. 选择 Pro 或 Enterprise，选择时长，点击 **支付宝** 按钮
4. 页面显示二维码
5. 用沙箱 App 或电脑浏览器扫描二维码
6. 使用沙箱买家账号完成支付
7. 系统每 3 秒轮询一次状态，支付成功后自动跳转"支付成功"页面

---

## 第六步：验证结果

### 检查用户套餐是否升级

方法一：查看侧边栏用户名旁的套餐标签，应由 `FREE` 变为 `PRO` 或 `ENTERPRISE`。

方法二：管理员进入**用户管理**页面，查看对应用户的套餐列是否已更新。

方法三：直接查数据库：

```bash
docker exec $(docker ps -qf "name=backend") python -c "
import asyncio, aiosqlite

async def check():
    async with aiosqlite.connect('/app/data/app.db') as db:
        cursor = await db.execute('SELECT username, tier, tier_expires_at FROM users')
        for row in await cursor.fetchall():
            print(row)

asyncio.run(check())
"
```

### 检查订单记录

```bash
docker exec $(docker ps -qf "name=backend") python -c "
import asyncio, aiosqlite

async def check():
    async with aiosqlite.connect('/app/data/app.db') as db:
        cursor = await db.execute(
            'SELECT order_no, tier, amount_fen, pay_method, status, paid_at FROM payment_orders'
        )
        for row in await cursor.fetchall():
            print(row)

asyncio.run(check())
"
```

---

## 常见问题

**Q：二维码显示但扫码后提示"订单不存在"**
A：确认已勾选"沙箱模式"并保存，沙箱和正式环境网关地址不同。

**Q：保存配置后支付宝仍显示"未配置"**
A：检查"启用支付宝"是否已勾选，勾选后必须点保存。

**Q：ngrok 地址变了怎么办**
A：每次重启 ngrok 地址会变，需要重新填写回调通知 URL 并保存配置。可以购买 ngrok 固定域名（约 $8/月）避免此问题。

**Q：回调没有触发，用户套餐没升级**
A：
1. 检查 ngrok 终端是否有请求进来
2. 查看后端日志：`docker logs $(docker ps -qf "name=backend") --tail 50`
3. 确认回调 URL 填写正确，末尾没有多余的斜杠

**Q：iOS 无法安装沙箱 App**
A：在电脑浏览器打开支付宝网页版 `https://sandbox.alipaydev.com`，用沙箱账号密码登录后扫码支付。

---

## 切换正式环境

测试通过后，切换正式环境只需：

1. 在支付宝开放平台创建正式应用，完成资质审核
2. 替换 App ID、私钥、支付宝公钥为正式环境的值
3. 将回调 URL 改为正式域名
4. **取消勾选"沙箱模式"**
5. 保存配置
