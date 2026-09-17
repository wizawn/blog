# -*- coding: utf-8 -*-
import re

PROTECTED = "- **微信**: GOV-HACK  ⚠️ **博主微信暂时被封，请优先加入上方 QQ 群（46333839）**"

emoji_chars = "✅❌⚠⭐🎯📋📦🖥🔧🔍💡📊🔗📝🎨🟢🟡🔴💬❤🎉💖👍🛑📌🔥😀"
emoji_set = set(emoji_chars) | {"️"}

def strip_emoji(s):
    return "".join(ch for ch in s if ch not in emoji_set)

files = [
    "/root/blog-repo/source/posts/codex-tools-tutorial.md",
    "/root/blog-repo/source/posts/codex-console-v111-tutorial.md",
    "/root/blog-repo/source/posts/chatgpt-pro-free-trial-methods-2026.md",
    "/root/blog-repo/source/posts/gpt-5-4-thinking-juice-test-guide-2026.md",
]

for path in files:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    out = []
    in_code = False
    for raw in lines:
        line = raw.rstrip("\n")
        nl = "\n" if raw.endswith("\n") else ""
        if line == PROTECTED:
            out.append(line + nl)
            continue
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_code = not in_code
            out.append(line + nl)
            continue
        if in_code:
            out.append(line + nl)
            continue
        text = line
        # star ratings -> words
        text = text.replace("⭐⭐⭐⭐⭐", "高").replace("⭐⭐⭐⭐", "较高")
        text = text.replace("⭐⭐⭐", "中").replace("⭐⭐", "中").replace("⭐", "中")
        # lone ❌ table cell -> 不支持
        text = re.sub(r"\|\s*❌\s*\|", "| 不支持 |", text)
        # strip remaining target emojis
        text = strip_emoji(text)
        # collapse internal multiple spaces (preserve leading indentation)
        m = re.match(r"^(\s*)(.*)$", text)
        lead, rest = m.group(1), m.group(2)
        rest = re.sub(r" {2,}", " ", rest)
        text = lead + rest
        # trim trailing whitespace
        text = text.rstrip()
        out.append(text + nl)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(out)
    print("done", path)
