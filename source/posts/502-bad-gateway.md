---
title: "502 Bad Gateway - 当理想撞上现实"
date: 2026-02-27T09:00:00+08:00
draft: false
categories: ["技术感悟"]
tags: ["运维", "随笔", "502"]
description: "刚入行时总觉得人生能配成高可用集群，真正扛事了才发现，上游说挂是一起挂的。"
weight: 10
---

刚入行那会儿特别迷信高可用架构。觉得只要前端架好 Nginx，底下挂上三台带权重的后端节点，配好 `max_fails` 被动摘除和自动故障转移，天塌下来总能留一个节点顶着：

```nginx
upstream life_backend {
    server 192.168.1.10:8080 weight=5;  # 熬夜攒出来的技术底子
    server 192.168.1.11:8080 weight=3;  # 手里看着还行的项目机会
    server 192.168.1.12:8080 weight=2;  # 一点不服输的心气
}
```

真在社会上挨了两年毒打才明白，现实生活里的故障从来不按教科书的独立概率发生。往往是一件事不顺，连带着精力、手头的项目和心态跟着一块雪崩，错误日志刷出来全是一个味儿：

```text
[error] upstream prematurely closed connection while reading response header from upstream
[error] connect() failed (111: Connection refused) while connecting to upstream
[error] no live upstreams while connecting to upstream
```

浏览器里孤零零一行 `502 Bad Gateway`。重试没用，刷新也没用，因为底下跑业务的那几个进程确实全趴窝了。

但真正做过运维的人，看到 `502` 骂归骂，骂完还是得顶着黑眼圈登机器：

```bash
systemctl status backend
journalctl -u backend -n 100 --no-pager
```

盯着屏幕发呆解决不了问题，拍脑门狂敲 `restart` 多半也还会再崩。先把挂掉的事实认下来，去翻日志看看到底是内存爆了、依赖断了，还是自己一开始把架构想得太美；把烂摊子一点点拆开修好，把监控补上，等 `curl -I http://127.0.0.1:8080/health` 重新吐出 `200 OK`，日子也就又能接着往下跑了。

写给最近同样在深夜盯着报错发呆的朋友。
