---
title: "Codex 卡住、提交消息失败或一直无响应，先按这 5 步排查"
slug: "codex-stuck-troubleshooting"
date: 2026-09-18T12:50:00+08:00
draft: false
weight: 50
categories: ["Codex常见问题"]
tags: ["Codex", "无响应", "提交失败", "日志排查"]
description: "Codex 卡住或提交消息失败时，从审批、终端、会话和日志四个方向快速定位，不误删历史。"
image: "/blog-cover-default.jpg"
---

{{< figure src="/images/wechat-qr.jpg" alt="微信二维码" width="200" >}}
{{< figure src="/images/qq-group-qr.jpg" alt="QQ群二维码" width="200" >}}
联系方式 & 交流群

- **QQ**: 46333839
- **微信**: GOV-HACK

---

## 五步快速排查

1. **先看是不是在等审批**：工具调用、文件写入或网络访问可能停在等待确认；完成或拒绝后，回到会话观察是否继续。
2. **开一个新的终端窗口**：运行 `pwd` 和 `git status`。如果命令本身都卡住，先处理终端、磁盘或网络问题，不要重复发送同一条消息。
3. **换成短请求或新建会话**：用一句简单的问题测试。短请求能返回，通常是原任务上下文太大或某一步工具调用卡住。
4. **更新并重启 Codex**：保存未发送的文字后，完全退出应用再打开；仍无响应时再尝试新会话。不要因为界面暂时空白就删除 `.codex` 目录。
5. **最后再看日志**：macOS 日志通常在 `~/Library/Logs/com.openai.codex/YYYY/MM/DD`，会话记录在 `$CODEX_HOME/sessions`。分享前删掉代码、路径、邮箱、token 和 `auth.json` 内容。

如果错误是反复 `Reconnecting`，可先看[这篇连接排查](../codex-reconnecting-5-times/)。如果是 `capacity`、429 或 503，按[常见报错表](../codex-common-errors/)处理。持续失败时，向 [OpenAI 帮助中心](https://help.openai.com/) 提供完整错误、客户端版本、模型、时间和请求 ID；不要把凭据当作“诊断材料”上传。

参考：[Codex 故障排除](https://developers.openai.com/zh-Hans/docs/reference/troubleshooting)。
