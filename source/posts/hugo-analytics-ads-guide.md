---
title: "Hugo 博客添加访问统计和广告联盟完整指南 - Google Analytics/百度统计/AdSense"
date: 2026-03-26T09:40:00+00:00
lastmod: 2026-03-26T09:40:00+00:00
categories: ["tech"]
tags: ["hugo", "tutorial", "analytics", "adsense", "guide"]
draft: false
---

## 📋 前言

本教程详细介绍如何为您的 Hugo 博客（Cloudflare Pages 部署）添加：

1. **访问统计**：Google Analytics 4 / 百度统计 / Plausible
2. **广告联盟**：Google AdSense / 百度联盟 / 其他替代方案

**适用场景**：
- ✅ Hugo + GitHub + Cloudflare Pages 部署
- ✅ 个人博客/技术博客
- ✅ 想要了解访客数据和变现

---

## ⚠️ 重要提醒

### 关于广告联盟

**Google AdSense**：
- ❌ 需要网站有一定流量和内容质量
- ❌ 审核较严格（通常 1-2 周）
- ❌ 需要绑定 AdSense 账号和收款方式
- ✅ 收益相对稳定，单价较高

**百度联盟**：
- ❌ 需要 ICP 备案（国内服务器）
- ❌ 审核严格，需要一定流量
- ✅ 国内访问速度快

**替代方案**（推荐新手）：
- ✅ **Buy Me a Coffee**：读者自愿打赏
- ✅ **爱发电**：国内创作者赞助平台
- ✅ **赞赏码**：微信/支付宝收款码

---

## 📊 第一部分：添加访问统计

### 方案一：Google Analytics 4（推荐海外流量）

#### 步骤 1：注册 Google Analytics

1. 访问：https://analytics.google.com/
2. 使用 Google 账号登录
3. 点击"开始衡量"
4. 创建账号（账号名称随意，如"我的博客"）
5. 创建媒体资源（选择"Web"）
6. 填写网站信息：
   - **网站名称**：您的博客名称
   - **网站网址**：https://blog.caowo.de/
   - **行业类别**：选择对应的
   - **业务规模**：个人/小型
7. 点击"创建"

#### 步骤 2：获取测量 ID

创建完成后，您会看到：
- **测量 ID**：格式如 `G-XXXXXXXXXX`
- **数据流 ID**：复制这个 ID

#### 步骤 3：在 Hugo 中配置

**方法 A：使用 Hugo 内置支持（推荐）**

编辑 `config.toml`：

```toml
# Google Analytics
googleAnalytics = "G-XXXXXXXXXX"

# 或者使用 params 配置
[params]
  [params.analytics]
    provider = "google"
    [params.analytics.google]
      id = "G-XXXXXXXXXX"
      anonymizeIP = true  # 匿名化 IP（GDPR 合规）
```

**方法 B：手动添加代码**

创建 `layouts/partials/head-custom.html`：

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX', {
    'anonymize_ip': true
  });
</script>
```

#### 步骤 4：部署验证

```bash
# 本地测试
hugo server -D

# 访问 http://localhost:1313
# 右键 → 检查 → Network → 查看 gtag/js 是否加载
```

**推送并部署**：

```bash
git add .
git commit -m "添加 Google Analytics 统计"
git push
```

#### 步骤 5：验证数据

1. 等待 24-48 小时（数据延迟）
2. 访问 Google Analytics 后台
3. 查看"实时"报告，确认有访客数据

---

### 方案二：百度统计（推荐国内流量）

#### 步骤 1：注册百度统计

1. 访问：https://tongji.baidu.com/
2. 使用百度账号登录
3. 点击"添加网站"
4. 填写网站信息：
   - **网站域名**：blog.caowo.de
   - **网站名称**：您的博客名称
   - **网站主页**：https://blog.caowo.de/
5. 同意协议，点击"确定"

#### 步骤 2：获取统计代码

添加网站后，您会看到统计代码：

```html
<script>
var _hmt = _hmt || [];
(function() {
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com/hm.js?xxxxxxxxxxxxxxxx";
  var s = document.getElementsByTagName("script")[0]; 
  s.parentNode.insertBefore(hm, s);
})();
</script>
```

**复制其中的 ID**：`xxxxxxxxxxxxxxxx`

#### 步骤 3：在 Hugo 中配置

**方法 A：使用主题支持**

如果您的主题支持百度统计，编辑 `config.toml`：

```toml
[params]
  baiduAnalytics = "xxxxxxxxxxxxxxxx"
```

**方法 B：手动添加代码**

创建 `layouts/partials/baidu-analytics.html`：

```html
<!-- 百度统计 -->
<script>
var _hmt = _hmt || [];
(function() {
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com/hm.js?xxxxxxxxxxxxxxxx";
  var s = document.getElementsByTagName("script")[0]; 
  s.parentNode.insertBefore(hm, s);
})();
</script>
```

然后在 `layouts/partials/head.html` 中添加：

```html
{{ partial "baidu-analytics.html" . }}
```

#### 步骤 4：部署验证

```bash
# 本地测试
hugo server -D

# 查看源代码，确认百度统计代码已加载
```

**推送并部署**：

```bash
git add .
git commit -m "添加百度统计"
git push
```

---

### 方案三：Plausible Analytics（隐私友好型）

**优势**：
- ✅ 轻量级（1KB vs Google 的 45KB）
- ✅ 无需 Cookie（GDPR 合规）
- ✅ 开源、尊重隐私
- ✅ 界面简洁易用

**劣势**：
- ❌ 付费服务（9 美元/月起）
- ❌ 需要自部署或使用官方服务

#### 步骤 1：注册 Plausible

1. 访问：https://plausible.io/
2. 点击"Start your free trial"
3. 填写网站信息
4. 选择付费计划（14 天免费试用）

#### 步骤 2：获取脚本

注册后，您会看到：

```html
<script defer data-domain="blog.caowo.de" src="https://plausible.io/js/script.js"></script>
```

#### 步骤 3：在 Hugo 中配置

创建 `layouts/partials/plausible-analytics.html`：

```html
<!-- Plausible Analytics -->
<script defer data-domain="blog.caowo.de" src="https://plausible.io/js/script.js"></script>
```

在 `layouts/partials/head.html` 中添加：

```html
{{ partial "plausible-analytics.html" . }}
```

#### 步骤 4：部署验证

```bash
git add .
git commit -m "添加 Plausible Analytics"
git push
```

---

## 💰 第二部分：添加广告联盟

### 方案一：Google AdSense（推荐）

#### 前提条件

- ✅ 网站有一定内容（建议 20+ 篇原创）
- ✅ 网站有一定流量（日均 100+ PV）
- ✅ 网站结构清晰，导航完整
- ✅ 有隐私政策页面（GDPR 要求）

#### 步骤 1：注册 AdSense

1. 访问：https://www.google.com/adsense/
2. 点击"开始使用"
3. 使用 Google 账号登录
4. 填写网站信息：
   - **网站地址**：https://blog.caowo.de/
   - **语言**：中文
   - **国家/地区**：中国
5. 阅读并同意条款

#### 步骤 2：添加验证代码

提交后，您会获得验证代码：

```html
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-xxxxxxxxxxxxxxxx"
     crossorigin="anonymous"></script>
```

**在 Hugo 中添加**：

创建 `layouts/partials/adsense.html`：

```html
<!-- Google AdSense -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-xxxxxxxxxxxxxxxx"
     crossorigin="anonymous"></script>
```

在 `layouts/partials/head.html` 中添加：

```html
{{ partial "adsense.html" . }}
```

#### 步骤 3：等待审核

- **审核时间**：通常 1-2 周
- **审核期间**：正常更新内容，保持活跃
- **审核结果**：邮件通知

#### 步骤 4：添加广告单元

审核通过后：

1. 登录 AdSense 后台
2. 点击"广告" → "按广告单元"
3. 选择广告类型：
   - **展示广告**：横幅广告
   - **信息流广告**：内容推荐
   - **原生广告**：与内容融合
4. 复制广告代码

**在 Hugo 中添加广告位**：

创建 `layouts/partials/ads-sidebar.html`（侧边栏广告）：

```html
<!-- 侧边栏广告 -->
<div class="ads-sidebar">
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-client="ca-pub-xxxxxxxxxxxxxxxx"
       data-ad-slot="1234567890"
       data-ad-format="auto"
       data-full-width-responsive="true"></ins>
  <script>
       (adsbygoogle = window.adsbygoogle || []).push({});
  </script>
</div>
```

在 `layouts/_default/single.html` 中调用：

```html
{{ partial "ads-sidebar.html" . }}
```

#### 步骤 5：设置收款

1. 进入 AdSense 后台 → "付款"
2. 添加收款账户（支持国内银行）
3. 填写税务信息
4. 设置付款阈值（默认 100 美元）

---

### 方案二：百度联盟（需要 ICP 备案）

#### 前提条件

- ❌ **必须有 ICP 备案**
- ✅ 网站内容健康
- ✅ 有一定流量

#### 步骤 1：注册百度联盟

1. 访问：https://union.baidu.com/
2. 注册账号
3. 添加网站（需要备案号）
4. 等待审核

#### 步骤 2：添加广告代码

审核通过后：

1. 登录百度联盟后台
2. 选择"推广管理" → "代码管理"
3. 选择广告类型
4. 复制代码

**在 Hugo 中添加**：

```html
<!-- 百度联盟广告 -->
<script>
var cpro_id = "uxxxxxxx";
</script>
<script src="https://cpro.baidustatic.com/cpro/ui/c.js"></script>
```

---

### 方案三：Buy Me a Coffee（推荐新手）

**优势**：
- ✅ 无需审核，立即可用
- ✅ 读者自愿打赏
- ✅ 支持多种支付方式
- ✅ 界面美观

#### 步骤 1：注册

1. 访问：https://www.buymeacoffee.com/
2. 使用账号注册
3. 设置个人资料
4. 绑定收款账户（PayPal/Payoneer）

#### 步骤 2：获取嵌入代码

在后台找到"Embed Widget"，复制代码：

```html
<script type="text/javascript" src="https://cdnjs.buymeacoffee.com/1.0.0/button.prod.min.js" data-name="bmc-button" data-slug="yourusername" data-color="#FFDD00" data-emoji=""  data-font="Cookie" data-text="Buy me a coffee" data-outline-color="#000000" data-font-color="#000000" data-coffee-color="#ffffff" ></script>
```

#### 步骤 3：在 Hugo 中添加

创建 `layouts/partials/buymeacoffee.html`：

```html
<!-- Buy Me a Coffee -->
<script type="text/javascript" src="https://cdnjs.buymeacoffee.com/1.0.0/button.prod.min.js" 
  data-name="bmc-button" 
  data-slug="yourusername" 
  data-color="#FFDD00" 
  data-emoji="" 
  data-font="Cookie" 
  data-text="Buy me a coffee" 
  data-outline-color="#000000" 
  data-font-color="#000000" 
  data-coffee-color="#ffffff" ></script>
```

在文章底部或侧边栏添加：

```html
{{ partial "buymeacoffee.html" . }}
```

---

### 方案四：微信/支付宝赞赏码（最简单）

#### 步骤 1：生成收款码

**微信**：
1. 打开微信 → 我 → 服务 → 收付款
2. 点击"二维码收款"
3. 保存图片

**支付宝**：
1. 打开支付宝 → 收付款
2. 点击"二维码收款"
3. 保存图片

#### 步骤 2：在 Hugo 中添加

创建 `layouts/partials/donate.html`：

```html
<!-- 赞赏支持 -->
<div class="donate-box">
  <h4>写教程不易，如果对您有帮助，可以赞赏一下吗？❤️</h4>
  <div class="qr-codes">
    <div class="qr-code">
      <img src="/images/wechat-pay.png" alt="微信赞赏">
      <p>微信</p>
    </div>
    <div class="qr-code">
      <img src="/images/alipay.png" alt="支付宝赞赏">
      <p>支付宝</p>
    </div>
  </div>
</div>

<style>
.donate-box {
  margin: 40px 0;
  padding: 20px;
  border: 2px dashed #ff6b6b;
  border-radius: 10px;
  background: #fff5f5;
  text-align: center;
}

.donate-box h4 {
  color: #ff6b6b;
  margin-bottom: 20px;
}

.qr-codes {
  display: flex;
  justify-content: center;
  gap: 30px;
}

.qr-code {
  text-align: center;
}

.qr-code img {
  width: 200px;
  height: 200px;
  border: 1px solid #ddd;
  border-radius: 5px;
}

.qr-code p {
  margin-top: 10px;
  font-weight: bold;
}
</style>
```

在文章底部添加：

```html
{{ partial "donate.html" . }}
```

---

## 🎯 第三部分：最佳实践建议

### 访问统计选择

| 需求 | 推荐方案 |
|------|----------|
| 海外流量为主 | Google Analytics 4 |
| 国内流量为主 | 百度统计 |
| 注重隐私 | Plausible Analytics |
| 简单轻量 | Umami（自托管） |

### 广告联盟选择

| 阶段 | 推荐方案 |
|------|----------|
| 新手起步 | Buy Me a Coffee + 赞赏码 |
| 有一定流量 | Google AdSense |
| 国内备案网站 | 百度联盟 + AdSense |
| 高流量网站 | 多个广告联盟组合 |

### 注意事项

1. **不要过度广告**：影响用户体验
2. **遵守 GDPR**：添加 Cookie 同意提示
3. **隐私政策**：说明数据收集方式
4. **广告位置**：侧边栏、文章底部最佳
5. **移动端优化**：确保广告在手机上正常显示

---

## 📋 完整配置示例

### config.toml 配置

```toml
# Google Analytics
googleAnalytics = "G-XXXXXXXXXX"

# 自定义参数
[params]
  # 统计
  baiduAnalytics = "xxxxxxxxxxxxxxxx"
  plausibleDomain = "blog.caowo.de"
  
  # 广告
  adsenseClient = "ca-pub-xxxxxxxxxxxxxxxx"
  buymeacoffeeSlug = "yourusername"
  
  # 赞赏功能
  enableDonate = true
  wechatPay = "/images/wechat-pay.png"
  alipay = "/images/alipay.png"
```

### 文章模板中添加

在 `layouts/_default/single.html` 的文章内容后添加：

```html
<article>
  {{ .Content }}
  
  <!-- 文章底部 -->
  <footer>
    <!-- 赞赏框 -->
    {{ if .Site.Params.enableDonate }}
      {{ partial "donate.html" . }}
    {{ end }}
    
    <!-- AdSense -->
    {{ if .Site.Params.adsenseClient }}
      {{ partial "adsense.html" . }}
    {{