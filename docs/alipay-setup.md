# 支付宝支付接入教程（电脑网站支付）

## 一、前提条件

- 已有企业支付宝账号（个人账号无法接入开放平台）
- 已部署本系统，后端可公网访问（支付宝回调需要公网地址）

---

## 二、创建应用

1. 登录 [支付宝开放平台](https://open.alipay.com)
2. 控制台 → **创建应用** → 选择"网页&移动应用"
3. 填写应用名称，提交审核
4. 审核通过后获得 **APPID**（如 `2021000122XXXXXX`）

---

## 三、开通电脑网站支付能力

1. 进入应用详情 → **能力列表** → 添加能力
2. 搜索"电脑网站支付"，申请开通
3. 等待审核（通常 1 个工作日）

> 本系统使用 `alipay.trade.page.pay` 接口，用户点击支付后跳转至支付宝页面完成付款，支付完成后回跳到系统。

---

## 四、配置密钥（证书验证模式）

本系统使用**证书验证模式**（推荐，安全性更高）。

### 4.1 生成应用私钥并申请证书

1. 应用详情 → **开发设置** → 密钥管理 → 选择"公钥证书模式"
2. 使用支付宝"密钥工具"生成 RSA2 密钥对，得到应用私钥和应用公钥
3. 上传应用公钥后，下载以下三个证书文件：

| 文件名 | 说明 | 对应配置字段 |
|--------|------|------------|
| `appCertPublicKey_xxx.crt` | 应用公钥证书 | 应用证书（app_cert） |
| `alipayCertPublicKey_RSA2.crt` | 支付宝公钥证书 | 支付宝公钥证书（alipay_cert） |
| `alipayRootCert.crt` | 支付宝根证书 | 支付宝根证书（alipay_root_cert） |

### 4.2 获取证书内容

将证书文件内容（包含 `-----BEGIN CERTIFICATE-----` 头尾）完整复制，填入管理后台对应字段。

```bash
cat appCertPublicKey_xxx.crt        # 复制全部内容 → 应用证书
cat alipayCertPublicKey_RSA2.crt    # 复制全部内容 → 支付宝公钥证书
cat alipayRootCert.crt              # 复制全部内容 → 支付宝根证书
```

### 4.3 私钥格式说明

系统支持两种格式，自动识别：
- 带 PEM 头的完整格式（`-----BEGIN PRIVATE KEY-----`）
- 纯 Base64 字符串（不带 PEM 头，系统自动补全）

---

## 五、配置回调与跳转地址

### 异步回调地址（notify_url）

支付宝支付成功后异步通知本系统，格式：

```
https://www.eleconet.cn/api/payment/callback/alipay
```

**要求：**
- 必须是公网可访问的 HTTPS 地址
- 不能是 localhost 或内网地址

### 同步跳转地址（return_url）

用户在支付宝页面完成支付后，浏览器跳回的地址：

```
https://www.eleconet.cn/pricing
```

> `return_url` 仅用于页面跳转展示，订单状态以 `notify_url` 的异步通知为准。

本地开发 notify_url 可使用 ngrok：
```bash
ngrok http 8000
# https://xxxx.ngrok-free.app/api/payment/callback/alipay
```

---

## 六、在管理后台填写配置

登录系统管理员账号 → **系统设置** → **支付配置** → 支付宝：

| 字段 | 说明 |
|------|------|
| 启用 | 是否开启支付宝支付 |
| 沙箱模式 | 测试时开启，上线后关闭 |
| 证书验证模式 | 勾选（推荐），使用证书验证 |
| App ID | 开放平台的应用 APPID |
| 应用私钥 | RSA2 私钥内容（含或不含 PEM 头均可） |
| 应用证书 | `appCertPublicKey_xxx.crt` 文件全部内容 |
| 支付宝公钥证书 | `alipayCertPublicKey_RSA2.crt` 文件全部内容 |
| 支付宝根证书 | `alipayRootCert.crt` 文件全部内容 |
| 回调地址 | `https://www.eleconet.cn/api/payment/callback/alipay` |
| 跳转地址 | `https://www.eleconet.cn/pricing` |

填写完成后点击保存。

---

## 七、支付流程说明

1. 用户点击"升级套餐" → 选择支付宝
2. 系统创建订单，浏览器**自动跳转**至支付宝收银台
3. 用户在支付宝页面完成付款
4. 支付宝异步回调 `notify_url`，系统升级用户套餐
5. 浏览器跳回 `return_url` 页面

---

## 八、沙箱测试

### 8.1 开启沙箱模式

管理后台勾选"沙箱模式"，使用[沙箱环境](https://open.alipay.com/develop/sandbox/app)的密钥和 APPID。

沙箱 APPID 格式为 `9021000XXXXXXXXX`，沙箱网关为：
```
https://openapi-sandbox.dl.alipaydev.com/gateway.do
```

### 8.2 测试支付流程

1. 前端选择支付宝付款 → 跳转至沙箱收银台
2. 使用沙箱买家账号完成付款（账号在沙箱控制台查看）
3. 支付成功后系统自动升级套餐

### 8.3 模拟支付（跳过页面）

沙箱模式下可直接调用模拟支付接口，无需跳转：

```bash
curl -X POST https://www.eleconet.cn/api/payment/simulate-pay/{order_no} \
  -H "Authorization: Bearer {token}"
```

---

## 九、生产上线

1. 关闭沙箱模式（取消勾选"沙箱模式"）
2. 将 APPID、密钥替换为正式环境的值
3. notify_url 和 return_url 使用正式域名
4. 确认"电脑网站支付"能力审核已通过

---

## 十、常见问题

**Q: 点击支付后没有跳转**
- 检查 APPID 是否正确
- 检查私钥格式（确保是 RSA2，不是 RSA）
- 查看后端日志：`docker compose logs backend`

**Q: 支付成功但套餐没升级**
- 检查 notify_url 是否公网可访问
- 支付宝回调失败会重试 8 次（间隔递增），可在支付宝商户平台查看回调记录
- 确认 HTTPS 证书有效（自签名证书支付宝不认）

**Q: 验签失败**
- 支付宝公钥填写的是"支付宝公钥"而非"应用公钥"，注意区分

**Q: 本地测试时 notify_url 收不到回调**
- 使用 ngrok 暴露本地端口，或在沙箱模式下使用模拟支付接口
