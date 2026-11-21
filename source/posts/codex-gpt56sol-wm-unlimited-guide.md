---
title: "把 Codex 缓存里隐藏的 gpt-5.6-sol-wm 翻出来用：配置步骤与额度真相"
date: 2026-08-15T10:00:00Z
draft: false
categories: ["AI 工具", "技术教程"]
tags: ["ChatGPT", "Codex", "GPT-5.6-Sol", "隐藏模型"]
description: "在本地 Codex 的 models_cache.json 里翻出默认隐藏的 gpt-5.6-sol-wm 条目，通过自定义模型目录解锁给付费订阅账号使用，顺手把 API 按量账单和订阅限流窗口两套额度的误区说清楚。"
weight: 10
---

2026 年 8 月 14 日翻本机 Codex 目录的时候，我在客户端自动拉下来的 `models_cache.json` 里撞见了一个界面菜单上压根找不到的模型条目：`gpt-5.6-sol-wm`。它的 `visibility` 默认写着 `hide`，`supported_in_api` 设成了 `false`。拿手头的付费号折腾测试了两天，发现只要在本地导出自定义模型目录把它改成可见，远端服务器居然直接放行。

在动手改配置之前，得先把外面传得最邪乎的一个误会摁死：这玩意儿既不"无限"，也跟"零消耗白嫖"半毛钱关系没有。

外面有人传出"用它不扣钱"的错觉，纯粹是把两本完全不相干的账混到一块儿去了。第一本账是 `platform.openai.com` 上的 API 按量美元余额：`gpt-5.6-sol-wm` 标着 `supported_in_api: false`，本来就不是公开 API 模型，自然不会进 Platform 的消费明细。但话说回来，只要你是拿 ChatGPT 订阅登录的 Codex，所有模型走的全是订阅授权，本来哪一个都不会去扣你 API 账户里的美金，这根本算不上 `wm` 的什么独门特权。第二本账是 ChatGPT / Codex 订阅自带的 5 小时与每周限流窗口：调 `gpt-5.6-sol-wm` 跟调普通 Sol 一样实打实往窗口里记账，刷猛了照样弹 `usage_limit_reached`。

说白了，它的实际价值就是在不额外花 API 美元的前提下，让你在付费订阅额度内多一个主观输出体感接近 Sol 的内部路由分支可选。

## 0x00 本地改可见性与服务端验权限是两码事

翻开 `models_cache.json` 搜 `gpt-5.6-sol-wm`（一般在文件第 90 多行附近，往下隔三十来行能看到它的可见性开关），能看到 OpenAI 服务器主动推下来的原始字段：

| 字段 | 缓存原始值 | 实际作用 |
|---|---|---|
| `slug` | `gpt-5.6-sol-wm` | 请求时传给后端的模型内部标识 |
| `visibility` | `hide` | 控制客户端模型下拉菜单里展不展示它 |
| `supported_in_api` | `false` | 标记它不开放给公开 Platform API |

这里得拎清楚两层完全独立的逻辑：把本地目录里的 `visibility` 从 `hide` 改成 `list`，仅仅是哄着客户端界面把它画进下拉框里；你的账号到底能不能调通，裁判权百分之百在 OpenAI 服务器手里。

我在两台机器上分别换不同档位的账号跑了一轮探针验证。主力机上的 Plus 和 Pro 付费号发请求过去直接吐回 `WM_OK`；另一台单独指定了自定义 `CODEX_HOME` 测试目录的机器切到 Free 免费号，哪怕本地 `models_cache.json` 里照样躺着一模一样的 `gpt-5.6-sol-wm` 条目，请求打过去还是被服务端干脆利落地拒了，直接回 `model is not supported`，切回付费号立刻恢复放行。至于 Business（原 Team）或 Edu 这类付费席位，手头没逐一测过，跑一把后面的最小探针就能当场验出来。

## 0x01 导出独立目录副本，千万别直接改原缓存

别图省事直接拿编辑器去改 `models_cache.json` 本尊，Codex 运行时隔三差五会自动刷新覆盖那个缓存文件，你刚改完重启两次又变回 `hide` 了。稳妥的路子是先把原文件备份好，再复制一份叫 `models_wm_visible.json` 的独立副本，只改副本里 `gpt-5.6-sol-wm` 这一项的 `visibility`，最后在 `config.toml` 里用 `model_catalog_json` 指过去。

动手前先把 Codex 桌面端彻底退干净，Windows 记得看一眼右下角系统托盘图标，macOS 看顶部菜单栏图标，别留后台常驻进程。

如果你在 Windows 上操作（推荐装 PowerShell 7 即 `pwsh`），先确认一下自己的 `CODEX_HOME` 落在哪（顺手看一眼是不是软链接目录），并带上 `-Context 0,40` 把 `slug` 底下隔着三十来行的 `visibility` 一块儿打印出来核对：

```powershell
$CodexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
Get-Item -LiteralPath $CodexRoot | Format-List FullName,LinkType,Target

$CachePath = Join-Path $CodexRoot 'models_cache.json'
Select-String -LiteralPath $CachePath -SimpleMatch '"slug": "gpt-5.6-sol-wm"' -Context 0,40
```

要是提示连 `models_cache.json` 都没找着，先正常打开 Codex 跑一次对话让它拉取缓存再回来查。确认条目存在之后，跑下面这段脚本生成 `models_wm_visible.json`。因为模型对象的 `slug` 与 `visibility` 中间还夹着 `supported_reasoning_levels` 嵌套子对象，这里特意用负向先行断言 `(?:(?!"slug"\s*:).)*?` 把匹配范围死死卡在当前模型条目之内（绝不越过下一个模型的 `slug`），而且把结果存进 `$Found`（避开 PowerShell 自带的自动变量 `$Matches`），防止跨对象把底下别的隐藏模型给误改了：

```powershell
$CodexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$CachePath = Join-Path $CodexRoot 'models_cache.json'
$VisibleCatalog = Join-Path $CodexRoot 'models_wm_visible.json'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$CacheBackup = Join-Path $CodexRoot "models_cache.before-wm-$Stamp.bak"

if (-not (Test-Path -LiteralPath $CachePath)) {
    throw "找不到模型缓存：$CachePath"
}

Copy-Item -LiteralPath $CachePath -Destination $CacheBackup
if (Test-Path -LiteralPath $VisibleCatalog) {
    Copy-Item -LiteralPath $VisibleCatalog -Destination "$VisibleCatalog.before-$Stamp.bak"
}
Copy-Item -LiteralPath $CachePath -Destination $VisibleCatalog -Force

$Raw = [IO.File]::ReadAllText($VisibleCatalog)
$Pattern = '(?s)("slug"\s*:\s*"gpt-5\.6-sol-wm"(?:(?!"slug"\s*:).)*?"visibility"\s*:\s*)"hide"'
$Found = [regex]::Matches($Raw, $Pattern)

if ($Found.Count -ne 1) {
    throw "预期精确匹配 1 处隐藏的 gpt-5.6-sol-wm，实际找到 $($Found.Count) 处，已中止。"
}

$Regex = [regex]::new($Pattern)
$Updated = $Regex.Replace(
    $Raw,
    [Text.RegularExpressions.MatchEvaluator]{ param($m) $m.Groups[1].Value + '"list"' },
    1
)

[IO.File]::WriteAllText($VisibleCatalog, $Updated, [Text.UTF8Encoding]::new($false))
Write-Host "已生成：$VisibleCatalog （原始缓存备份在 $CacheBackup）"
```

跑完顺手验一下生成的 JSON，确认只有 `gpt-5.6-sol-wm` 变成了 `list`，而目录里另一个给内部代码审查用的隐藏模型 `codex-auto-review` 依然老老实实保持 `hide`（这里没加 `-Depth 100`，免得在 Windows 默认自带的旧版 PowerShell 5.1 下报参数不存在；如果你用的是 `pwsh` 7 加上也无妨）：

```powershell
$Catalog = Get-Content -Raw -LiteralPath $VisibleCatalog | ConvertFrom-Json
$WM = @($Catalog.models | Where-Object slug -eq 'gpt-5.6-sol-wm')
$Auto = @($Catalog.models | Where-Object slug -eq 'codex-auto-review')

[pscustomobject]@{
    WMCount        = $WM.Count
    WMVisibility   = $WM[0].visibility
    AutoCount      = $Auto.Count
    AutoVisibility = $Auto[0].visibility
}
```

要是你在 macOS 或 Linux 下折腾，终端里拿 `jq` 两行命令就能干完同样的活：

```bash
CODEX_ROOT="${CODEX_HOME:-$HOME/.codex}"
STAMP="$(date +%Y%m%d-%H%M%S)"

cp "$CODEX_ROOT/models_cache.json" "$CODEX_ROOT/models_cache.before-wm-$STAMP.bak"
jq '(.models[] | select(.slug == "gpt-5.6-sol-wm") | .visibility) = "list"' \
  "$CODEX_ROOT/models_cache.json" > "$CODEX_ROOT/models_wm_visible.json"

jq -r '.models[] | select(.slug == "gpt-5.6-sol-wm" or .slug == "codex-auto-review") | "\(.slug): \(.visibility)"' \
  "$CODEX_ROOT/models_wm_visible.json"
```

## 0x02 写进 `config.toml` 并跑一条只读探针

改配置文件前同样先敲一行 `cp "$CODEX_ROOT/config.toml" "$CODEX_ROOT/config.toml.before-wm.bak"`（PowerShell 用 `Copy-Item`）留一份备份，然后打开 `$CODEX_HOME/config.toml`，在最外层顶层区域（千万别塞进底下某个 `[features]` 或 `[model_providers]` 表头里面）加上这三行：

```toml
model = "gpt-5.6-sol-wm"
# Windows 路径同样建议用正斜杠，如 "C:/Users/<你的用户名>/.codex/models_wm_visible.json"
# macOS 填 "/Users/<你的用户名>/.codex/models_wm_visible.json"
model_catalog_json = "/Users/<你的用户名>/.codex/models_wm_visible.json"
model_reasoning_effort = "high"
```

`supported_in_api` 那个字段不用去动它，不影响订阅通道调用。至于 `model_reasoning_effort`，配置规范里支持 `low`、`medium`、`high`、`xhigh`、`max` 乃至 `ultra`（取决于具体模型放开的档位）。平时写业务代码设成 `high` 其实最划算；硬拉到 `max` 或 `ultra` 虽然思考最深，但响应最慢，吃 5 小时和每周订阅配额的速度也最凶。同理，如果你追求响应速度额外加了 Fast 优先队列开关（注意 `service_tier` 同样必须放在顶层；如果原文件里已经有 `[features]` 表头，直接把 `fast_mode = true` 填进原表底下，别重复写两个 `[features]` 引发 TOML 解析报错）：

```toml
service_tier = "fast"

[features]
fast_mode = true
```

速度确实能快一截，但配额消耗倍率也会跟着往上翻，按自己手头账号的窗口余量酌情开就行。

保存之后重新打开 Codex，新建任务点开模型选择器就能看到 `GPT-5.6-Sol-WM` 了；万一列表没刷出来，在终端敲一下实验性的 `codex debug models` 查一眼当前生效的模型表。平时懒得改模型选择器的话，直接在命令行敲 `codex --model gpt-5.6-sol-wm`（或者带上 `-c 'service_tier="fast"'`，Windows 下建议用 `pwsh` 7.3+ 免得旧版把原生命令参数里的内嵌双引号剥掉）也能直接拉起会话。

想单独确认远端服务器到底认不认你当前登录的账号，可以跑下面这条加了 `--ignore-user-config` 的最小只读探针（注意因为它跳过了用户配置，测的是纯服务端对这个模型名的授权，不依赖刚才写的 `config.toml`）：

```bash
# macOS / Linux 示例（Windows PowerShell 把 ${TMPDIR:-/tmp} 换成 $env:TEMP，行尾反斜杠换成反引号 `）
codex --ask-for-approval never exec \
  --ignore-user-config \
  --ephemeral \
  --json \
  --skip-git-repo-check \
  -C "${TMPDIR:-/tmp}" \
  --sandbox read-only \
  --model gpt-5.6-sol-wm \
  -c 'model_reasoning_effort="low"' \
  -c 'web_search="disabled"' \
  -c 'features.shell_tool=false' \
  -c 'features.multi_agent=false' \
  -c 'project_doc_max_bytes=0' \
  'Reply exactly WM_OK. Do not call any tool.'
```

退出码为 `0` 且吐出 `WM_OK` 就说明服务端认账；吐 `model is not supported` 多半是当前登错成了 Free 账号；报 `401` 就重新 `codex login` 刷一下登录态；要是撞上限流报错，等窗口重置后再测。

## 0x03 升级重刷、回滚与边界提醒

后面每次升级 Codex 客户端版本之后，`models_cache.json` 的字段结构可能会跟着变，记得拿新版缓存重新跑一遍脚本生成 `models_wm_visible.json`，别一直抱着旧版 JSON 不撒手。另外切记别去拷别人的 `auth.json` 或 token 来蹭模型，调用权限跟服务端账号订阅死死绑在一起，乱导认证文件除了招风控和盗号风险百害无一利。

虽然这通操作只是在本地把服务端自己下发的隐藏条目改成了可见、没伪造任何协议包，但毕竟调的是未公开的内部模型路由，上游哪天一声不吭把它撤掉或者在服务条款层面收紧限制都不稀奇，平时拿来写写代码尝鲜挺好，别把关键自动化流水线死绑在它身上。

哪天不想用了或者路由下线了，回滚只要一分钟：彻底退出 Codex，直接把之前留好的 `config.toml.before-wm.bak` 覆盖回 `config.toml`（或者手动把 `0x02` 里添进去的 `model`、`model_catalog_json`、`model_reasoning_effort` 以及可选的 `service_tier` / `fast_mode` 全删干净），重启客户端就跟没改过一样了。

---

顺手安利一下朋友维护的开源项目 [RikkaHub Agent](https://github.com/AAAelina/rikkahub-agent)，平时喜欢折腾本地 Agent 工具链的可以去逛逛。
