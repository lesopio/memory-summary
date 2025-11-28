# 快速启动指南 - Python 后端

## 🚀 30 秒快速启动

### Windows 用户
```powershell
python server.py
```
然后在另一个终端：
```powershell
npm run dev
```

### Linux/Mac 用户
```bash
python3 server.py
```
然后在另一个终端：
```bash
npm run dev
```

---

## 前置要求

- ✅ Python 3.8+ 已安装
- ✅ Node.js 和 npm 已安装
- ✅ LONGCAT_API_KEY 已设置

### 检查 Python
```bash
python --version       # Windows
python3 --version      # Linux/Mac
```

### 检查 Node.js
```bash
node --version
npm --version
```

---

## 安装依赖

```bash
# 一次性安装所有 Python 依赖
pip install -r requirements.txt          # Windows
pip3 install -r requirements.txt         # Linux/Mac
```

---

## 启动方式

### 方式 1：分两个终端启动（推荐）

**终端 1 - 启动后端：**
```bash
python server.py        # Windows
python3 server.py       # Linux/Mac
```

**终端 2 - 启动前端：**
```bash
npm run dev
```

### 方式 2：使用启动脚本

**Windows:**
```bash
run.bat
```

**Linux/Mac:**
```bash
chmod +x run.sh
./run.sh
```

### 方式 3：使用 npm 脚本

```bash
npm run server:python   # 仅启动后端
npm run dev             # 仅启动前端
npm run dev:all:python  # 同时启动后端和前端
```

---

## 设置 API Key

### 方法 1：.env 文件（推荐）

在项目根目录创建 `.env` 文件：
```env
LONGCAT_API_KEY=sk_xxx_your_key_here
```

### 方法 2：环境变量

**Windows PowerShell:**
```powershell
$env:LONGCAT_API_KEY="sk_xxx_your_key_here"
python server.py
```

**Windows CMD:**
```cmd
set LONGCAT_API_KEY=sk_xxx_your_key_here
python server.py
```

**Linux/Mac:**
```bash
export LONGCAT_API_KEY="sk_xxx_your_key_here"
python3 server.py
```

---

## 验证运行

### 后端启动成功标志
```
[INFO] 服务器运行在 http://localhost:3001
[INFO] LongCat API: https://api.longcat.chat/openai
[INFO] ✅ API Key 已设置
```

### 前端启动成功标志
```
  VITE v5.4.21  ready in 937 ms
  ➜  Local:   http://localhost:5173/
```

### 打开应用
浏览器访问：http://localhost:5173/

---

## 故障排除

### 问题：Python 命令不存在
**解决方案：**
- 确保 Python 已安装：`python --version`
- 如果没有，[下载 Python](https://www.python.org/downloads/)

### 问题：Module not found (flask, requests 等)
**解决方案：**
```bash
pip install -r requirements.txt      # Windows
pip3 install -r requirements.txt     # Linux/Mac
```

### 问题：端口 3001 已被占用
**解决方案：**
修改 `server.py` 中的 `PORT = 3001`

### 问题：API Key 未设置警告
**解决方案：**
见上面的"设置 API Key"部分

### 问题：流式响应为空
**解决方案：**
1. 检查 API Key 是否有效
2. 检查网络连接
3. 查看控制台日志中的具体错误

---

## 项目结构

```
h:\AI_Project\
├── server.py                    # Python Flask 后端
├── server.js                    # (旧) Node.js Express 后端
├── requirements.txt             # Python 依赖
├── run.bat                      # Windows 启动脚本
├── run.sh                       # Linux/Mac 启动脚本
├── run.py                       # Python 启动脚本
├── .env                         # 环境变量 (需要创建)
├── src/
│   ├── main.jsx
│   ├── index.css
│   ├── MorandiAnnotationApp.jsx
│   ├── components/
│   │   └── ui/
│   │       ├── button.jsx
│   │       ├── card.jsx
│   │       └── input.jsx
│   └── utils/
│       ├── memoryManager.js     # (旧) JavaScript 记忆管理器
│       └── memory_manager.py    # Python 记忆管理器
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── index.html
├── package.json
├── PYTHON_MIGRATION.md          # Python 迁移指南
└── SETUP_API_KEY.md             # API Key 设置指南
```

---

## 常用命令速查

| 命令 | 描述 |
|------|------|
| `python server.py` | 启动 Python 后端 |
| `npm run dev` | 启动 Vite 前端 |
| `npm run dev:all:python` | 同时启动后端和前端 |
| `npm run server:python` | (npm 脚本) 启动后端 |
| `pip install -r requirements.txt` | 安装 Python 依赖 |
| `python --version` | 检查 Python 版本 |
| `npm --version` | 检查 npm 版本 |

---

## 更多信息

- 📚 详细迁移指南：见 `PYTHON_MIGRATION.md`
- 🔑 API Key 设置：见 `SETUP_API_KEY.md`
- 📖 项目 README：见 `README.md`

---

**祝你使用愉快！如有问题，请查看详细文档或检查控制台日志。** 🎉
