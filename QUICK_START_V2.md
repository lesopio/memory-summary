# Memory-Summary v2.0 快速启动指南

## 🚀 5 分钟快速上手

### 步骤 1: 安装依赖

```bash
# 安装 Python 依赖
sudo pip3 install python-dotenv flask flask-cors requests

# 安装 Node.js 依赖（如果还没安装）
npm install
```

### 步骤 2: 配置 API Key

创建 `.env` 文件:

```bash
# LongCat API（必需）
LONGCAT_API_KEY=your_api_key_here

# 其他 API（可选）
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# 服务器端口
PORT=3001
```

### 步骤 3: 启用 v2 版本

编辑 `src/main.jsx`,修改导入:

```javascript
// 将这行
import MorandiAnnotationApp from './MorandiAnnotationApp'

// 改为
import MorandiAnnotationApp from './MorandiAnnotationApp_v2'
```

### 步骤 4: 启动应用

```bash
# 方式 1: 同时启动前后端（推荐）
npm run dev:all

# 方式 2: 分别启动
# 终端 1 - 启动后端
python3 server_v2.py

# 终端 2 - 启动前端
npm run dev
```

### 步骤 5: 访问应用

- **前端**: http://localhost:5173
- **后端 API**: http://localhost:3001

## 📱 移动端使用

1. 在移动设备浏览器中打开 http://localhost:5173
2. 点击左上角 **☰** 菜单图标选择 Persona
3. 点击右上角 **🧠** 大脑图标查看记忆库

## 🎯 核心功能

### 1. 对话聊天
- 选择 Persona
- 输入消息并发送
- AI 会自动检索相关记忆并回复

### 2. 记忆管理

**搜索记忆**:
- 在记忆库顶部搜索框输入关键词
- 支持语义搜索

**筛选记忆**:
- 点击"全部"、"公共"、"私有"按钮
- 查看不同类型的记忆

**编辑记忆**:
- 点击记忆卡片上的 ✏️ 编辑图标
- 修改内容后点击"保存"

**删除记忆**:
- 点击记忆卡片上的 🗑️ 删除图标
- 确认删除操作

### 3. 模型切换
- 在左侧面板选择模型:
  - **Flash-Chat**: 高性能通用对话
  - **Flash-Thinking**: 深度思考模式

### 4. 数据导出
- 点击记忆库底部的"导出记忆"按钮
- 下载 JSON 格式的所有数据

## 🔧 常见问题

### Q: 如何回退到旧版本?

编辑 `src/main.jsx`:
```javascript
import MorandiAnnotationApp from './MorandiAnnotationApp'
```

### Q: 数据保存在哪里?

- **数据库文件**: `./memory_data.db`
- **备份**: 使用"导出记忆"功能

### Q: 如何添加新的 API?

编辑 `api_config.py`,在 `PROVIDERS` 中添加配置:
```python
'your_provider': {
    'name': 'Your Provider',
    'base_url': 'https://api.example.com',
    'api_key_env': 'YOUR_API_KEY',
    'models': ['model-1', 'model-2'],
    'supports_stream': True,
}
```

### Q: 如何清空所有数据?

```bash
# 删除数据库文件
rm memory_data.db

# 重启服务器会自动创建新数据库
python3 server_v2.py
```

## 📚 更多文档

- **完整功能说明**: `COMPLETION_SUMMARY.md`
- **升级指南**: `UPGRADE_GUIDE.md`
- **改进方案**: `IMPROVEMENT_PLAN.md`
- **原始 README**: `README.md`

## 🆘 获取帮助

遇到问题?

1. 查看测试脚本: `python3 test_features.py`
2. 查看日志输出
3. 在 GitHub Issues 提问

## ✨ 新功能亮点

| 功能 | 说明 | 状态 |
|------|------|------|
| 📱 移动端适配 | 完全响应式设计 | ✅ |
| 💾 数据持久化 | SQLite 数据库 | ✅ |
| 🔍 记忆搜索 | 语义检索 + 筛选 | ✅ |
| ✏️ 记忆编辑 | 实时编辑和删除 | ✅ |
| 🔌 多 API 支持 | 5 种 AI 服务 | ✅ |
| ⚡ 流式输出 | 实时打字效果 | ✅ |

---

**版本**: 2.0.0  
**最后更新**: 2024-12  
**测试状态**: ✅ 全部通过
