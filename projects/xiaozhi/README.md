# 小智 · 儿童 AI 聊天机器人

面向 5–12 岁儿童的对话陪伴机器人。个人独立完成。

## 功能

- **对话陪伴**：通过大模型生成符合儿童语境的回复，主动提问延续对话
- **内容安全**：独立的分级敏感词库（`safety_words.py`），覆盖暴力、脏话等类别，
  配合系统提示词约束，对输入输出做双重拦截
- **角色约束**：系统提示词限定身份、语言风格、回复长度与知识边界
  —— 不确定的内容不编造，引导孩子一起查证

## 技术栈

| 项 | 说明 |
|---|---|
| 语言 | Python |
| Web 服务 | Flask |
| 模型接入 | OpenAI 兼容协议 · 阿里云百炼 DashScope |
| 内容安全 | 自建敏感词库 + 系统提示词约束 |

## 目录结构

```
xiaozhi/
├── child_ai/                # 主版本
│   ├── child_ai2.ipynb      # 主程序（Jupyter Notebook）
│   ├── config.py            # 模型与角色配置（密钥从环境变量读取）
│   └── safety_words.py      # 敏感词库
└── Chird_AI2.0/             # 早期版本
    ├── ChildAI-2 .ipynb
    ├── config.py
    └── safety_words.py
```

## 运行

1. 安装依赖

   ```bash
   pip install -r requirements.txt
   ```

2. 配置 API Key（不要写进代码）

   ```bash
   # Windows PowerShell
   $env:DASHSCOPE_API_KEY="你的Key"

   # macOS / Linux
   export DASHSCOPE_API_KEY="你的Key"
   ```

3. 打开 `child_ai/child_ai2.ipynb`，按顺序运行单元格

> **说明**：`config.py` 通过 `os.getenv("DASHSCOPE_API_KEY")` 读取密钥，
> 仓库中不含任何明文密钥。语音相关依赖（`torch`、`pyaudio`）体积较大，已标注为可选。
