# TextRoom 全流程通关视频 · 录制脚本

真实浏览器 UI 驱动的自动通关录屏 SOP。产物：`videos/textroom_full_playthrough.webm`（约 2 分 10 秒 / 12.5MB）。

驱动脚本：`scripts/record_playthrough.py`（本文是它的操作说明书，改动 UI 后按本文校准即可重录）。

---

## 0. 前置条件

| 项 | 要求 | 当前状态 |
|---|---|---|
| 项目虚拟环境 | `.venv`（含 playwright） | 已装 |
| 浏览器 | Chromium → `.pw-browsers/`（**必须 D 盘**，禁 C 盘） | 已装 chromium-1234 |
| 环境量 | `PLAYWRIGHT_BROWSERS_PATH` 指向项目 `.pw-browsers` | 需每次显式设置 |
| 后端服务 | `http://127.0.0.1:8000` 在跑 | 录制前必须确认 |
| 视频编码器 | 无需系统 ffmpeg，Playwright 自带 record_video | OK |

启动/确认后端（**必须用受管后台任务，不能用 `&` 放到普通 bash**）：

```bash
# 受管后台任务方式（推荐）
cd D:/A-work/WorkBuddy/TextRoom
.venv/Scripts/python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# 确认端口在监听
netstat -ano | grep ":8000" | grep LISTENING
```

---

## 1. 安装（仅首次）

```bash
cd D:/A-work/WorkBuddy/TextRoom
.venv/Scripts/python.exe -m pip install playwright

export PLAYWRIGHT_BROWSERS_PATH="D:/A-work/WorkBuddy/TextRoom/.pw-browsers"
.venv/Scripts/python.exe -m playwright install chromium
```

探针验证（避免录到一半才炸）：

```bash
export PLAYWRIGHT_BROWSERS_PATH="D:/A-work/WorkBuddy/TextRoom/.pw-browsers"
.venv/Scripts/python.exe -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={'width':1280,'height':800})
    pg.goto('http://127.0.0.1:8000'); pg.wait_for_timeout(800)
    pg.screenshot(path='assets/prompts/_pw_probe.png'); b.close()
print('LAUNCH OK')
"
```

---

## 2. 一键录制

```bash
cd D:/A-work/WorkBuddy/TextRoom
export PLAYWRIGHT_BROWSERS_PATH="D:/A-work/WorkBuddy/TextRoom/.pw-browsers"
.venv/Scripts/python.exe scripts/record_playthrough.py textroom_full_playthrough.webm
```

- 可选参数：输出文件名（默认 `textroom_full_playthrough.webm`）
- 录制过程中视频落在 `videos/_rec/`，脚本结束时自动重命名为目标文件并清理临时目录
- **全程约 2-4 分钟，务必用后台任务跑**（`run_in_background`），前台易超时

---

## 3. 分镜脚本（共 3 关，40 步）

图例：`等待`＝操作后的画面停留秒数（也是节奏可控点）。

### 序幕 · 开局（约 8.5s）

| # | 操作 | 画面 / 旁白 | 等待 |
|---|---|---|---|
| 0 | `goto` 首页 → `wait_for_selector("#cover-btn")` | **开始游戏界面完整入镜**（此前一闪而过） | **3.0s** `COVER_HOLD` |
| 0.5 | 点击「开始游戏」 | 淡入书房全景 | — |
| 0.6 | 不点击、不滚动，纯停留 | **第 1 关全景扫视**（别一上来就点热点） | **2.5s** `ROOM_HOLD` |

> **节奏参数**集中在脚本顶部：`COVER_HOLD = 3.0`（封面）、`ROOM_HOLD = 2.5`（每关开场与跨关后）。嫌慢或嫌快改这两个数即可，不用动流程。
> 同理，第 2、3 关进入后各自动获得一次 `ROOM_HOLD` 全景停留（`cross_room()` 内置）。

### 第 1 关 · 书房（约 45s）

> 铁律：**先拿线索，再输密码**。密码必须在它的线索到手之后才出现，否则流程演示失去说服力。

| # | 操作 | 画面 / 旁白 | 等待 |
|---|---|---|---|
| 1 | 热点 `bookshelf` →「拾取 半把钥匙①」→「查看 旧书」 | 旧书里夹的铅笔字：「另一半在画框之后」 | 1.6s |
| 2 | 返回 → 热点 `picture_frame` →「掀开画框」→「拾取 半把钥匙②」 | 画框背面暗格 | 1.6s |
| 3 | 返回 → 背包 `key_half_a` →「组合」→「与 半把钥匙② 组合」 | 完整钥匙合成 | 1.0s |
| 4 | 热点 `desk` → 背包 `key_full` →「使用」 | 抽屉咔哒弹开 | 1.0s |
| 5 | 「拾取 密码纸」「拾取 齿轮」→ 背包查看密码纸 | 「第三位 — 7」+ 背面「三位数」 | 1.6s |
| 6 | 返回 → 热点 `clock` → 背包 `gear` →「使用」 | 时钟重新走动：**时针 3、分针 9** | 1.8s |
| 7 | 返回 → 热点 `safe` →「输入密码」→ **111** | **错误反馈**（此时线索已齐） | 1.2s |
| 8 | 再「输入密码」→ **397**（3-9-7 线索拼合） | 咔嗒开启 | 1.2s |
| 9 | 「拾取 书房门钥匙」 | 钥匙入包、线索入栏 | 0.7s |
| 10 | 返回 → 热点 `door` → 背包 `study_key` →「使用」 | **白底黑字衔接页：第 2 关 · 客厅** | — |
| 11 | `cross_room`：等 `state.room == living_room` → 点衔接页任意位置 | 淡出进入客厅 | 2.6 + 1.2s |

### 第 2 关 · 客厅（约 45s）

| # | 操作 | 画面 / 旁白 | 等待 |
|---|---|---|---|
| 14 | 热点 `coffee_table` →「拾取 外卖小票」「拾取 鱼食」 | 茶几特写 | 1.6s |
| 15 | 背包 `receipt_note` →「查看」 | 小票上的顺序线索 | 1.6s |
| 16 | 返回 → 热点 `fridge` →「揭下冰箱贴」→「拾取 冰箱贴」 | 冰箱磁贴 | 1.3s |
| 17 | 背包 `fridge_magnet` →「查看」 | 冰箱贴内容 | 1.3s |
| 18 | 返回 → 热点 `sofa` →「拾取 晾衣杆」 | 沙发缝里抽出长杆 | 0.7s |
| 19 | 返回 → 热点 `wall_clock` → 背包 `drying_pole` →「使用」 | 挂钟被挑落 | 1.0s |
| 20 | 「拾取 挂钟背板」→ 背包查看 | 背板暗格内容 | 1.3s |
| 21 | 返回 → 热点 `tv_cabinet` →「拾取 相册」→ 查看 | 相册线索 | 1.3s |
| 22 | 返回 → 热点 `fish_tank` → 背包 `fish_food` →「使用」 | 撒食 → 数出 **8 条鱼** | 1.6s |
| 23 | 返回 → 热点 `garage_door` →「输入密码」→ **3728** | 密码盘亮绿 | 1.2s |
| 24 | `cross_room`：等 `room == garage` → 点衔接页 | **第 3 关 · 车库** | 2.6 + 1.2s |

### 第 3 关 · 车库（约 60s）

> 同第 1 关：必须先从工具箱纸条拿到 **529**，电子屏密码才登场。

| # | 操作 | 画面 / 旁白 | 等待 |
|---|---|---|---|
| 25 | 热点 `remote` → 看一眼 → 返回 | 外壳开裂、电池仓空的坏遥控器 | 1.3s |
| 26 | 热点 `car` →「查看 褪色贴纸」 | 引擎盖内侧：旋钮停在**刻度 6** | 1.6s |
| 27 | 返回 → 热点 `tool_board` →「向右旋转」×6 | 刻度盘 0→6，铁皮盒弹开 | 0.55×6 |
| 28 | 「拾取 旧钥匙」 | 老式铜钥匙 | 0.7s |
| 29 | 返回 → 热点 `tool_box` → 背包 `old_key` →「使用」 | 挂锁啪地弹开 | 1.0s |
| 30 | 「拾取 纸条」→ 背包查看 | 油笔写着 **「5 2 9」** ← 密码线索 | 1.6s |
| 31 | 返回 → 热点 `keypad` →「输入密码」→ **111** | **错误反馈**（线索在手后演示） | 1.2s |
| 32 | 再「输入密码」→ **529** | 玻璃面板弹开、露出箭头键 | 1.4s |
| 33 | 「查看电子屏（上下箭头）」→ 点 **⬇** | 「没有任何动静」 | 1.4s |
| 34 | 再开箭头弹窗 → 点 **⬆** | **卷帘门缓缓升起** | 1.0s |
| 35 | 返回 → 热点 `exit_door` →「走出卷帘门」 | — | 1.8s |
| 36 | 等 `state.finished == True` | **白底通关结算**（用时/探索处数/步数） | **6.0s**（收尾留白） |

### 收尾

| # | 操作 | 说明 |
|---|---|---|
| 37 | `ctx.close()` → `browser.close()` | 必须关 context 视频才落盘 |
| 38 | 取 `_rec/` 里最新的 `.webm` 重命名为目标文件 | 脚本自动完成 |
| 39 | `shutil.rmtree(videos/_rec)` | 清理临时目录 |

---

## 4. DOM 契约（改 UI 后必须对齐）

| 用途 | 选择器 | 说明 |
|---|---|---|
| 开始按钮 | `#cover-btn` | 首页遮罩里的开始 |
| 场景热点 | `.hotspot[data-id="<对象id>"]` | 全景上的可点标记 |
| 返回按钮 | `#closeupClose` | 特写弹窗右上角 |
| 动作按钮 | `#closeupActs .act-btn` | 拾取/查看/输入密码/互动… |
| 菜单/目标按钮 | `.act-btn`（全局，取最后一个可见层） | 背包菜单与目标选择列表 |
| 背包物品 | `.inv-item[data-id="<物品id>"]` | 右侧背包栏 |
| 密码键 | `.pad-key[data-k="0-9/OK"]` | 数字键盘 |
| 箭头键 | `body .act-btn`（文本 ⬆ / ⬇） | 电子屏弹窗 |
| 关卡衔接页 | `#levelGate` | 白底黑字过渡页 |
| 状态读取 | `evaluate(() => lastData.state…)` | **见坑 1** |

状态字段：`room / level / progress / inventory / clues / finished / dial_position / shutter_opened`
场景字段：`mode / object_id / items[] / needs_interaction / needs_password / needs_dial`

---

## 5. 三个已知坑（必读）

**坑 1 · `let` 不挂 window**
页面顶层是 `let lastData`，属于词法绑定，**不会挂到 `window`**。`page.evaluate("() => window.lastData")` 恒为空 → 脚本误判"开局失败"。
正确写法：`typeof lastData !== 'undefined' ? lastData : null`（裸标识符）。

**坑 2 · 跨关是异步的**
`use(study_key, door)` / `enter_password(3728)` 返回后房间尚未切换，此时衔接页还没出现。若直接 `see()` 会读到旧房间，随后衔接页迟到并遮挡后续点击。
正确写法：`cross_room()` 先轮询 `state.room == 目标房间`，再 `wait_for #levelGate visible` → 停留 → `click(force=True)`。

**坑 3 · 后台进程被 shell 带走**
bash 里 `uvicorn ... &` 会随 shell 退出被杀，**日志干净无报错但端口消失**，冒烟/录制瞬间全挂。
正确写法：用受管后台任务（`run_in_background`）启动服务与录制。

**附带修复（录制时发现的产品 bug）**：LLM 润色旁白带 Markdown `**` 星号残留 → 前端 `cleanNarr()` 统一清理旁白 / 反馈区 / 描述 / 通关文案。改 LLM 输出或换模型后需复查此点。

---

## 6. 失败排查清单

| 症状 | 原因 | 处理 |
|---|---|---|
| `LAUNCH OK` 都通不过 | Chromium 未装 / 路径错 | 检查 `.pw-browsers` 与 `PLAYWRIGHT_BROWSERS_PATH` |
| 第一步就报「等待超时: 拿到 state」 | 坑 1 或后端未启动 | 先 `curl /api/start` 确认接口通 |
| 卡在客厅/车库入口 | 坑 2 衔接页遮挡 | 确认用 `cross_room` 而非 `see` + `dismiss_gate` |
| 全部请求空响应 | 坑 3 服务被杀 | 受管后台任务重启 uvicorn |
| 找不到动作按钮 xxx | 按钮文案改过 | 对照第 4 节选择器与 `click_act` 的文本子串 |
| 视频 0 字节 | 未 `ctx.close()` | 录制必须关闭 context 才落盘 |

---

## 7. 收尾质检

抽帧检查（自带 ffmpeg 在 `.pw-browsers/ffmpeg-1011/ffmpeg-win64.exe`）：

```bash
cd D:/A-work/WorkBuddy/TextRoom
FF=.pw-browsers/ffmpeg-1011/ffmpeg-win64.exe
"$FF" -y -ss 40 -i videos/textroom_full_playthrough.webm -frames:v 1 -q:v 3 assets/prompts/_chk40.png
```

建议抽查时间点：**8s（开局）、40s（跨关衔接页）、75s（是否出现 `**` 星号）、结算前 5s（通关页）**。

> 格式说明：自带 ffmpeg 是精简版，**只有 vp8/webv，没有 h264/mp4 muxer**，无法本地转 mp4。webm 可被 Chrome/Edge/Firefox/Safari 原生播放，也可用 `<video src="...webm">` 直接嵌入网页。确需 mp4 时在 D 盘装完整版 ffmpeg 再转。
