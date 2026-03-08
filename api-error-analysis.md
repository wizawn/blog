# 阿里云百炼生图 API 400 错误分析

## 错误信息

```json
{
  "request_id": "e4a8bc9d-e4ef-4a15-afe0-c7051687ed39",
  "code": "InvalidParameter",
  "message": "url error, please check url！"
}
```

## 根本原因

**错误的 API 端点 URL**

### ❌ 错误的 URL
```
https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation
```

### ✅ 正确的 URL
```
https://dashscope.aliyuncs.com/api/v1/services/aigc/text-to-image/generation
```

## 其他可能的问题

1. **模型名称不正确**
   - 正确：`wanx2.1-t2i-turbo`
   - 错误：`wanx-v1`, `wanx2.0-t2i`

2. **请求格式问题**
   - 需要同步请求时添加：`X-DashScope-Async: disable`
   - 图片生成使用 `text-to-image` 端点，不是 `multimodal-generation`

3. **API Key 权限**
   - 确保 API Key 有万相（Wanx）服务权限
   - 检查账户余额/免费额度

## 正确的请求示例

```python
import requests

API_KEY = "sk-xxx"
API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-to-image/generation"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "X-DashScope-Async": "disable"
}

payload = {
    "model": "wanx2.1-t2i-turbo",
    "input": {
        "prompt": "你的提示词"
    },
    "parameters": {
        "size": "1024x1024",
        "n": 1
    }
}

response = requests.post(API_URL, headers=headers, json=payload)
```

## 参考文档

- [阿里云万相 API 文档](https://help.aliyun.com/zh/model-studio/developer-reference/quick-start)
- [错误码说明](https://help.aliyun.com/zh/model-studio/error-code#error-url)

---
*分析时间：2026-03-01 01:40 UTC*
