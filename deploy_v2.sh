#!/bin/bash
#
# Memory-Summary v2.0 一键部署脚本 (Ubuntu Server)
# 作者: Manus AI
#
# ----------------------------------------------------------------------
# 警告: 本脚本假设您在全新的 Ubuntu Server 环境中运行,并拥有 sudo 权限。
# ----------------------------------------------------------------------

set -e

REPO_NAME="memory-summary"
FRONTEND_PORT=5173
BACKEND_PORT=3001

echo "🚀 启动 Memory-Summary v2.0 一键部署..."
echo "----------------------------------------------------------------------"

# 1. 安装必备工具
echo "✅ 1. 检查并安装必备工具 (git, npm, python3-venv, screen)..."
sudo apt update
sudo apt install -y git npm python3-venv screen curl

# 2. 克隆仓库
if [ -d "$REPO_NAME" ]; then
    echo "⚠️ 仓库已存在，跳过克隆。"
    cd $REPO_NAME
    git pull
else
    echo "⬇️ 克隆 GitHub 仓库 lesopio/$REPO_NAME..."
    git clone https://github.com/lesopio/$REPO_NAME.git
    cd $REPO_NAME
fi

# 3. 配置 API Key
echo "----------------------------------------------------------------------"
read -p "请输入您的 LONGCAT_API_KEY (必填): " API_KEY
if [ -z "$API_KEY" ]; then
    echo "❌ 错误: API Key 不能为空。部署终止。"
    exit 1
fi

# 尝试获取服务器公网 IP
SERVER_IP=$(curl -s ifconfig.me || echo "localhost")
if [ "$SERVER_IP" == "localhost" ]; then
    echo "⚠️ 警告: 无法获取公网 IP，将使用 localhost。请手动替换 .env 文件中的地址。"
fi

# 写入 .env 文件 (用于前端构建和后端运行)
echo "✅ 写入 .env 文件..."
cat << EOF > .env
# 后端 API 基础地址 (用于前端构建)
VITE_API_BASE_URL=http://$SERVER_IP:$BACKEND_PORT

# LongCat API Key (用于后端运行)
LONGCAT_API_KEY=$API_KEY

# 服务器端口
PORT=$BACKEND_PORT
EOF

# 4. 安装 Python 依赖 (使用 venv)
echo "✅ 4. 安装 Python 依赖..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# 5. 安装 Node.js 依赖
echo "✅ 5. 安装 Node.js 依赖..."
npm install

# 6. 构建前端生产版本
echo "✅ 6. 构建前端生产版本..."
# 确保 VITE_API_BASE_URL 在构建时被注入
VITE_API_BASE_URL="http://$SERVER_IP:$BACKEND_PORT" npm run build

# 7. 启动服务 (使用 screen)
echo "✅ 7. 启动服务 (使用 screen 后台运行)..."

# 启动后端
echo "📡 启动后端 (Flask) 到 screen 会话: memory-backend"
screen -dmS memory-backend bash -c "cd $REPO_NAME && source venv/bin/activate && ENV=production python3 server_v2.py"

# 启动前端
echo "🌐 启动前端 (HTTP Server) 到 screen 会话: memory-frontend"
screen -dmS memory-frontend bash -c "cd $REPO_NAME/dist && python3 -m http.server $FRONTEND_PORT"

echo "----------------------------------------------------------------------"
echo "🎉 部署完成!"
echo "----------------------------------------------------------------------"
echo "访问地址:"
echo "前端 (Web App): http://$SERVER_IP:$FRONTEND_PORT"
echo "后端 (API):    http://$SERVER_IP:$BACKEND_PORT"
echo ""
echo "注意: 如果您使用了云服务器，请确保已在防火墙/安全组中开放 $FRONTEND_PORT 和 $BACKEND_PORT 端口。"
echo ""
echo "后台管理:"
echo "使用 'screen -ls' 查看会话。"
echo "使用 'screen -r memory-backend' 或 'screen -r memory-frontend' 重新连接会话。"
echo "使用 Ctrl+A, D 组合键分离会话。"
echo "----------------------------------------------------------------------"
