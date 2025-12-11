#!/bin/bash

# Memory-Summary 生产环境启动脚本

echo "🚀 启动 Memory-Summary 生产环境..."

# 检查环境变量
if [ -z "$LONGCAT_API_KEY" ]; then
    echo "⚠️  警告: LONGCAT_API_KEY 未设置"
    echo "请设置环境变量或创建 .env 文件"
fi

# 设置生产环境标志
export ENV=production

# 启动后端服务器
echo "📡 启动后端服务器..."
python3 server_v2.py &
SERVER_PID=$!

# 等待服务器启动
sleep 2

# 使用 Python 简单 HTTP 服务器提供前端静态文件
echo "🌐 启动前端服务器..."
cd dist
python3 -m http.server 5173 &
FRONTEND_PID=$!

cd ..

echo ""
echo "✅ 服务已启动!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 前端地址: http://localhost:5173"
echo "🔌 后端 API: http://localhost:3001"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "后端进程 PID: $SERVER_PID"
echo "前端进程 PID: $FRONTEND_PID"
echo ""
echo "按 Ctrl+C 停止服务..."

# 等待中断信号
trap "echo ''; echo '🛑 停止服务...'; kill $SERVER_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

# 保持脚本运行
wait
