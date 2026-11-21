---
title: "ACG-Faka 发卡站回调伪造复盘：从备份包与 BEpusdt Config.php 泄露到库存被搬空"
description: "复盘一起针对 ACG-Faka + BEpusdt 的真实盗卡事件：从 660 条访问日志还原攻击者如何放弃盲猜签名、转头读走 Config.php 明文密钥，最后每 6 秒伪造一条合法回调搬空库存；顺带记一笔五个同类站点的授权排查结果。"
date: 2026-08-13T23:00:00+08:00
draft: false
slug: acg-faka-bepusdt-callback-forgery-analysis
categories: ["漏洞分析"]
tags: ["支付安全", "Web 安全", "PHP", "回调伪造", "ACG-Faka", "BEpusdt"]
weight: 10
---

前阵子有个朋友用 ACG-Faka 搭的虚拟发卡站（收款接的 BEpusdt），一宿之间被人搬空了上百张卡密。

最邪门的地方在于：上服务器翻了一圈没见着半个 WebShell，数据库没被拖库，后台管理员账号也没有异地登录记录。对方全程就干了一件事，往公开暴露的支付回调接口发了一串带合法签名的"已付款" POST 请求，发卡程序乖乖把订单状态改成已支付，自动把卡密吐了个底朝天。

拿到他发过来的 Nginx 访问日志仔细捋了一遍，再对照当时 ACG-Faka 官方刚发的安全通告（严禁在网站根目录放整站或数据库备份包），整条链路其实半点不玄乎：签名算法本身没破，是算签名用的 `api_token` 从别的口子漏出去了。

## 0x00 660 条日志里的两小时空白，与 `33` 字节成功指纹

把受害站点的 Nginx `access.log` 拉出来按可疑 IP（`203.27.106.***`）筛了一下，一共 660 来条记录，整场动作的节奏特别清楚。

下午 `14:22`，对方先在摸路，拿 `/callback/BEpusdt` 和 `/user/api/order/callback.BEpusdt` 挨个试回调路由格式，看到从 `404` 变成 `200` 之后锁定了正确的插件入口。

到了 `14:50`，对方发了几条全零签名（`000...000`）过来试探验签逻辑。这时候看 Nginx 日志里的响应体字节数 `body_bytes_sent` 就能直接把结果看穿：返回 `35` 字节对应 `{"code":0,"msg":"handle not found"}`（插件名不对）；返回 `29` 字节对应 `{"code":0,"msg":"sign error"}`（签名没过被拦下）；一旦变成 `33` 字节的成功回执，说明验签已经放行，订单当场入账发货。

在 `14:50` 连吃几个 `29` 字节的 `sign error` 之后，这个 IP 突然安静了整整两个小时，压根没去傻乎乎地暴力撞哈希。等到 `17:01` 再露面的时候，他直接精准请求了 `/app/Pay/BEpusdt/Config/Config.php`，拿到了包含源码的 `200` 响应。半小时后的 `17:32`，日志里蹦出了第一条 `33` 字节的成功回调；`18:31` 之后彻底挂上了自动化脚本，卡着每 6 秒建一单、伪造一次回调的节奏，一路把库存扫空。

那两小时的空白期，人家根本没在死磕密码学，而是转头把签名密钥明文给读走了。

## 0x01 两条漏密钥的野路子：根目录备份包与 PHP 源码直出

在 ACG-Faka 里，一笔支付回调从进门到放货主要过三个文件：路由收到 `/user/api/order/callback.BEpusdt` 后调插件目录下的 `app/Pay/BEpusdt/Impl/Signature.php` 验签，密钥从同插件的 `app/Pay/BEpusdt/Config/Config.php` 里读，验过之后调 `app/Service/Bind/Order.php` 改订单状态并吐卡密。

BEpusdt 这套 USDT 收款网关的验签公式很直白：把除了 `signature` 本身之外的所有非空字段按字母排个序拼成 `k=v&...`，尾巴上直接拼上商户配的 `api_token`，整体算一把 MD5：

```python
params = {k: v for k, v in data.items() if v != "" and k != "signature"}
sorted_str = "&".join(f"{k}={params[k]}" for k in sorted(params.keys()))
signature = hashlib.md5((sorted_str + api_token).encode()).hexdigest()
```

只要 `api_token` 不为空也不外泄，外人靠 `curl` 是算不出合法签名的。可现实里不少站长自己把保险箱钥匙摆在了门口，一边是整站备份包裸奔，另一边就是这次日志里抓到的 `Config.php` 直读。

先说官方通告点名的备份包问题。很多用宝塔面板的站长图省事，点完一键备份或者导完库，随手就把 `backup.zip`、`www.zip`、`域名.sql` 留在网站根目录 `/www/wwwroot/faka/` 底下。Nginx 看见 `.zip` 和 `.sql` 默认当普通静态文件直出，扫描器挂个常见备份文件名字典撞中一次，全站源码连带 `config/database.php` 里的数据库密码、上游货源接口密钥和支付 `api_token` 直接一锅端，数据库导出文件里甚至躺着现成的卡密库存，连伪造回调那一步都省了。

再看这次日志里实锤的第二条路。`app/Pay/BEpusdt/Config/Config.php` 里就几行返回配置数组的 PHP 代码（`'api_token' => 'a1b2c3d4...'`）。按理说就算站长没给 `/app/` 目录配访问拦截，请求 `.php` 交给 PHP-FPM 执行完 `return [...]` 也只会吐出一个长度为 0 的空页面；偏偏有些站长自己改伪静态或者子目录规则的时候写歪了 `location ~ \.php$` 的匹配范围，导致深层路径 `/app/Pay/...` 底下的 `.php` 压根没进 PHP-FPM，直接被 Nginx 当纯文本把源码吐了出去，密钥当场裸奔。

## 0x02 插件代码与访问控制上的两处软肋

除了运维配错漏出密钥，翻看这类 PHP 发卡插件时还有两处代码与架构层面的隐患得留心。

第一处是 PHP 里的签名比对写法。如果插件在 `Signature.php` 里图省事拿宽松比较 `==` 去对签名，在老 PHP 7 环境里传个整数 `signature=0` 或布尔值就会撞上弱类型绕过；哪怕到了 ACG-Faka V3 跑的 PHP 8 环境里 `0 == "非数字字符串"` 已经修成了 `false`，一旦两端都是字符串且碰上 `0e` 开头的纯数字科学计数法哈希（Magic Hash），`==` 照样会当成 `0 == 0` 放行，外加普通字符串逐字节比对还带时序侧信道风险。规矩的写法必须先用 `is_string()` 拦掉数组和异形参数、判掉空串与空密钥，再进恒定时间的 `hash_equals()`：

```php
public static function safetyEquals(mixed $str, string $local): bool
{
    if (!is_string($str) || $str === '' || $local === '') {
        return false;
    }
    return hash_equals($local, $str);
}
```

如果收款网关和发卡插件两端都是自己可控的代码，顺手把简陋的 `md5($sorted_string . $token)` 字符串拼接升级成标准的 `hash_hmac('sha256', $sorted_string, $token)` 也稳妥得多。

第二处软肋是 `/user/api/order/callback.BEpusdt` 默认对全网任意 IP 敞开。只要密钥因为任何一次失误漏了，随便找台机器敲条 `curl` 就能往里灌假通知，网络层没有任何拦阻。

## 0x03 顺手帮五家同类站体检，四家没锁 `/app/` 目录

帮朋友止完血之后，我征得另外五家同类小站站长的许可，拿包含全零签名、空签名、缺失签名字段、`signature=0`、`signature=false`、`signature=[]` 数组、空密钥 MD5 / HMAC-SHA256、非成功 `status`、`0.01` 金额篡改、`Content-Type` 混淆、Handle 路径穿越和目录暴露检查在内的十几类用例帮他们过了一遍体检：

| 站点 | 架构 | 伪造回调测试 | `/app/` 与敏感文件暴露情况 |
|---|---|---|---|
| 站点 A | ACG-Faka | 34 次请求全部拦截 | 报错暴露物理路径，`/app/` 未配 `deny`（靠 PHP-FPM 执行返回空兜底） |
| 站点 B | ACG-Faka | 全部拦截 | 同上，`/app/` 可直接打到 PHP-FPM |
| 站点 C | Next.js (Vercel) | 接口强鉴权 | 全站套 Cloudflare，无静态源码目录与备份包残留隐患 |
| 站点 D | ACG-Faka | 全部拦截 | 暴露物理路径，`composer.json` 可直接下载 |
| 站点 E | ACG-Faka | 64 次请求全部拦截 | 暴露物理路径，`composer.json` 可读，`/app/` 未配 `deny` |

这五家站没被伪造回调打穿，纯粹是因为根目录刚好没留备份包，外加 PHP-FPM 正常运转替他们把 `Config.php` 执行成了空响应。但四家 PHP 站的 `/app/`、`/config/` 目录全都没在 Nginx 层配 `deny all`。这种状态就像在冰面上开车，只要哪天迁服务器改坏一次 PHP 解析规则，或者半夜维护随手在根目录打了个压缩包忘了删，分分钟就会步前面那位朋友的后尘。

## 0x04 五分钟把口子焊死

手头还在跑 ACG-Faka 或类似 PHP 发卡系统的，别等库存空了再翻日志，先把根目录下的压缩包和 SQL 导出文件彻底清出去（备份一律存到 Web 目录之外，比如 `/data/backups/`）：

```bash
find /www/wwwroot/faka/ -maxdepth 1 \
  \( -name "*.zip" -o -name "*.tar.gz" -o -name "*.rar" \
     -o -name "*.sql" -o -name "*.bak" -o -name "*.7z" \) \
  -exec rm -f {} \;
```

紧接着在 Nginx 的 `server` 块里把内部源码目录、敏感描述文件、归档后缀以及回调网关的来源 IP 白名单一次性配齐（BEpusdt 一般都是自己固定机器跑的收款服务，绑死网关 IP 之后就算哪天 Token 真漏了，外网伪造请求也连门都进不来）：

```nginx
# 放在 include enable-php*.conf 之前，封死内部源码、配置与运行时目录
location ~* ^/(app|config|runtime|vendor)/ {
    deny all;
    return 403;
}

# 封死所有备份包后缀与敏感工程文件
location ~* (\.(zip|tar\.gz|tgz|gz|rar|7z|sql|bak)$|composer\.(json|lock)|\.env|\.git) {
    deny all;
    return 403;
}

# 支付回调接口仅放行你自己的收款网关服务器 IP（用 try_files 进入口，避免 rewrite 提前跳出访问控制）
location ~* ^/user/api/order/callback\. {
    allow 203.0.113.10; # 换成你的真实支付网关服务器 IP
    deny all;
    try_files $uri /index.php?s=$uri&$args;
}
```

最后两条收尾动作也别省：凡是以前在网站目录里放过备份包的，一律按已经泄露处理，把支付 `api_token`、数据库密码、货源对接密钥和后台口令全换一遍；平时在监控脚本里给回调接口加个单 IP 频率限制（比如每分钟不超过 10 次），再盯一下访问日志里短时间连续刷出 `33` 字节响应的异常波动，基本就能把这类盗卡路子彻底断干净。

---

*文中所涉日志与五站体检均获站点负责人授权许可，IP 与域名均已脱敏。*
