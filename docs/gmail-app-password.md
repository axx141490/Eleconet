# Gmail 应用专用密码获取教程

## 前提条件

Gmail 账号已开启**两步验证**（必须，否则无法生成应用专用密码）。

---

## 第一步：开启两步验证（已开启可跳过）

1. 访问 [myaccount.google.com](https://myaccount.google.com)
2. 左侧点击「**安全性**」
3. 找到「两步验证」，点击进入并按提示完成开启

---

## 第二步：生成应用专用密码

1. 访问 [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   （或在「安全性」页面搜索栏搜「应用专用密码」）

2. 可能需要再次输入 Google 账号密码验证身份

3. 在「应用名称」输入框中填写一个名称，例如：
   ```
   RAG知识库
   ```

4. 点击「**创建**」

5. 页面会显示一个 **16 位密码**，格式如下：
   ```
   xxxx xxxx xxxx xxxx
   ```

6. 复制这个密码（**只显示一次，关闭后无法再查看**）

---

## 第三步：填写到 .env 配置

打开 `backend/.env`，将以下字段替换为真实值：

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your@gmail.com
SMTP_PASSWORD=xxxxxxxxxxxxxxxx
SMTP_FROM=your@gmail.com
```

> `SMTP_PASSWORD` 填入 16 位密码时**去掉中间的空格**，例如 `abcdabcdabcdabcd`。

---

## 常见问题

**Q：找不到「应用专用密码」入口**
A：确认两步验证已开启，且账号不是 Google Workspace 企业账号（企业账号需管理员在后台开放此功能）。

**Q：发送时报错 `535 Authentication failed`**
A：检查 `SMTP_PASSWORD` 是否填的是应用专用密码而不是 Gmail 登录密码，两者不同。

**Q：应用专用密码丢了怎么办**
A：无法找回，重新生成一个新的，替换 `.env` 中的 `SMTP_PASSWORD` 即可。旧密码自动失效。

**Q：如何撤销应用专用密码**
A：回到 [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)，找到对应条目点击删除即可。
