# 微信支付配置教程

## 前提条件

- 已有微信支付商户号（个人或企业均可，需完成实名认证）
- 本地 Docker 服务正常运行（前端 `localhost:3000`，后端 `localhost:8000`）
- 已安装 ngrok（用于接收微信回调）

> **注意：微信支付没有沙箱环境。** 测试时需使用真实商户号，建议以 ¥0.01 小额测试，验证后退款。

---

## 第一步：获取商户信息

### 1.1 登录微信支付商户平台

前往 [pay.weixin.qq.com](https://pay.weixin.qq.com) 登录商户后台。

### 1.2 获取商户号（mchid）

登录商户后台后，右上角或 **账户中心 → 商户信息** 中可以看到纯数字的商户号，如 `1234567890`。

### 1.3 获取 AppID

> **注意：AppID 不在微信支付商户后台，而是在微信开放平台或公众平台。**

本系统使用 Native 支付（PC 网页扫码），AppID 来源取决于你的接入方式：

**方案 A：使用微信开放平台网站应用（推荐）**

1. 前往 [open.weixin.qq.com](https://open.weixin.qq.com) 登录
2. 顶部菜单 → **管理中心 → 网站应用**
3. 找到对应应用，AppID 显示在应用名称下方，格式如 `wx1234567890abcdef`
4. 如果没有网站应用，点击「创建网站应用」，填写资料提交审核（需 300 元认证费）

**方案 B：使用微信公众号 AppID**

1. 前往 [mp.weixin.qq.com](https://mp.weixin.qq.com) 登录
2. 左侧菜单 → **设置与开发 → 基本配置**
3. 页面顶部即可看到 AppID

获取 AppID 后，还需将其与商户号绑定：

- 微信支付商户后台 → **产品中心 → AppID 账号管理** → 关联 AppID
- 或由 AppID 所属平台主动发起绑定邀请

绑定完成后方可正常发起支付。

---

## 第二步：生成 API 证书和密钥

微信支付 v3 使用证书鉴权，需要在商户后台申请。

### 2.1 下载商户 API 证书

1. 商户后台 → **账户中心 → API 安全**
2. 点击「申请 API 证书」，按提示完成操作（需安装微信支付证书助手工具）
3. 生成完成后，下载得到以下文件：
   - `apiclient_key.pem` — 商户私钥（**重要，不要泄露**）
   - `apiclient_cert.pem` — 商户证书
   - `apiclient_cert.p12` — 证书 p12 格式

### 2.2 获取证书序列号（cert_serial_no）

```bash
# 查看证书序列号
openssl x509 -in apiclient_cert.pem -noout -serial
```

输出类似：

```
serial=6F2D8B4A1C9E3D7F0A5B2C8E4D1F6A3B9C2E7D4
```

记录这个序列号（不含 `serial=` 前缀）。

### 2.3 查看私钥内容

```bash
cat apiclient_key.pem
```

复制完整内容（含 `-----BEGIN PRIVATE KEY-----` 首尾行），待会填入系统。

### 2.4 获取微信支付公钥（新版商户必须）

> **说明：** 2024 年后新注册的商户平台已切换为「微信支付公钥」模式，不再提供传统平台证书。如果你在第五步填完配置后仍下单失败，请检查商户平台是否已切换到公钥模式。

1. 商户后台 → **账户中心 → API 安全 → 微信支付公钥**
2. 点击「申请/查看微信支付公钥」
3. 下载公钥文件，内容格式为：
   ```
   -----BEGIN PUBLIC KEY-----
   MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
   -----END PUBLIC KEY-----
   ```
4. 记录页面上显示的**公钥 ID**，格式为 `PUB_KEY_ID_0114xxxxxxxxx`

---

## 第三步：设置 APIv3 密钥

APIv3 密钥用于微信回调通知的解密验签。

1. 商户后台 → **账户中心 → API 安全 → APIv3 密钥**
2. 点击「设置 APIv3 密钥」
3. 输入一个 32 位字符串（可自行生成，如下）：

```bash
# 生成随机 32 位字符串
openssl rand -hex 16
```

4. 保存后，记录这个 32 位密钥备用。

---

## 第四步：配置 ngrok 内网穿透

微信支付需要向你的服务器发送支付结果通知，本地服务必须通过 ngrok 暴露到公网。

### 4.1 安装 ngrok

```bash
# macOS
brew install ngrok
```

### 4.2 注册并配置 token

前往 [ngrok.com](https://ngrok.com) 注册免费账号，复制 Authtoken：

```bash
ngrok config add-authtoken 你的authtoken
```

### 4.3 启动穿透

```bash
ngrok http 8000
```

终端输出类似：

```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8000
```

记录这个 `https://abc123.ngrok-free.app` 地址（每次重启 ngrok 地址会变）。

---

## 第五步：填写系统配置

登录 RAG 系统（管理员账号），进入 **模型配置** 页面，滚动到底部"支付配置"区块。

### 微信支付字段填写

| 字段 | 填写内容 |
|------|---------|
| AppID | 关联公众号或小程序的 AppID，如 `wx1234567890abcdef` |
| 商户号（mchid） | 纯数字商户号，如 `1234567890` |
| 商户私钥 | `apiclient_key.pem` 的完整内容（含首尾行） |
| 证书序列号 | 第 2.2 步获取的序列号，如 `6F2D8B4A1C9E3D7F...` |
| APIv3 密钥 | 第三步设置的 32 位字符串 |
| 回调通知 URL | `https://abc123.ngrok-free.app/api/payment/callback/wechat` |
| 微信支付公钥 | 第 2.4 步下载的公钥文件完整内容（新版商户必填） |
| 公钥 ID | 第 2.4 步记录的公钥 ID，如 `PUB_KEY_ID_0114xxxxxx`（新版商户必填） |

勾选：
- ☑ **启用微信支付**

点击 **保存支付配置**。

---

## 第六步：配置微信支付回调白名单（可选）

如果商户后台要求配置回调域名白名单：

1. 商户后台 → **产品中心 → Native 支付**
2. 在「支付授权目录」或「回调域名」中添加 ngrok 域名：`abc123.ngrok-free.app`

---

## 第七步：发起测试支付

1. 打开 RAG 系统，登录一个**非管理员的 Free 用户**
2. 点击侧边栏 **升级套餐**
3. 选择 Pro 或 Enterprise，选择时长，点击 **微信支付** 按钮
4. 页面显示二维码
5. 用微信 App 扫描二维码，完成真实支付（建议选最短时长，金额最小）
6. 系统每 3 秒轮询一次状态，支付成功后自动跳转"支付成功"页面

---

## 第八步：验证结果

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

**Q：下单失败，提示"微信支付下单失败，请检查配置"**
A：按以下顺序排查：
1. 检查 AppID、mchid、私钥、证书序列号、APIv3 密钥是否填写正确
2. 私钥必须是 `apiclient_key.pem` 的完整内容，包含 `-----BEGIN PRIVATE KEY-----` 首尾行，中间不能混入其他文字
3. 如后端日志出现 `无可用的平台证书` 或 `RESOURCE_NOT_EXISTS`，说明商户已切换为公钥模式，需在商户后台获取微信支付公钥和公钥 ID 并填入配置（见第 2.4 步）

**Q：扫码后提示"商家参数格式有误，请联系商家解决"**
A：AppID 与商户号不匹配，确认该 AppID 已在商户后台完成关联绑定。

**Q：支付成功但用户套餐没升级**
A：
1. 检查 ngrok 终端是否收到了回调请求（POST 到 `/api/payment/callback/wechat`）
2. 查看后端日志：`docker logs $(docker ps -qf "name=backend") --tail 50`
3. 确认回调 URL 末尾没有多余的斜杠

**Q：ngrok 地址变了怎么办**
A：每次重启 ngrok 地址会变，需要重新填写回调通知 URL 并保存配置。可购买 ngrok 固定域名（约 $8/月）避免此问题。

**Q：如何退款测试金额**
A：商户后台 → **交易中心 → 全部订单** 中找到对应订单，点击"退款"即可。

---

## 切换正式环境

测试通过后，正式上线只需：

1. 将 ngrok 回调 URL 改为正式服务器域名，如 `https://yourdomain.com/api/payment/callback/wechat`
2. 确认正式域名已在微信商户后台完成白名单配置
3. 保存配置

AppID、mchid、证书等均使用同一套，无需更换。
