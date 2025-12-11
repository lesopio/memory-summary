# Memory-Summary 升级指南

## 版本 2.0 新特性

本次升级为 Memory-Summary 带来了全面的功能增强和用户体验改进。

### 主要更新内容

#### 1. 移动端响应式设计 ✨

**新增功能:**
- 完全响应式布局,支持手机、平板和桌面设备
- 移动端侧边栏抽屉菜单,优化小屏幕体验
- 触摸友好的交互设计
- 自适应字体大小和按钮尺寸

**使用方法:**
- 在移动设备上访问应用
- 点击左上角菜单图标切换 Persona 列表
- 点击右上角大脑图标查看记忆库

#### 2. 数据库持久化存储 💾

**新增功能:**
- SQLite 数据库集成,数据永久保存
- 自动数据迁移和备份
- 支持聊天历史持久化
- 记忆数据库化存储

**文件说明:**
- `database.py` - 数据库管理模块
- `memory_data.db` - SQLite 数据库文件（自动创建）

**数据表结构:**
- `personas` - Persona 信息
- `chat_sessions` - 聊天历史记录
- `memories` - 记忆数据

#### 3. 增强的记忆管理 🧠

**新增功能:**
- **编辑记忆**: 点击记忆卡片上的编辑按钮修改内容
- **删除记忆**: 点击删除按钮移除不需要的记忆
- **高级搜索**: 在记忆库中搜索关键词
- **类型筛选**: 按"全部"、"公共"、"私有"筛选记忆
- **实时更新**: 记忆列表自动刷新

**使用方法:**
1. 在右侧记忆库面板输入搜索关键词
2. 使用筛选按钮切换记忆类型
3. 点击编辑图标修改记忆内容
4. 点击删除图标移除记忆（需确认）

#### 4. 多 API 支持 🔌

**新增功能:**
- 支持多种 AI 服务提供商
- 统一的 API 接口管理
- 灵活的模型切换

**支持的 API:**
- ✅ LongCat API（默认）
- ✅ OpenAI API
- ✅ Anthropic Claude API
- ✅ 本地 Ollama
- ✅ 自定义 OpenAI 兼容 API

**配置方法:**
在 `.env` 文件中添加对应的 API Key:

```bash
# LongCat API
LONGCAT_API_KEY=your_longcat_key

# OpenAI API
OPENAI_API_KEY=your_openai_key

# Anthropic API
ANTHROPIC_API_KEY=your_anthropic_key

# 自定义 API
CUSTOM_API_BASE_URL=http://your-api-url
CUSTOM_API_KEY=your_custom_key
```

#### 5. 优化的流式输出 ⚡

**改进内容:**
- 更稳定的流式响应处理
- 更好的错误处理和重试机制
- 实时打字效果
- 响应状态显示

### 文件结构变化

#### 新增文件

```
memory-summary/
├── database.py                      # 数据库管理模块
├── api_config.py                    # API 配置管理
├── src/
│   ├── MorandiAnnotationApp_v2.jsx # 响应式前端组件
│   └── utils/
│       └── memory_manager_v2.py    # 增强版记忆管理器
├── server_v2.py                     # 增强版后端服务器
├── UPGRADE_GUIDE.md                 # 本文档
└── IMPROVEMENT_PLAN.md              # 改进方案文档
```

#### 保留的原始文件

原始文件已保留,新版本使用 `_v2` 后缀:
- `server.py` → `server_v2.py`
- `src/MorandiAnnotationApp.jsx` → `src/MorandiAnnotationApp_v2.jsx`
- `src/utils/memory_manager.py` → `src/utils/memory_manager_v2.py`

### 升级步骤

#### 方式一: 使用新版本（推荐）

1. **更新主入口文件**

编辑 `src/main.jsx`:

```javascript
import MorandiAnnotationApp from './MorandiAnnotationApp_v2'
```

2. **更新 package.json 脚本**

```json
{
  "scripts": {
    "server": "python3 server_v2.py",
    "dev:all": "concurrently \"npm run server\" \"npm run dev\""
  }
}
```

3. **安装 Python 依赖**

```bash
pip3 install flask flask-cors python-dotenv requests
```

4. **启动应用**

```bash
npm run dev:all
```

#### 方式二: 逐步迁移

1. 先测试新功能,保留原版本运行
2. 确认无误后再切换到新版本
3. 可以同时运行两个版本对比

### 数据迁移

#### 从内存存储迁移到数据库

新版本会自动创建数据库,无需手动迁移。首次启动时:

1. 数据库自动初始化
2. 创建默认 Personas
3. 后续的聊天和记忆会自动保存到数据库

#### 导入旧数据

如果有导出的 JSON 数据:

```python
from database import get_db

db = get_db()
with open('old_data.json', 'r') as f:
    data = json.load(f)
    db.import_data(data)
```

### API 变更

#### 新增 API 端点

**记忆管理:**
- `PUT /memories/<memory_id>` - 更新记忆
- `DELETE /memories/<memory_id>` - 删除记忆

**Persona 管理:**
- `POST /personas` - 创建新 Persona

#### 修改的 API

**`GET /memories-live/<persona_id>`**
- 新增查询参数: `?query=搜索关键词`
- 支持语义搜索

### 配置说明

#### 环境变量

新增环境变量（可选）:

```bash
# API 超时时间（毫秒）
LONGCAT_API_TIMEOUT_MS=30000

# 自定义 API 配置
CUSTOM_API_BASE_URL=http://localhost:8000
CUSTOM_API_KEY=your_key
```

#### 数据库配置

数据库文件默认位置: `./memory_data.db`

如需修改,编辑 `database.py`:

```python
DB_PATH = Path('/your/custom/path/memory_data.db')
```

### 性能优化

#### 记忆缓存

新版本使用内存缓存 + 数据库持久化:
- 快速访问常用记忆
- 自动同步到数据库
- 缓存超时时间: 60 秒

#### 权重衰减

自动权重衰减机制:
- 每小时自动执行
- 衰减因子: 0.95
- 自动删除低权重记忆（< 0.1）

### 故障排除

#### 数据库锁定错误

如果遇到 "database is locked" 错误:

```bash
# 停止所有服务
pkill -f server_v2.py

# 删除锁文件
rm memory_data.db-journal

# 重新启动
npm run server
```

#### API 连接失败

检查 API Key 配置:

```bash
# 查看环境变量
echo $LONGCAT_API_KEY

# 测试 API 配置
python3 api_config.py
```

#### 前端无法连接后端

确认后端服务运行:

```bash
# 检查端口 3001
lsof -i :3001

# 查看后端日志
tail -f server.log
```

### 回退到旧版本

如果需要回退:

1. **恢复原始文件引用**

编辑 `src/main.jsx`:

```javascript
import MorandiAnnotationApp from './MorandiAnnotationApp'
```

2. **使用旧版服务器**

```json
{
  "scripts": {
    "server": "python3 server.py"
  }
}
```

3. **重启应用**

```bash
npm run dev:all
```

### 后续计划

未来版本将包含:
- 记忆可视化图表
- 知识图谱展示
- 更多 AI 模型支持
- 多用户支持
- 云端同步

### 获取帮助

如遇问题,请查看:
- `README.md` - 基本使用说明
- `IMPROVEMENT_PLAN.md` - 详细改进方案
- GitHub Issues - 提交问题和建议

---

**版本**: 2.0.0  
**更新日期**: 2024-12  
**兼容性**: 向后兼容 1.x 版本
