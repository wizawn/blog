@echo off
REM OpenClaw 一键安装和配置脚本 (Windows)

echo ========================================================================
echo 🚀 ClawGuard-BNB OpenClaw 一键安装
echo ========================================================================
echo.

REM 检查 Python
echo 📋 检查 Python 版本...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装
    pause
    exit /b 1
)
python --version
echo ✅ Python 已安装
echo.

REM 检查 pip
echo 📋 检查 pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip 未安装
    pause
    exit /b 1
)
echo ✅ pip 已安装
echo.

REM 安装依赖
echo 📦 安装依赖...
if exist requirements.txt (
    pip install -r requirements.txt
    echo ✅ 依赖安装完成
) else (
    echo ⚠️  requirements.txt 不存在，跳过依赖安装
)
echo.

REM 创建 .env 文件
echo 📝 配置环境变量...
if not exist .env (
    if exist .env.example (
        copy .env.example .env
        echo ✅ 已创建 .env 文件
        echo ⚠️  请编辑 .env 文件填写您的配置
    ) else (
        echo ⚠️  .env.example 不存在，跳过
    )
) else (
    echo ✅ .env 文件已存在
)
echo.

REM 运行自动配置
echo 🔧 运行自动配置...
if exist openclaw_configure.py (
    python openclaw_configure.py
    echo ✅ 自动配置完成
) else (
    echo ⚠️  openclaw_configure.py 不存在，跳过
)
echo.

REM 运行验证
echo 🔍 验证配置...
if exist openclaw_validate.py (
    python openclaw_validate.py
    if errorlevel 1 (
        echo ⚠️  验证发现问题，请检查上面的输出
    ) else (
        echo ✅ 验证通过
    )
) else (
    echo ⚠️  openclaw_validate.py 不存在，跳过验证
)
echo.

REM 完成
echo ========================================================================
echo ✅ 安装完成！
echo ========================================================================
echo.
echo 快速开始:
echo.
echo   1. CLI 模式:
echo      python clawguard.py price BTC --json
echo.
echo   2. HTTP API 服务器:
echo      python openclaw_server.py
echo.
echo   3. 查看示例:
echo      python openclaw_examples.py
echo.
echo   4. 查看文档:
echo      type OPENCLAW_QUICKSTART.md
echo.
echo ========================================================================
echo.

REM 询问是否启动服务器
set /p REPLY="是否现在启动 HTTP API 服务器？(y/n) "
if /i "%REPLY%"=="y" (
    echo.
    echo 🚀 启动 HTTP API 服务器...
    python openclaw_server.py
)

pause
