// server.js
// ==========================================
// LongCat Chat Server 启动入口
// 环境变量配置 + 本地服务运行
// ==========================================

import express from "express";
import dotenv from "dotenv";
import cors from "cors";
import fetch from "node-fetch"; // 若使用 Node18 可省略安装

// ========== 1. 初始化环境变量 ==========
dotenv.config();

const app = express();
const PORT = 3001;

// ========== 2. 读取并校验环境变量 ==========
const LONGCAT_API_KEY = process.env.LONGCAT_API_KEY;

if (!LONGCAT_API_KEY) {
  console.warn(`
⚠️  警告：LONGCAT_API_KEY 未设置！
请创建 .env 文件并添加以下内容：

LONGCAT_API_KEY=your_api_key_here

或者使用命令设置环境变量：
Linux/Mac:
  export LONGCAT_API_KEY=your_api_key_here
Windows:
  set LONGCAT_API_KEY=your_api_key_here
`);
}

// ========== 3. Express 基础配置 ==========
app.use(cors());
app.use(express.json());

// ========== 4. 路由：测试接口 ==========
app.get("/", (req, res) => {
  res.send("✅ LongCat Chat Server 正在运行于 http://localhost:3001");
});

// ========== 5. 路由：代理 LongCat Chat API ==========
app.post("/api/chat", async (req, res) => {
  const { messages, model = "LongCat-Flash-Chat" } = req.body;

  if (!LONGCAT_API_KEY) {
    return res.status(400).json({ error: "缺少 LONGCAT_API_KEY，请先配置环境变量。" });
  }

  if (!messages || !Array.isArray(messages)) {
    return res.status(400).json({ error: "请求体缺少有效的 messages 数组。" });
  }

  try {
    const response = await fetch("https://api.longcat.chat/openai", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${LONGCAT_API_KEY}`,
      },
      body: JSON.stringify({
        model,
        messages,
        stream: false,
      }),
    });

    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error("❌ 调用 LongCat API 出错：", error);
    res.status(500).json({ error: "服务器内部错误，请检查 API 调用或网络连接。" });
  }
});

// ========== 6. 启动服务器 ==========
app.listen(PORT, () => {
  console.log(`🚀 服务器运行在 http://localhost:${PORT}`);
  if (!LONGCAT_API_KEY) {
    console.log("⚠️  当前未设置 LONGCAT_API_KEY，API 调用将失败。");
  }
});
