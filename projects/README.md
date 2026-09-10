# 作品集 · 项目源码

本仓库既是作品集网站本体（`index.html` + `assets/`），也是配套项目源码的存放处。

## 项目索引

| 编号 | 项目 | 技术栈 | 源码目录 |
|---|---|---|---|
| 01 | 小智 · 儿童 AI 聊天机器人 | Python · Flask · 大模型 API · 内容安全过滤 | [`xiaozhi/`](./xiaozhi) |
| 02 | TextRoom · AI 文字密室逃脱 | FastAPI · Pydantic · DeepSeek Function Calling · 原生 JS | [`textroom/`](./textroom) |
| 04 | 医道求真 · 中医卡牌合成游戏 | Unity 2022.3 · C# | [`doctor/`](./doctor) |

另有 **03 文物数字展 · 弩射**（团队项目，源码未留存）与 **05 星眠 APP**（设计稿）
两个作品，详情见在线作品集网站。

## 目录说明

```
.
├── index.html        # 作品集网站（部署入口）
├── assets/
│   ├── videos/       # 各项目演示视频
│   └── shots/        # 各项目截图
└── projects/         # 项目源码
    ├── xiaozhi/      # 01 小智
    ├── textroom/     # 02 TextRoom
    └── doctor/       # 04 医道求真
```

各项目目录下均有独立 README，说明功能、技术栈、目录结构与运行方式。

## 说明

- 仓库中所有 API 密钥均通过**环境变量**读取，不含任何明文密钥
- 已排除运行环境与自动生成目录（`.venv/`、`Library/`、`__pycache__/` 等）
