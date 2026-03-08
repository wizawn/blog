#!/bin/bash
# OpenClaw 一键安装和配置脚本

set -e

echo "========================================================================"
echo "🚀 ClawGuard-BNB OpenClaw 一键安装"
echo "========================================================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Python 版本
echo "📋 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 未安装${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✅ Python $PYTHON_VERSION${NC}"
echo ""

# 检查 pip
echo "📋 检查 pip..."
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ pip3 已安装${NC}"
echo ""

# 安装依赖
echo "📦 安装依赖..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt 不存在，跳过依赖安装${NC}"
fi
echo ""

# 创建 .env 文件
echo "📝 配置环境变量..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ 已创建 .env 文件${NC}"
        echo -e "${YELLOW}⚠️  请编辑 .env 文件填写您的配置${NC}"
    else
        echo -e "${YELLOW}⚠️  .env.example 不存在，跳过${NC}"
    fi
else
    echo -e "${GREEN}✅ .env 文件已存在${NC}"
fi
echo ""

# 运行自动配置
echo "🔧 运行自动配置..."
if [ -f "openclaw_configure.py" ]; then
    python3 openclaw_configure.py
    echo -e "${GREEN}✅ 自动配置完成${NC}"
else
    echo -e "${YELLOW}⚠️  openclaw_configure.py 不存在，跳过${NC}"
fi
echo ""

# 运行验证
echo "🔍 验证配置..."
if [ -f "openclaw_validate.py" ]; then
    python3 openclaw_validate.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 验证通过${NC}"
    else
        echo -e "${YELLOW}⚠️  验证发现问题，请检查上面的输出${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  openclaw_validate.py 不存在，跳过验证${NC}"
fi
echo ""

# 完成
echo "========================================================================"
echo "✅ 安装完成！"
echo "========================================================================"
echo ""
echo "快速开始:"
echo ""
echo "  1. CLI 模式:"
echo "     python3 clawguard.py price BTC --json"
echo ""
echo "  2. HTTP API 服务器:"
echo "     python3 openclaw_server.py"
echo ""
echo "  3. 查看示例:"
echo "     python3 openclaw_examples.py"
echo ""
echo "  4. 查看文档:"
echo "     cat OPENCLAW_QUICKSTART.md"
echo ""
echo "========================================================================"
echo ""

# 询问是否启动服务器
read -p "是否现在启动 HTTP API 服务器？(y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 启动 HTTP API 服务器..."
    python3 openclaw_server.py
fi
