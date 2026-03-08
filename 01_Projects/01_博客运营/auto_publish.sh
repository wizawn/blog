#!/bin/bash
# 博客自动发布脚本

BLOG_DIR="/root/.openclaw/workspace/01_Projects/01_博客运营/blog"
CONTENT_FACTORY_DIR="/root/.openclaw/workspace/01_Projects/03_内容工厂"
DATE=$(date +%Y-%m-%d)

echo "=== 博客自动发布 ==="
echo "日期：$DATE"
echo ""

# 检查今日文章
if [ ! -d "$CONTENT_FACTORY_DIR/$DATE" ]; then
    echo "❌ 今日文章目录不存在"
    exit 1
fi

# 移动文章到博客目录
echo "移动文章到博客目录..."
cp "$CONTENT_FACTORY_DIR/$DATE"/*.md "$BLOG_DIR/source/posts/"

# 构建博客
echo "构建博客..."
cd "$BLOG_DIR"
hugo --gc --minify

# 部署到 Cloudflare Pages (手动执行)
echo "✅ 博客构建完成"
echo ""
echo "下一步：手动部署到 Cloudflare Pages"
echo "cd $BLOG_DIR"
echo "wrangler pages deploy public/"
