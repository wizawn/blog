#!/usr/bin/env python3
"""
言零的博客 (blog.caowo.de) — 存量内容安全清洗与快讯分流脚本
默认干跑（--dry-run），仅打印变更摘要；确认无误后传入 --apply 实际执行。

完成四件事：
1. 将带 Auto-Generated / Ai-Processed / Rss 标签的自动抓取文章从 the configured content root posts directory 移至 the configured content root feeds directory
2. 移除三篇早期随笔 (hello-world / 404-not-found / 502-bad-gateway) 与域名声明的首页强置顶 weight
3. 移除所有文章里硬编码指向 /blog-cover-default.jpg 的默认封面字段
4. 移除文章正文开头硬塞的 qq-group-qr.jpg 手机截图与“可否打赏一些呀~”段落，以及 about/links 重复的首行 H1
"""

import argparse
import os
import re
import shutil
from pathlib import Path


AUTO_TAG_PATTERN = re.compile(r"(auto-generated|ai-processed)", re.IGNORECASE)
UNPIN_SLUGS = {
    "hello-world",
    "404-not-found",
    "502-bad-gateway",
    "domain-ownership-clarification",
}

# 匹配旧文章开头固定插入的二维码与讨赏模板块
TOP_QR_BLOCK_RE = re.compile(
    r"(?:\{\{<\s*figure\s+src=\"/images/qq-group-qr\.jpg\"[^>]*>\}\}|!\[QQ群二维码\]\(/images/qq-group-qr\.jpg[^\n]*\)|<figure>\s*<img[^>]*qq-group-qr\.jpg[^>]*>.*?</figure>)"
    r"[\s\S]{0,360}?可否打赏一些呀~\s*---?\s*",
    re.MULTILINE,
)


def split_frontmatter(text: str):
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[: end + 5], text[end + 5 :]
    if text.startswith("+++\n"):
        end = text.find("\n+++\n", 4)
        if end != -1:
            return text[: end + 5], text[end + 5 :]
    return "", text


def process_repo(repo_root: Path, apply: bool):
    content_root = repo_root / "source" if (repo_root / "source" / "posts").exists() else repo_root / "content"
    posts_dir = content_root / "posts"
    feeds_dir = content_root / "feeds"

    moved_feeds = 0
    unpinned = 0
    cleaned_cover = 0
    cleaned_qr = 0
    cleaned_dup_h1 = 0

    if not posts_dir.exists():
        raise SystemExit(f"未找到目录: {posts_dir}")

    if apply:
        feeds_dir.mkdir(parents=True, exist_ok=True)

    # 1. 遍历 the configured content root posts directory
    for md_path in sorted(posts_dir.rglob("*.md")):
        if md_path.name == "_index.md":
            continue

        raw = md_path.read_text(encoding="utf-8")
        fm, body = split_frontmatter(raw)
        if not fm:
            continue

        # 判断是否为自动抓取的 RSS 文章
        if AUTO_TAG_PATTERN.search(fm):
            rel = md_path.relative_to(posts_dir)
            # 若为 page bundle (posts/xxx/index.md) 则移动整个子目录，否则移动单文件
            if md_path.name == "index.md" and md_path.parent != posts_dir:
                src_item = md_path.parent
                dst_item = feeds_dir / src_item.name
            else:
                src_item = md_path
                dst_item = feeds_dir / rel

            moved_feeds += 1
            if apply:
                dst_item.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src_item), str(dst_item))
            continue

        new_fm = fm
        new_body = body

        # 取消旧随笔首页强置顶 weight
        slug_key = md_path.parent.name if md_path.name == "index.md" else md_path.stem
        if slug_key in UNPIN_SLUGS or any(s in fm for s in UNPIN_SLUGS):
            updated_fm = re.sub(r"(?m)^weight\s*[:=]\s*\d+\s*\n", "", new_fm)
            if updated_fm != new_fm:
                new_fm = updated_fm
                unpinned += 1

        # 清理硬编码默认绿电路板封面
        updated_fm = re.sub(
            r'(?m)^image\s*[:=]\s*["\']?/blog-cover-default\.jpg["\']?\s*\n',
            "",
            new_fm,
        )
        if updated_fm != new_fm:
            new_fm = updated_fm
            cleaned_cover += 1

        # 清理正文开头的二维码截屏与讨赏块
        # 只处理正文开头的公共模板，避免误删文章中段的项目专属群号或联系方式。
        if TOP_QR_BLOCK_RE.search(new_body[:400]):
            updated_body = TOP_QR_BLOCK_RE.sub("", new_body, count=1)
        else:
            updated_body = new_body
        if updated_body != new_body:
            new_body = updated_body
            cleaned_qr += 1

        if (new_fm != fm or new_body != body) and apply:
            md_path.write_text(new_fm + new_body, encoding="utf-8")

    # 2. 清理 about / links 静态页首行重复 H1 与默认电路板图
    content_dir = content_root
    for md_path in sorted(content_dir.rglob("*.md")):
        if posts_dir in md_path.parents or feeds_dir in md_path.parents:
            continue
        raw = md_path.read_text(encoding="utf-8")
        fm, body = split_frontmatter(raw)
        if not fm:
            continue
        new_fm = re.sub(
            r'(?m)^image\s*[:=]\s*["\']?/blog-cover-default\.jpg["\']?\s*\n',
            "",
            fm,
        )
        new_body = re.sub(r"^\s*#\s+[^\n]+\n+", "\n", body, count=1)
        if new_body != body:
            cleaned_dup_h1 += 1
        if (new_fm != fm or new_body != body) and apply:
            md_path.write_text(new_fm + new_body, encoding="utf-8")

    mode = "APPLY 已写入" if apply else "DRY-RUN 预览（未改文件）"
    print(f"[{mode}]")
    print(f"  - 迁移至 the configured content root feeds directory 的自动快讯数: {moved_feeds}")
    print(f"  - 取消首页强置顶旧文数: {unpinned}")
    print(f"  - 移除默认绿电路板封面数: {cleaned_cover}")
    print(f"  - 移除开篇手机截屏二维码块数: {cleaned_qr}")
    print(f"  - 清理静态页首行重复 H1 数: {cleaned_dup_h1}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="Hugo 博客仓库根目录路径")
    parser.add_argument("--apply", action="store_true", help="确认执行修改")
    args = parser.parse_args()
    process_repo(Path(args.repo).resolve(), apply=args.apply)
