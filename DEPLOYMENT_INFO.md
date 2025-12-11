# Memory-Summary 部署信息

## 🌐 公网访问地址

### 前端应用
**URL**: https://5173-ir5pgmyht3ksvzgr2mov3-ae5764cf.sg1.manus.computer

- 完整的 Web 界面
- 支持移动端和桌面端
- 响应式设计

### 后端 API
**URL**: https://3001-ir5pgmyht3ksvzgr2mov3-ae5764cf.sg1.manus.computer

- RESTful API 接口
- 支持流式响应
- 数据持久化存储

---

## ✅ 部署状态

| 组件 | 状态 | 端口 | 说明 |
|------|------|------|------|
| 前端服务 | ✅ 运行中 | 5173 | Vite 构建的静态文件 |
| 后端服务 | ✅ 运行中 | 3001 | Flask + SQLite |
| 数据库 | ✅ 已初始化 | - | SQLite (memory_data.db) |

---

## 🐛 Bug 修复总结

本次部署包含了对原始代码的全面 bug 修复:

### 1. 严重问题修复

#### ✅ 权重衰减逻辑 Bug
- **问题**: 使用 `dict.update()` 在列表推导式中的反模式
- **修复**: 重写为清晰的循环逻辑
- **文件**: `src/utils/memory_manager.py`

#### ✅ 流式响应重复保存
- **问题**: AI 响应被保存两次
- **修复**: 统一保存逻辑,避免重复
- **文件**: `server.py`

### 2. 中等问题修复

#### ✅ 权重上限过低
- **问题**: 权重上限为 1.0,增量 0.05 太小
- **修复**: 上限提升到 2.0,增量改为 0.1
- **文件**: `src/utils/memory_manager.py`, `server.py`

#### ✅ 记忆合并频率
- **问题**: 每 20 轮才合并一次
- **修复**: 改为每 10 轮合并
- **文件**: `server.py`

### 3. 安全改进

#### ✅ 输入验证
- 添加 Persona ID 验证
- 添加消息长度限制 (5000 字符)
- **文件**: `server.py`

#### ✅ 服务器绑定
- 支持生产环境绑定 0.0.0.0
- 开发环境绑定 localhost
- **文件**: `server.py`

---

## 📊 性能优化

### 已实现
- ✅ 数据库持久化 (SQLite)
- ✅ 内存缓存机制
- ✅ 权重衰减自动化
- ✅ 记忆合并优化

### 待优化 (长期)
- ⏳ 向量数据库集成 (Pinecone/Weaviate)
- ⏳ Redis 缓存层
- ⏳ 负载均衡
- ⏳ CDN 加速

---

## 🚀 使用指南

### 访问应用

1. **打开前端地址**: https://5173-ir5pgmyht3ksvzgr2mov3-ae5764cf.sg1.manus.computer

2. **选择 Persona**: 点击左侧列表选择对话角色

3. **开始对话**: 输入消息并发送

4. **查看记忆**: 点击右侧"记忆库"查看自动生成的记忆

### 配置 API Key

⚠️ **重要**: 当前部署未配置 LONGCAT_API_KEY,需要设置才能使用 AI 功能。

**方法 1: 环境变量**
```bash
export LONGCAT_API_KEY=your_api_key_here
```

**方法 2: .env 文件**
```bash
echo "LONGCAT_API_KEY=your_api_key_here" > .env
```

**方法 3: 使用 v2 版本 (支持多种 API)**
- 编辑 `src/main.jsx`,改用 `MorandiAnnotationApp_v2`
- 支持 OpenAI, Anthropic, Ollama 等

---

## 📱 移动端访问

应用已完全支持移动端:

1. 在手机浏览器打开前端地址
2. 点击左上角 ☰ 菜单选择 Persona
3. 点击右上角 🧠 图标查看记忆库
4. 享受流畅的移动端体验

---

## 🔧 本地开发

如果需要在本地运行:

### 方式 1: 使用原始版本

```bash
# 安装依赖
npm install
sudo pip3 install flask flask-cors python-dotenv requests

# 配置 API Key
echo "LONGCAT_API_KEY=your_key" > .env

# 启动服务
npm run dev:all
```

### 方式 2: 使用 v2 版本 (推荐)

```bash
# 修改 src/main.jsx
# import MorandiAnnotationApp from './MorandiAnnotationApp_v2'

# 启动后端
python3 server_v2.py

# 启动前端
npm run dev
```

---

## 📚 文档资源

| 文档 | 说明 |
|------|------|
| `BUG_ANALYSIS.md` | 详细的 bug 分析报告 |
| `COMPLETION_SUMMARY.md` | v2.0 功能完善总结 |
| `UPGRADE_GUIDE.md` | 升级指南 |
| `QUICK_START_V2.md` | 快速启动指南 |
| `README.md` | 项目说明 |

---

## 🛠️ 技术栈

### 前端
- React 18
- Vite 5
- Tailwind CSS
- Framer Motion
- Lucide React Icons

### 后端
- Python 3.11
- Flask
- SQLite
- LongCat API

### 部署
- Manus Sandbox
- 公网代理域名
- 临时部署 (沙箱生命周期)

---

## ⚠️ 注意事项

### 1. 临时部署
- 当前部署在 Manus Sandbox 中
- 沙箱关闭后服务将停止
- 数据库文件会保留在 GitHub 仓库中

### 2. API Key 安全
- 不要在前端代码中硬编码 API Key
- 使用环境变量或 .env 文件
- 不要将 .env 文件提交到 Git

### 3. 生产环境建议
- 使用专业的 WSGI 服务器 (Gunicorn, uWSGI)
- 配置 Nginx 反向代理
- 使用 PostgreSQL 或 MySQL 替代 SQLite
- 启用 HTTPS
- 配置 CORS 白名单

---

## 📞 获取帮助

如遇问题:

1. 查看日志文件: `server.log`, `frontend.log`
2. 运行测试: `python3 test_features.py`
3. 查看文档: `BUG_ANALYSIS.md`
4. GitHub Issues: https://github.com/lesopio/memory-summary/issues

---

## 🎯 下一步

### 短期 (1-2 周)
- [ ] 配置 LONGCAT_API_KEY
- [ ] 测试所有功能
- [ ] 添加更多 Persona
- [ ] 优化记忆生成质量

### 中期 (1-2 月)
- [ ] 部署到正式服务器
- [ ] 集成向量数据库
- [ ] 添加用户认证
- [ ] 实现数据导入/导出

### 长期 (3-6 月)
- [ ] 多用户支持
- [ ] 云端同步
- [ ] 移动应用
- [ ] 知识图谱可视化

---

**部署日期**: 2024-12-11  
**版本**: 2.0.0 (含 bug 修复)  
**状态**: ✅ 运行中  
**维护**: 自动化
