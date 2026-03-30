#!/bin/bash
# 博客部署脚本 - Cloudflare Workers

set -e

WORKSPACE="/root/.openclaw/workspace/01_Projects/01_博客运营/blog"
API_KEY="130a4dfc45ea5ae510ceed8a079292a616744"
EMAIL="hihacker@foxmail.com"

cd "$WORKSPACE"

echo "🔨 生成静态文件..."
hugo --minify

echo "🚀 部署到 Cloudflare Workers..."
export CLOUDFLARE_API_KEY="$API_KEY"
export CLOUDFLARE_EMAIL="$EMAIL"
wrangler deploy

echo "✅ 部署完成！"
echo "📱 Workers URL: https://blog-worker.hihacker.workers.dev"
echo "🌐 自定义域名：https://blog.caowo.de (需手动绑定)"
echo ""
echo "⚠️  如需绑定自定义域名，请手动操作："
echo "   1. 访问 https://dash.cloudflare.com"
echo "   2. Workers & Pages → blog-worker"
echo "   3. Triggers → Custom Domains"
echo "   4. Add domain: blog.caowo.de"
