# Python 后端迁移指南

## 概述

已将 Node.js/Express 后端成功转换为 Python/Flask 后端，保持所有 API 端点和功能不变。

## 迁移内容

- ✅ `server.js` → `server.py` (Flask 应用)
- ✅ `src/utils/memoryManager.js` → `src/utils/memory_manager.py` (记忆管理器)
- ✅ 添加 `requirements.txt` (Python 依赖)

## 安装 Python 依赖

### 方法 1：自动安装（推荐）

```bash
python run.py
```

这会自动检查并安装所需的依赖，然后启动后端和前端。

### 方法 2：手动安装

```bash
# Windows
pip install -r requirements.txt

# Linux/Mac
pip3 install -r requirements.txt
```

## 运行应用

### 使用 Python 脚本（推荐）

```bash
python run.py
```

### 使用 npm 脚本

后端和前端同时运行：
```bash
npm run dev:all:python
```

仅运行 Python 后端：
```bash
npm run server:python
```

仅运行 Vite 前端：
```bash
npm run dev
```

### 手动运行

终端 1 - 启动后端：
```bash
python server.py
```

终端 2 - 启动前端：
```bash
npm run dev
```

## 环境变量配置

创建 `.env` 文件或设置环境变量：

```bash
LONGCAT_API_KEY=your_api_key_here
LONGCAT_API_TIMEOUT_MS=30000  # 可选，默认 30000 ms
```

**Windows PowerShell:**
```powershell
$env:LONGCAT_API_KEY="your_api_key_here"
python server.py
```

**Windows CMD:**
```cmd
set LONGCAT_API_KEY=your_api_key_here
python server.py
```

**Linux/Mac:**
```bash
export LONGCAT_API_KEY=your_api_key_here
python3 server.py
```

## API 端点（保持不变）

所有原有的 API 端点都已保留：

| 端点 | 方法 | 描述 |
|------|------|------|
| `/personas` | GET | 获取 Persona 列表 |
| `/switch-model` | POST | 切换 AI 模型 |
| `/chat` | POST | 发送聊天消息（流式响应） |
| `/memories/:personaId` | GET | 获取指定 Persona 的记忆 |
| `/memories-live/:personaId` | GET | 获取实时记忆 |
| `/memories` | POST | 手动添加记忆 |
| `/export` | GET | 导出所有数据 |

## Python 后端特性

- 🔄 完全兼容原 Node.js API
- 🚀 使用 Flask 框架（轻量级、易扩展）
- 📝 流式响应支持（SSE 格式）
- 💾 异步记忆保存（后台线程）
- ⏰ 定期权重衰减（后台线程）
- 🔐 同样的 CORS 和环境变量支持
- 📊 相同的记忆管理和向量相似度计算

## 依赖说明

| 包名 | 版本 | 用途 |
|------|------|------|
| Flask | 3.0.0 | Web 框架 |
| flask-cors | 4.0.0 | CORS 支持 |
| python-dotenv | 1.0.0 | 环境变量加载 |
| requests | 2.31.0 | HTTP 请求库 |

## 调试

### 查看详细日志

后端默认输出日志到控制台：

```
[INFO] 服务器运行在 http://localhost:3001
[INFO] LongCat API: https://api.longcat.chat/openai
[INFO] ✅ API Key 已设置
[INFO] [Chat] 调用 API - Persona: 1, Model: LongCat-Flash-Chat
[INFO] [Chat] 流式响应完成，总长度: 256 字符
```

### 常见问题

**Q: 导入错误？**
```bash
# 确保在项目根目录运行
cd h:\AI_Project
python server.py
```

**Q: API Key 未设置？**
```
⚠️  警告：LONGCAT_API_KEY 未设置！
请创建 .env 文件并添加：
LONGCAT_API_KEY=your_api_key_here
```

**Q: 流式响应为空？**
- 检查 LONGCAT_API_KEY 是否有效
- 确认网络连接正常
- 查看日志中的 API 响应状态

## 保持与前端兼容

前端代码不需要任何修改，因为 Python 后端使用相同的：
- ✅ API 端点路径
- ✅ 请求/响应格式（JSON）
- ✅ 流式响应格式（text/plain）
- ✅ CORS 头部配置

## 后续改进建议

1. **向量数据库**：将简单的向量计算替换为 Pinecone/Weaviate
2. **数据持久化**：使用 SQLite/PostgreSQL 存储记忆和聊天记录
3. **缓存**：使用 Redis 缓存热门记忆
4. **日志系统**：集成 Loguru 或 ELK Stack
5. **测试**：添加 pytest 单元测试
6. **容器化**：创建 Docker 镜像便于部署

---

**使用 Python 后端享受更灵活的开发体验！** 🎉
