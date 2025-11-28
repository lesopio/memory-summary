#!/bin/bash

# Linux/Mac 启动脚本 - 启动 Python 后端和前端

echo ""
echo "================================="
echo "  Morandi Annotation App"
echo "  Python + Vite 启动脚本"
echo "================================="
echo ""

# 检查 Python
echo "[*] 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "[-] Python 未安装"
    echo "[!] 请先安装 Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "[+] 找到 $PYTHON_VERSION"

# 检查依赖
echo ""
echo "[*] 检查 Python 依赖..."
python3 -c "import flask, flask_cors, dotenv, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[-] 依赖缺失，正在安装..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[-] 依赖安装失败"
        exit 1
    fi
    echo "[+] 依赖安装完成"
else
    echo "[+] 依赖已安装"
fi

# 检查 Node.js
echo ""
echo "[*] 检查 Node.js 环境..."
if ! command -v npm &> /dev/null; then
    echo "[-] npm 未安装"
    echo "[!] 前端需要 Node.js，但可以选择先启动后端"
    echo ""
fi

# 提示用户选择
echo ""
echo "启动选项:"
echo " 1. 仅启动 Python 后端"
echo " 2. 启动 Python 后端 + 前端 (需要 npm)"
echo " 3. 退出"
echo ""
read -p "请选择 (1-3): " CHOICE

case $CHOICE in
    1)
        echo ""
        echo "[+] 启动 Python 后端..."
        echo ""
        python3 server.py
        ;;
    2)
        echo ""
        echo "[+] 启动 Python 后端和前端..."
        echo ""
        python3 server.py &
        BACKEND_PID=$!
        sleep 2
        npm run dev
        kill $BACKEND_PID 2>/dev/null
        ;;
    3)
        echo ""
        echo "[*] 已退出"
        ;;
    *)
        echo ""
        echo "[-] 无效选择"
        ;;
esac
