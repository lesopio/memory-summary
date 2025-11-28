# 设置 LongCat API Key

## 问题
如果看到以下错误：
```
API调用失败: 401 - {"error":{"code":"invalid_api_key","message":"missing_api_key"}}
```

这说明 LongCat API Key 未设置或设置不正确。

## 解决方案

### 方法 1：使用 .env 文件（推荐）

1. 在项目根目录创建 `.env` 文件
2. 添加以下内容：

```env
LONGCAT_API_KEY=your_actual_api_key_here
```

3. 将 `your_actual_api_key_here` 替换为您的实际 API Key
4. 重启服务器

### 方法 2：使用环境变量

#### Windows (PowerShell) - Node.js 后端
```powershell
$env:LONGCAT_API_KEY="your_actual_api_key_here"
npm run server
```

#### Windows (PowerShell) - Python 后端
```powershell
$env:LONGCAT_API_KEY="your_actual_api_key_here"
python server.py
```

#### Windows (CMD) - Node.js 后端
```cmd
set LONGCAT_API_KEY=your_actual_api_key_here
npm run server
```

#### Windows (CMD) - Python 后端
```cmd
set LONGCAT_API_KEY=your_actual_api_key_here
python server.py
```

#### Linux/Mac - Node.js 后端
```bash
export LONGCAT_API_KEY="your_actual_api_key_here"
npm run server
```

#### Linux/Mac - Python 后端
```bash
export LONGCAT_API_KEY="your_actual_api_key_here"
python3 server.py
```

### 方法 3：在 package.json 中设置（不推荐）

修改 `package.json` 中的 scripts：
```json
{
  "scripts": {
    "server": "cross-env LONGCAT_API_KEY=your_key node server.js"
  }
}
```

## 获取 API Key

1. 访问 LongCat API 网站
2. 注册/登录账户
3. 在控制台获取您的 API Key
4. 将 API Key 复制到 `.env` 文件或环境变量中

## 验证设置

启动服务器后，您应该看到：
```
✅ API Key 已设置
```

如果看到：
```
⚠️  警告：LONGCAT_API_KEY 未设置！
```

说明 API Key 仍未正确设置，请按照上述方法重新设置。

## 注意事项

- `.env` 文件已添加到 `.gitignore`，不会被提交到版本控制
- 不要将 API Key 提交到 Git 仓库
- 如果 API Key 泄露，请立即在 LongCat 控制台重新生成

