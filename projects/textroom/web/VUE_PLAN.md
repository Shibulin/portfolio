# TextRoom 前端 Vue 重写 · 实施文档

> 目标：把 `frontend/index.html`（747 行原生单文件）重写为 **Vue 3 + Vite + Pinia** 组件化前端。
> 硬底线：**界面、布局、交互与原版几乎完全一致**；后端逻辑不改。

---

## 一、基本原则

| 原则 | 说明 |
|---|---|
| 视觉零偏差 | CSS **原样搬运**，不改任何数值；组件不使用 `scoped` |
| DOM 契约不动 | 保留原 id / class，4 套冒烟与录屏脚本**零改动**即可跑通 |
| 原版冻结 | `frontend/index.html` 不再修改；出问题一键切回 |
| 两版共存 | 后端加一个开关，默认仍走原版，互不干扰 |

---

## 二、目录结构

```
TextRoom/
├── frontend/index.html       原版（冻结，回退点）
├── web/                      Vue 项目（新增）
│   ├── index.html            Vite 入口
│   ├── package.json          依赖清单
│   ├── vite.config.js        构建配置（assetsDir = static）
│   ├── .npmrc                缓存指向 D 盘
│   └── src/
│       ├── main.js           【待写】挂载 App + Pinia
│       ├── App.vue           【待写】组装 11 个组件
│       ├── api/index.js      ✅ 接口封装（4 个）
│       ├── store/game.js     ✅ Pinia 状态层
│       ├── constants/index.js✅ 热点坐标 / 图标 / 房间名
│       ├── styles/main.css   ✅ 原版样式 1:1 迁移
│       └── components/       【待写】11 个组件
└── backend/main.py           【待改】加前端切换开关
```

---

## 三、组件拆分（11 个）

| # | 组件 | 职责 | 必须保留的选择器 |
|---|---|---|---|
| 1 | `CoverScreen.vue` | 白底开始页 | `#cover-btn` |
| 2 | `SceneView.vue` | 场景底图 + 热点按钮 | `.hotspot[data-id]` |
| 3 | `HudBar.vue` | 关卡名 + 进度条 | — |
| 4 | `SidePanel.vue` | 背包 / 线索双栏 | `.inv-item[data-id]` |
| 5 | `NarrationBox.vue` | 底部旁白（留 4 条） | `#narration` |
| 6 | `CloseupModal.vue` | 特写弹窗 + 动作按钮 + 反馈区 | `#closeupClose` `#closeupActs .act-btn` `#closeupFeedback` |
| 7 | `PasswordPad.vue` | 密码盘 + 物理键盘 | `.pad-key[data-k]` |
| 8 | `ArrowModal.vue` | 电子屏 ⬆⬇ 弹层 | `.act-btn` |
| 9 | `ItemMenu.vue` | 物品菜单 + 目标选择 | `.act-btn` |
| 10 | `LevelGate.vue` | 关卡衔接页 | `#levelGate` |
| 11 | `WinScreen.vue` | 通关结算 | `#win-restart` |

---

## 四、实施步骤

每一步做完**停下来**，确认无误再进下一步。

| 步 | 做什么 | 验证方式 | 状态 |
|---|---|---|---|
| **1** | git 备份 + 建脚手架 + 装依赖 | 已完成 | ✅ |
| **2** | 写 `main.js`、`App.vue`，加 3 个纯展示组件（Cover / Hud / Narration） | `npm run build` 构建通过（25 modules） | ✅ |
| **3** | `SceneView` + `SidePanel` | 构建通过（27 modules） | ✅ |
| **4** | `CloseupModal` + `PasswordPad` | 构建通过（29 modules） | ✅ |
| **5** | `ArrowModal` + `ItemMenu` + `LevelGate` + `WinScreen` | 构建通过（33 modules），11 组件就位 | ✅ |
| **6** | 后端接入 + 回归 | **4 套冒烟全 PASS + 截图逐像素比对一致** | ✅ |

---

## 五、三条硬约束（不遵守会直接坏）

原版 CSS 已迁移过来，其中四条遮罩层规则把 `display` 写死了。写组件时必须按下面来：

| # | 规则 | 为什么 |
|---|---|---|
| 1 | `#modalMask` / `#pwdMask` / `#win-bg` / `#levelGate` **必须用 `:class="{ show: 条件 }"`** | CSS 里写死了 `display:none`，用 `v-if` 或 `v-show` **都显示不出来** |
| 2 | `#closeupFeedback` 的 `v-if` **挂在元素本身** | CSS 靠 `:empty` 隐藏，`v-if` 会留注释节点导致 `:empty` 失效、弹窗底部多出空隙 |
| 3 | 动作按钮里的**信息行用 `<div class="act-btn">`** | 原版是 div（不匹配 `:disabled` 伪类），改成 `<button disabled>` 会变暗，视觉不一致 |

> 对照：`#scene` / `#hud` / `#sidebar` / `#narration` 是**内联** `display:none`，这四个用 `v-show` 是安全的。别和第 1 条混。

---

## 六、后端接入（只改 1 处）

```python
# backend/main.py
@app.get("/")                     # TR_FRONTEND=vue 时返回 web/dist，否则返回原版
@app.get("/static/{path:path}")   # 新增：服务 dist/static/*
```

- `vite.config.js` 里 `assetsDir: 'static'`，避开后端已占用的 `/assets`（AI 场景图）
- `/api`、`/assets`、`/videos`、`/scene-map.json` **全部不变**

---

## 七、回退

```bash
git checkout v1-native -- .        # 切回原生 JS 基线
```

原版文件在整个过程中不被修改，`v1-native` 标签永久保留。

---

## 八、当前进度

**全部完成（6/6 步）**

| 项 | 内容 |
|---|---|
| git 备份 | commit `0cfce08` + 标签 `v1-native` |
| 依赖 | vue 3.5.42 / pinia 4.0.3 / vite 8.3.0 / @vitejs/plugin-vue 6.0.8 |
| 落盘位置 | `web/node_modules` 50MB、`.npm-cache` 143.7MB，**均在 D 盘** |
| 组件 | 11 个全部完成；构建 33 modules → 85.00 kB（gzip 33.30 kB） |
| 工具链实测 | `vite build` rc=0 |
| CSS 迁移核验 | 原版 156 非空行，`main.css` **0 条缺失** |
| **冒烟回归** | **4 套全 PASS**（smoke_study / smoke_study_locked / smoke_living_room / smoke_day4） |
| **UI 一致性** | 封面 / 全景 / 特写 / 侧栏 四张截图 **逐像素比对：三张 0 差异，第四张 0.28% 差异经查证为 LLM 旁白文案随机生成，非 UI 偏差** |
| 后端改动 | `main.py` 加 `TR_FRONTEND` 开关 + `/static/{path}` 路由；默认仍走原版 |

**用法**

```bash
# Vue 版
TR_FRONTEND=vue .venv/Scripts/python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# 原版（默认）
.venv/Scripts/python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
