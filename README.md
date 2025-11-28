# Morandi配色长期语义记忆系统
![02ad890fde5795aa7068eab8ddbd23e2](https://github.com/user-attachments/assets/66d83127-0368-4c1f-96c0-e1ec4e0b6e0d)

一个支持大模型长期语义记忆的智能对话系统，具有自动记忆摘要生成、向量化存储、语义检索和权重衰减机制。还有好看的配色。

## 功能特性

### 核心功能

- **长期语义记忆**：每轮对话结束后自动生成记忆摘要
- **向量化存储与检索**：基于余弦相似度的语义记忆检索
- **多角色记忆库**：每个角色拥有独立记忆 + 公共记忆
- **权重衰减机制**：定期合并旧记忆与新记忆，使用权重衰减
- **雾霾蓝与莫兰迪绿主题**：优雅的 UI 设计
- **模型切换**：支持 LongCat-Flash-Chat 和 LongCat-Flash-Thinking 模型

### 记忆系统

1. **自动记忆生成**：每轮对话结束后自动生成记忆摘要
2. **向量化存储**：使用词频向量化和余弦相似度进行语义检索
3. **记忆检索**：在新对话开始时检索最相关的记忆并注入上下文
4. **权重管理**：记忆访问时权重增加，定期应用权重衰减
5. **记忆合并**：定期合并相似记忆，避免冗余

## 技术栈

- **前端**：React + Vite + Tailwind CSS + Framer Motion
- **后端**：Node.js + Express
- **AI API**：LongCat API (OpenAI 兼容格式)
- **记忆系统**：自定义向量化记忆管理器
- **UI 组件**：自定义 UI 组件库

## 安装和运行

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# LongCat API Configuration
LONGCAT_API_KEY=your_api_key_here

# Server Configuration
PORT=3001
```

### 3. 启动开发服务器

#### 方式一：同时启动（推荐）

```bash
npm run dev:all
```

#### 方式二：分别启动

```bash
# 终端 1：启动后端服务器
npm run server

# 终端 2：启动前端开发服务器
npm run dev
```

### 4. 访问应用

- 前端地址：http://localhost:5173
- 后端 API：http://localhost:3001

## 项目结构

```
├── src/
│   ├── components/
│   │   └── ui/              # UI 组件（Button, Card, Input）
│   ├── utils/
│   │   └── memoryManager.js # 记忆管理系统
│   ├── MorandiAnnotationApp.jsx  # 主应用组件
│   ├── main.jsx             # 入口文件
│   └── index.css            # 全局样式
├── server.js                # 后端服务器
├── vite.config.js           # Vite 配置
├── tailwind.config.js       # Tailwind 配置（自定义颜色主题）
└── package.json             # 项目配置
```

## API 接口

### Persona 管理

- `GET /personas` - 获取所有 Persona 列表
- `POST /switch-model` - 切换模型（Flash-Chat / Flash-Thinking）

### 聊天接口

- `POST /chat` - 发送聊天消息（流式响应）
  - 请求体：`{ persona: number, message: string, model?: string }`
  - 自动检索相关记忆并注入上下文
  - 对话结束后自动生成记忆摘要

### 记忆管理

- `GET /memories/:personaId` - 获取指定角色的所有记忆
- `GET /memories-live/:personaId` - 获取实时记忆（用于前端显示）
  - 查询参数：`?query=搜索关键词`（可选）
- `POST /memories` - 手动添加记忆
  - 请求体：`{ personaId: number, content: string, isPublic?: boolean }`

### 数据导出

- `GET /export` - 导出所有数据（JSON 格式）
  - 包含：personas、chatSessions、memories、publicMemories

## 使用说明

### 基本使用

1. **选择 Persona**：在左侧列表中选择一个 Persona
2. **选择模型**：在左侧模型选择区域切换模型
   - **Flash-Chat**：高性能通用对话模型
   - **Flash-Thinking**：深度思考模型
3. **开始对话**：在中间区域输入消息并发送
   - AI 会自动检索相关记忆并注入上下文
   - 响应以流式方式实时显示
4. **查看记忆**：在右侧记忆库查看实时记忆
   - 显示角色记忆和公共记忆
   - 显示记忆相关度和时间戳
   - 自动刷新（每5秒）

### 记忆系统工作原理

1. **对话时**：
   - 系统检索与当前消息最相关的记忆（最多3条）
   - 将记忆注入系统提示词中
   - AI 基于记忆和上下文生成响应

2. **对话后**：
   - 自动生成对话摘要（1-2句话）
   - 判断是否为公共记忆（包含"通用"、"公共"等关键词）
   - 将摘要向量化并存储到记忆库

3. **记忆管理**：
   - 记忆被访问时权重增加
   - 每小时自动应用权重衰减（衰减因子：0.95）
   - 每20轮对话自动合并相似记忆（相似度阈值：0.8）
   - 权重低于0.1的记忆自动删除

## 颜色主题

### 雾霾蓝 (Haze Blue)
- 主色：`#486581` (haze-blue-600)
- 背景：`#f0f4f8` (haze-blue-50)
- 用于：主要 UI 元素、聊天消息、按钮

### 莫兰迪绿 (Morandi Green)
- 主色：`#3d6654` (morandi-green-600)
- 背景：`#f0f5f3` (morandi-green-50)
- 用于：侧边栏、记忆卡片、辅助元素

## LongCat API 配置

### API 端点
- 基础 URL：`https://api.longcat.chat/openai`
- 聊天补全：`/v1/chat/completions`

### 支持的模型
- `LongCat-Flash-Chat`：高性能通用对话模型
- `LongCat-Flash-Thinking`：深度思考模型

### 环境变量
在 `.env` 文件中设置 `LONGCAT_API_KEY`。

## 开发计划

- [x] 集成 LongCat API
- [x] 实现记忆摘要生成
- [x] 实现向量化存储和检索
- [x] 实现权重衰减机制
- [x] 支持多角色记忆库
- [x] 更新 UI 主题
- [x] 添加模型切换功能
- [ ] 集成专业向量数据库（如 Pinecone、Weaviate）
- [ ] 添加数据库持久化存储
- [ ] 支持记忆编辑和删除
- [ ] 添加记忆搜索功能
- [ ] 优化记忆摘要生成质量
- [ ] 添加记忆可视化图表

## 注意事项

- 确保后端服务器在端口 3001 运行
- 前端开发服务器运行在端口 5173
- Vite 配置了代理，会自动将 API 请求转发到后端
- 记忆系统使用内存存储，重启服务器后记忆会丢失（计划添加持久化）
- 当前使用简单的词频向量化，生产环境建议使用专业向量数据库

## 许可证

MIT License
