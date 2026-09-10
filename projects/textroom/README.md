# TextRoom · AI 文字密室逃脱

由大模型担任"游戏主持人"的文字密室逃脱。玩家在三关场景中以文字指令探索、解谜、逃生。
个人独立完成。

## 玩法

- **三关场景**：旧书房 → 客厅 → 车库，逐关解锁
- **文字交互**：玩家输入自然语言指令（查看 / 拾取 / 使用 / 组合等）
- **AI 主持人**：大模型理解玩家意图，返回场景旁白、线索与状态变更
- **状态机**：可交互物、道具、锁具与密码门由后端状态机统一管理

## 技术栈

| 层 | 说明 |
|---|---|
| 后端 | FastAPI + Pydantic（接口定义与数据校验） |
| 大模型 | DeepSeek，OpenAI 兼容协议 + Function Calling 结构化输出 |
| 前端 | 原生 JavaScript 单文件（无框架、无构建步骤） |
| 美术 | AI 生成的场景全景图与特写图 |
| 测试 | Playwright 冒烟测试脚本 |

## 设计要点

- **不依赖第三方 LLM SDK**：使用 Python 标准库 `urllib` 直连 HTTP 接口，减少依赖面（见 `backend/llm.py`）
- **密钥仅从环境变量 / `.env` 读取**，不接收参数传入、不打印到日志
- **状态与提示词分离**：`state.py`（房间 / 道具 / 状态机）、`prompts.py`（系统提示词与工具定义）、`actions.py`（动作处理）
- **失败降级**：未配置密钥时服务仍可启动，AI 旁白降级为占位文本

## 目录结构

```
textroom/
├── backend/              # FastAPI 服务
│   ├── main.py             # 接口与静态资源
│   ├── llm.py              # DeepSeek 客户端（标准库实现）
│   ├── state.py            # 房间、道具与游戏状态机
│   ├── prompts.py          # 系统提示词、Function Calling 工具定义
│   └── actions.py          # 玩家动作处理
├── frontend/index.html   # 前端（单文件原生 JS）
├── assets/               # 场景图（study / living_room / garage）
├── scripts/              # 录屏与截图脚本
├── smoke_*.py            # 冒烟测试
└── scene_map.json        # 场景映射
```

## 运行

1. 安装依赖

   ```bash
   pip install -r requirements.txt
   ```

2. 配置密钥：复制 `.env.example` 为 `.env`，填入 `DEEPSEEK_API_KEY`

3. 启动服务

   ```bash
   uvicorn backend.main:app --reload
   ```

4. 浏览器打开 `http://127.0.0.1:8000`

> 未配置密钥时仍可启动，AI 旁白会降级为占位文本；配置后即可完整游玩。
