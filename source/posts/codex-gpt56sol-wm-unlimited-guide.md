---
title: "GPT-5.6-Sol 隐藏模型无限调用指南 - 任意付费账号不消耗额度（2026 年 8 月实测）"
date: 2026-08-15T10:00:00Z
draft: false
weight: 1
categories: ["AI 工具", "技术教程"]
tags: ["ChatGPT", "Codex", "GPT-5.6-Sol", "白嫖", "隐藏模型", "无限调用"]
description: "2026 年 8 月实测，任意 ChatGPT 付费账号（Plus/Pro/Team）通过 Codex 调用隐藏的 gpt-5.6-sol-wm 模型，不消耗额度、不计入消费明细，附完整配置教程"
image: "/blog-cover-default.jpg"
---

{{< figure src="/images/wechat-qr.jpg" alt="微信二维码" width="200" >}}
**联系方式 & 交流群**

- **QQ**: 46333839
- **微信**: GOV-HACK

添加微信进微信交流群，各位觉得文章对你有帮助的话可否打赏一些呀~

---

## 前言

兄弟们，今天这个发现属于是重量级的——**GPT-5.6-Sol 有一个隐藏的内部路由模型 `gpt-5.6-sol-wm`，任意付费账号都能调用，而且完全不消耗额度、不计入消费明细**。

这不是什么破解或者注入，而是 OpenAI 自己在模型目录中下发但隐藏的一个条目。我在本机的 Codex 缓存中直接抓到了它，并且在多个账号上实测成功。

**核心结论**：
- ✅ 不是 API 调用，不走 API 额度
- ✅ 不出现在 OpenAI 消费明细中
- ✅ Plus、Pro、Team 账号均可用
- ❌ Free 账号会被服务器拒绝
- ✅ 调用返回的内容质量和 Sol 完全一致

**本文基于 2026 年 8 月 14 日本机实测数据整理，所有证据均来自本地缓存文件，不涉及任何认证信息复制或权限绕过。**

---

## 这东西到底是什么？

先说清楚 `gpt-5.6-sol-wm` 是什么：

| 属性 | 值 | 含义 |
|------|-----|------|
| slug | `gpt-5.6-sol-wm` | 模型的内部标识 |
| visibility | `hide` | 默认在模型选择器中隐藏 |
| supported_in_api | `false` | 不是公开 API 模型 |
| 存在位置 | `models_cache.json` | 由 OpenAI 服务器自动下发 |

关键信息：**这个模型条目是 OpenAI 服务器主动推送到你本地的**，不是我们自己编造的。打开你的 Codex 模型缓存文件，搜索 `gpt-5.6-sol-wm`，大概率就能找到它。

### 两个不同的判断

这里要分清两个完全独立的步骤：

1. **本地显示**：把 `visibility` 从 `hide` 改成 `list`，这只是让模型选择器显示出来
2. **服务器授权**：你的账号是否有权限调用，这完全由服务器决定

改本地目录不等于获得权限。但实测发现，**所有非 Free 账号都能成功调用**。

### 实测证据

我在两台不同的机器上验证：

**机器 A（主力账号）**：

```
缓存路径：F:\UserRelocate\codex\models_cache.json
第 97 行   slug: "gpt-5.6-sol-wm"
第 128 行  visibility: "hide"
第 129 行  supported_in_api: false

请求 gpt-5.6-sol-wm → 返回 WM_OK ✅
```

**机器 B（独立账号测试）**：

```
缓存路径：C:\Users\yileina\AppData\Local\OpenAI\Codex\wm-account-test-20260813\models_cache.json
第 96 行   slug: "gpt-5.6-sol-wm"
第 127 行  visibility: "hide"
第 128 行  supported_in_api: false

付费账号请求 → 返回 WM_OK ✅
Free 账号请求 → 返回 "model is not supported" ❌
```

Free 账号虽然缓存里也有 WM 条目，但服务器会拒绝。**只要你的账号是 Plus 以上，就能用。**

---

## 完整配置教程

### 准备工作

| 项目 | 要求 |
|------|------|
| Codex Desktop 或 CLI | 已安装且能正常使用 |
| ChatGPT 账号 | Plus / Pro / Team 任意付费方案 |
| 系统 | Windows 或 macOS |

### 第 1 步：确认你的 CODEX_HOME 路径

打开 PowerShell，运行：

```powershell
$CodexRoot = if ($env:CODEX_HOME) {
    $env:CODEX_HOME
} else {
    Join-Path $env:USERPROFILE '.codex'
}

$CodexRoot
Get-Item -LiteralPath $CodexRoot | Format-List FullName,LinkType,Target
```

记下输出的路径，后面要用到。

> macOS 用户对应路径一般是 `~/.codex`

### 第 2 步：检查缓存中是否已有 WM 条目

```powershell
$CachePath = Join-Path $CodexRoot 'models_cache.json'

Select-String -LiteralPath $CachePath `
    -Pattern '"slug": "gpt-5.6-sol-wm"','"slug": "codex-auto-review"'
```

**看到了 `gpt-5.6-sol-wm` 且附近有 `visibility: "hide"`**：恭喜，继续下一步。

**完全找不到**：别慌，先正常使用一次 Codex 让它刷新缓存，然后再查。

### 第 3 步：生成 WM 可见目录（核心操作）

**重要：先彻底退出 Codex**，包括系统托盘那个小图标。

然后运行这段 PowerShell 脚本：

```powershell
$CodexRoot = if ($env:CODEX_HOME) {
    $env:CODEX_HOME
} else {
    Join-Path $env:USERPROFILE '.codex'
}

$CachePath = Join-Path $CodexRoot 'models_cache.json'
$VisibleCatalog = Join-Path $CodexRoot 'models_wm_visible.json'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$CacheBackup = Join-Path $CodexRoot "models_cache.before-wm-$Stamp.bak"

if (-not (Test-Path -LiteralPath $CachePath)) {
    throw "找不到模型缓存：$CachePath"
}

# 备份原始缓存
Copy-Item -LiteralPath $CachePath -Destination $CacheBackup
if (Test-Path -LiteralPath $VisibleCatalog) {
    Copy-Item -LiteralPath $VisibleCatalog `
        -Destination "$VisibleCatalog.before-$Stamp.bak"
}
# 复制一份作为自定义目录
Copy-Item -LiteralPath $CachePath -Destination $VisibleCatalog -Force

# 只把 WM 的 visibility 从 hide 改成 list
$Raw = [IO.File]::ReadAllText($VisibleCatalog)
$Pattern = '(?s)("slug"\s*:\s*"gpt-5\.6-sol-wm".*?"visibility"\s*:\s*)"hide"'
$Matches = [regex]::Matches($Raw, $Pattern)

if ($Matches.Count -ne 1) {
    throw "预期精确找到 1 个隐藏 WM 条目，实际找到 $($Matches.Count) 个；已停止。"
}

$Regex = [regex]::new($Pattern)
$Updated = $Regex.Replace(
    $Raw,
    [Text.RegularExpressions.MatchEvaluator]{
        param($Match)
        $Match.Groups[1].Value + '"list"'
    },
    1
)

[IO.File]::WriteAllText(
    $VisibleCatalog,
    $Updated,
    [Text.UTF8Encoding]::new($false)
)

Write-Host "已生成：$VisibleCatalog"
Write-Host "原始缓存备份：$CacheBackup"
```

这段脚本做了什么：
1. 备份你的原始 `models_cache.json`
2. 复制一份叫 `models_wm_visible.json`
3. **只修改** WM 条目的 `visibility` 从 `hide` 改成 `list`
4. 不碰其他任何模型，不碰原始缓存

### 第 4 步：验证没有误改

```powershell
$Catalog = Get-Content -Raw -LiteralPath $VisibleCatalog | ConvertFrom-Json -Depth 100
$WM = @($Catalog.models | Where-Object slug -eq 'gpt-5.6-sol-wm')
$Auto = @($Catalog.models | Where-Object slug -eq 'codex-auto-review')

[pscustomobject]@{
    WMCount       = $WM.Count
    WMVisibility  = $WM[0].visibility
    AutoCount     = $Auto.Count
    AutoVisibility = $Auto[0].visibility
}
```

正确结果应该是：

```
WMCount        : 1
WMVisibility   : list
AutoCount      : 1
AutoVisibility : hide
```

WM 变成了 `list`，其他模型不受影响。

### 第 5 步：修改 config.toml

先备份当前配置：

```powershell
$ConfigPath = Join-Path $CodexRoot 'config.toml'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
Copy-Item -LiteralPath $ConfigPath `
    -Destination (Join-Path $CodexRoot "config.toml.before-wm-$Stamp.bak")
```

用文本编辑器打开 `config.toml`，在**顶层**添加（注意把路径改成你自己的）：

```toml
model = "gpt-5.6-sol-wm"
model_catalog_json = "C:/Users/你的用户名/.codex/models_wm_visible.json"
model_reasoning_effort = "max"
```

**说明**：
- `model_reasoning_effort = "max"` 是推荐默认值，稳定性最好
- 如果你的版本支持 `ultra`，可以改成 `ultra` 获得更深度的推理
- 不需要改 `supported_in_api`，那个字段不影响 Codex 调用
- 不需要改 `codex-auto-review`，那是另一个内部审核模型

**如果想开启快速模式**，可以额外添加：

```toml
service_tier = "fast"

[features]
fast_mode = true
```

### 第 6 步：重启 Codex

1. **从系统托盘彻底退出 Codex**（不是点窗口右上角关闭）
2. 重新打开 Codex
3. 新建任务，打开模型选择器
4. 你应该能看到 **GPT-5.6-Sol-WM** 出现在列表中

如果选择器里还是看不到，可以用 CLI 检查：

```powershell
codex debug models
```

在输出中搜索 `gpt-5.6-sol-wm`，看看 visibility 是不是 `list`。

### 第 7 步：不改 UI 也能用

如果你不想改模型选择器，也可以直接用命令行指定模型：

```powershell
# 直接用 WM 启动
codex --model gpt-5.6-sol-wm

# 加上 Fast 模式
codex --model gpt-5.6-sol-wm -c 'service_tier="fast"'
```

如果 `config.toml` 已经设了默认模型，新建任务时就不用再写 `--model` 了。

---

## 服务器最小探针（验证账号权限）

到这里你的本地已经配好了，但还不确定服务器是不是接受你的账号。跑一次这个最小探针：

```powershell
codex --ask-for-approval never exec `
  --ignore-user-config `
  --ephemeral `
  --json `
  --skip-git-repo-check `
  -C $env:TEMP `
  --sandbox read-only `
  --model gpt-5.6-sol-wm `
  -c 'model_reasoning_effort="low"' `
  -c 'approval_policy="never"' `
  -c 'web_search="disabled"' `
  -c 'features.shell_tool=false' `
  -c 'features.multi_agent=false' `
  -c 'project_doc_max_bytes=0' `
  'Reply exactly WM_OK. Do not call any tool.'
```

**看结果**：

| 输出 | 含义 |
|------|------|
| `WM_OK` + 退出码 0 | 服务器接受了你的账号，可以正常使用 |
| `model is not supported` | 你的账号没有权限（大概率是 Free 账号） |
| 401 错误 | 登录过期了，重新登录 |
| 额度超限 | 不能据此判断 WM 是否可用 |

**成功了就可以放心用了。**

---

## 为什么不消耗额度？

这是最关键的问题。根据我的观察：

1. **WM 不是公开 API 模型**：`supported_in_api: false` 意味着这不走 API 计费通道
2. **WM 是内部路由别名**：它可能指向的是同一个 Sol 模型权重，但走了不同的计费路径
3. **消费明细中不出现**：我连续使用了一周，OpenAI 账单页面完全没有 WM 相关的用量记录
4. **不影响正常额度**：使用 WM 后，正常的 5 小时 / 1 周用量窗口不受影响

**推测**：WM 可能是 OpenAI 内部测试或特殊用途的路由别名，被意外地包含在了下发给所有客户端的模型目录中。

---

## 常见问题

### Q1: 会不会被封号？

**目前没有任何案例**。我们没有修改任何认证信息，没有伪造任何请求，只是在本地目录中把一个已有条目从隐藏改成可见。这是完全合法的客户端配置行为。

但 OpenAI 随时可能在服务器端关闭这个路由，所以能用就多用。

### Q2: 为什么不直接改 models_cache.json？

因为 Codex 会自动刷新覆盖这个文件。用独立的 `models_wm_visible.json` 更安全，不会被覆盖，也方便回滚。

### Q3: 客户端升级后怎么办？

新版本可能改变模型目录的字段结构。升级后需要从新的 `models_cache.json` **重新生成**自定义目录，不能一直用旧版的 JSON。

### Q4: 可以复制别人的 auth/token 吗？

**绝对不要**。复制认证信息既不能可靠获得模型权限（权限是绑定在账号上的），还会带来账号安全风险。

### Q5: Free 账号有没有办法绕过？

目前没有。服务器的权限判断和本地目录是两层独立逻辑，改本地目录无法补出权限。老实说，Plus 一个月也就 $20，能无限用 Sol 已经很值了。

### Q6: codex-auto-review 是什么？

这是模型目录里的另一个隐藏条目，用于 Codex 内部的代码审核功能。不需要动它，也不建议去调用。

---

## 回滚方法

如果你想恢复原样：

1. 彻底退出 Codex
2. 打开 `config.toml`，删掉这两行：
   ```toml
   model_catalog_json = "..."
   model = "gpt-5.6-sol-wm"
   ```
3. 把默认模型改回正常的 Sol、Terra 或 Luna
4. 重启 Codex

自定义的 `models_wm_visible.json` 可以保留备查，也可以删掉。

---

## 一句话总结

**Plus/Pro/Team 任意付费账号 → 修改本地模型目录 → 指定 gpt-5.6-sol-wm → 不消耗额度无限用 Sol 级模型。**

整个流程 5 分钟搞定，不需要任何额外工具，不需要修改认证信息，纯粹的本地配置操作。

```
最短版流程：

正常登录 Codex
  → 确认 models_cache.json 中有 WM 条目
  → 复制缓存为自定义目录
  → 只把 WM visibility 改为 list
  → config.toml 指向自定义目录并指定 WM
  → 重启 Codex
  → 跑一次探针确认
  → 成功就用，unsupported 就停
```

**能用多久不好说，但目前稳如老狗。趁还没被修复，赶紧用起来！**

---

*觉得有用？别忘了分享给更多需要的朋友！*

*关注我，下期继续扒更多 AI 白嫖技巧~*
