# 阿里云百炼万相生图 API 测试报告

## 测试时间
2026-03-01 01:56 UTC

## 测试状态
❌ **失败** - API 返回 400 错误

---

## 测试详情

### 测试 1: 同步请求
**端点:** `POST https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation`
**模型:** `wanx-v1`
**状态码:** 400
**错误:**
```json
{
  "request_id": "af0ddb11-5b6e-40b4-a2a7-ea4166caec31",
  "code": "InvalidParameter",
  "message": "url error, please check url！"
}
```

### 测试 2: 异步请求
**Headers:** `X-DashScope-Async: enable`
**结果:** 同样返回 400 错误

### 测试 3: API Key 权限检查
**通义千问文本模型:** ✅ 可用 (状态码 200)
**万相生图模型:** ❌ 不可用 (状态码 400)

---

## 问题分析

### ✅ 确认有效
- API Key 格式正确
- API Key 对文本模型有效
- 网络连接正常
- 请求格式符合文档

### ❌ 问题所在
- 万相生图服务返回"url error"
- 该错误通常表示 API 端点不正确或服务未开通

---

## 可能原因

1. **API Key 没有万相服务权限**
   - API Key 可能只开通了文本模型权限
   - 需要在阿里云控制台开通万相服务

2. **万相服务未开通**
   - 登录阿里云百炼控制台
   - 开通"通义万相"服务
   - 确认有免费额度或账户余额

3. **API 端点已变更**
   - 阿里云可能更新了 API 端点
   - 需要查看最新官方文档

4. **区域限制**
   - 某些服务可能仅限特定区域使用

---

## 解决方案

### 方案 1: 检查阿里云控制台

1. 登录 https://dashscope.console.aliyun.com/
2. 检查"通义万相"服务状态
3. 确认服务已开通
4. 检查免费额度/账户余额

### 方案 2: 查看最新 API 文档

访问：https://help.aliyun.com/zh/model-studio/developer-reference/

查找最新的万相生图 API 文档，确认：
- 正确的 API 端点
- 正确的模型名称
- 正确的请求格式

### 方案 3: 使用替代方案

**Unsplash（免费，已配置）:**
- 无需 API Key
- 高质量专业图片
- 直接嵌入博客

**Pexels（免费）:**
- 网站：https://www.pexels.com/
- API 文档：https://www.pexels.com/api/

---

## 当前建议

**暂时使用 Unsplash 免费图片源**，原因：
1. ✅ 无需 API Key
2. ✅ 高质量图片
3. ✅ 已配置到 4 篇教程
4. ✅ 加载速度快

等阿里云万相服务确认开通后，再切换回阿里云 API。

---

## 联系支持

如果确认已开通服务但仍无法使用，联系阿里云支持：
- 工单：https://workorder.console.aliyun.com/
- 文档：https://help.aliyun.com/

---

*报告生成时间：2026-03-01 01:56 UTC*
