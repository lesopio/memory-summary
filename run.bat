@echo off
REM Windows 批处理脚本 - 启动 Python 后端和前端
REM 使用方法: 运行 run.bat

setlocal enabledelayedexpansion

echo.
echo =================================
echo   Morandi Annotation App
echo   Python + Vite 启动脚本
echo =================================
echo.

REM 检查 Python
echo [*] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [-] Python 未安装或不在 PATH 中
    echo [!] 请确保已安装 Python 3.8+ 并添加到 PATH
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [+] 找到 %PYTHON_VERSION%

REM 检查依赖
echo.
echo [*] 检查 Python 依赖...
python -c "import flask, flask_cors, dotenv, requests" >nul 2>&1
if errorlevel 1 (
    echo [-] 依赖缺失，正在安装...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [-] 依赖安装失败
        pause
        exit /b 1
    )
    echo [+] 依赖安装完成
) else (
    echo [+] 依赖已安装
)

REM 检查 Node.js 和 npm
echo.
echo [*] 检查 Node.js 环境...
npm --version >nul 2>&1
if errorlevel 1 (
    echo [-] npm 未安装或不在 PATH 中
    echo [!] 前端需要 Node.js，但可以选择先启动后端
    echo.
)

REM 提示用户选择
echo.
echo 启动选项:
echo  1. 仅启动 Python 后端
echo  2. 启动 Python 后端 + 前端 (需要 npm)
echo  3. 退出
echo.
set /p CHOICE="请选择 (1-3): "

if "%CHOICE%"=="1" (
    echo.
    echo [+] 启动 Python 后端...
    echo.
    python server.py
) else if "%CHOICE%"=="2" (
    echo.
    echo [+] 启动 Python 后端和前端...
    echo.
    start "Morandi Backend" python server.py
    timeout /t 2 /nobreak
    start "Morandi Frontend" cmd /k "npm run dev"
) else (
    echo.
    echo [*] 已退出
)

pause
