# 浏览器扩展安装指南

## 问题总结

**当前状态:** 服务器已安装 XFCE4 + XRDP 桌面环境，但浏览器扩展无法在 headless 模式下自动加载。

**原因:** Snap 版 Chromium 的 AppArmor 安全策略限制了扩展的自动加载。

---

## 解决方案：通过 RDP 手动安装

### 步骤 1: 连接 RDP 桌面

```
地址：104.249.159.149:3389
用户名：root
密码：当前 SSH 密码
```

### 步骤 2: 打开 Chromium 浏览器

在 RDP 桌面中启动 Chromium。

### 步骤 3: 加载扩展

1. 访问 `chrome://extensions/`
2. 开启右上角的 **开发者模式** (Developer mode)
3. 点击 **加载已解压的扩展程序** (Load unpacked)
4. 选择扩展目录：
   ```
   /root/.nvm/versions/node/v24.13.1/lib/node_modules/openclaw/assets/chrome-extension/
   ```
5. 扩展应显示为 "OpenClaw Browser Relay"

### 步骤 4: 固定扩展到工具栏

1. 点击浏览器右上角的拼图图标 🧩
2. 找到 OpenClaw Browser Relay
3. 点击图钉图标 📌 固定到工具栏

### 步骤 5: 激活扩展

1. 打开任意网页（如 https://example.com）
2. 点击工具栏中的 OpenClaw 扩展图标
3. 确保徽章状态为 **ON**（已连接标签页）

---

## 验证连接

扩展安装完成后，在终端执行：

```bash
openclaw browser status
```

应显示：
- `running: true`
- `cdpReady: true`
- `profile: chrome`

---

## 自动化脚本（可选）

创建启动脚本 `/root/start-browser.sh`：

```bash
#!/bin/bash
export DISPLAY=:99
chromium-browser \
  --no-sandbox \
  --disable-dev-shm-usage \
  --load-extension=/root/.nvm/versions/node/v24.13.1/lib/node_modules/openclaw/assets/chrome-extension/ \
  --user-data-dir=/root/.openclaw/chrome-profile \
  --remote-debugging-port=18792 &
```

然后添加到 XFCE 自动启动：
```bash
mkdir -p ~/.config/autostart
cp /root/start-browser.sh ~/.config/autostart/
chmod +x ~/.config/autostart/start-browser.sh
```

---

## 故障排除

### 问题：扩展不显示
- 确认扩展目录路径正确
- 检查 `manifest.json` 是否存在
- 重启 Chromium

### 问题：无法连接 DevTools
- 确认端口 18792 未被占用
- 检查防火墙设置
- 重启 Gateway：`openclaw gateway restart`

### 问题：AppArmor 阻止
- 使用非 Snap 版 Chromium：`apt install chromium`
- 或临时禁用 AppArmor（不推荐）

---

**最后更新:** 2026-02-25 16:10 UTC
