# AdSense 广告部署指南

## 📋 已配置网站

### 1. blog.caowo.de ✅
- **状态**: 已部署
- **AdSense 客户 ID**: ca-pub-2336550233412374
- **部署方式**: GitHub + Cloudflare Pages
- **广告位置**: 每篇文章底部

### 2. blog.wizawn.com ✅
- **状态**: 已配置（与 blog.caowo.de 共享代码）
- **AdSense 客户 ID**: ca-pub-2336550233412374
- **部署方式**: GitHub + Cloudflare Pages

---

## 🖥️ 需要手动添加的网站

### 3. www.caowo.de（宝塔面板）
**服务器**: 154.201.78.213

**部署步骤**:

1. **登录宝塔面板**
   - 地址：http://154.201.78.213:8888
   - 用户名/密码：查看之前保存的记忆

2. **添加 AdSense 代码到网站**
   - 进入"网站" → 找到 www.caowo.de
   - 点击"设置" → "配置文件"
   - 在 `</head>` 标签前添加：

```html
<!-- Google AdSense -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2336550233412374"
     crossorigin="anonymous"></script>
```

3. **添加广告位到页面底部**
   - 编辑网站模板文件（通常是 footer.php 或 footer.html）
   - 在 `</body>` 标签前添加：

```html
<!-- AdSense 广告位 -->
<div style="margin: 30px 0; padding: 20px; text-align: center; background: #f9f9f9; border-radius: 10px;">
  <p style="margin-bottom: 15px; color: #666; font-size: 0.9em;">📢 广告</p>
  <ins class="adsbygoogle"
       style="display:block; min-height: 250px;"
       data-ad-client="ca-pub-2336550233412374"
       data-ad-slot="1234567890"
       data-ad-format="auto"
       data-full-width-responsive="true"></ins>
  <script>
       (adsbygoogle = window.adsbygoogle || []).push({});
  </script>
</div>
```

4. **保存并测试**
   - 保存配置文件
   - 访问网站查看源代码，确认代码已加载

---

### 4. www.wizawn.com（宝塔面板）
**服务器**: 154.201.78.213

**部署步骤**: 同上，重复上述步骤即可。

---

## 📊 验证方法

### 1. 检查代码是否加载
访问网站后，右键 → 查看源代码，搜索：
- `ca-pub-2336550233412374`
- `adsbygoogle`
- `pagead2.googlesyndication.com`

### 2. AdSense 后台验证
1. 登录：https://www.google.com/adsense/
2. 进入"网站" → "按网站查看"
3. 确认网站状态为"已就绪"

### 3. 查看广告展示
- 登录 AdSense 后台
- 进入"报告"
- 查看广告展示次数、点击率等数据

---

## ⚠️ 注意事项

1. **广告位 ID**
   - 当前使用的是通用广告位：`1234567890`
   - 建议在 AdSense 后台创建专用广告位后替换

2. **广告显示延迟**
   - 新网站可能需要几天才能显示广告
   - 确保网站内容符合 AdSense 政策

3. **robots.txt**
   - 确保不要屏蔽 Google 爬虫
   - 检查：https://www.caowo.de/robots.txt

4. **网站验证**
   - 可能需要在 AdSense 后台验证网站所有权
   - 使用已上传的验证文件：`/google8e5a0b4c9d1f2a3b.html`

---

## 📝 创建专用广告位（推荐）

1. 登录 AdSense 后台
2. 点击"广告" → "按广告单元"
3. 点击"+ 新广告单元"
4. 选择广告类型：
   - 名称：博客文章底部广告
   - 类型：展示广告
   - 尺寸：响应式
5. 创建后复制广告代码
6. 替换 `data-ad-slot="1234567890"` 中的数字

---

*最后更新：2026-03-26*
