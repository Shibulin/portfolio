# -*- coding: utf-8 -*-
"""
TextRoom — AI 密室逃脱主持 Agent
- 状态模型抽到 backend/state.py（Day 2）
- 动作路由抽到 backend/actions.py（Day 3）
- LLM 主持与函数调用接在 backend/llm.py（Day 4）
- 本文件只剩 HTTP 路由与"动作 → LLM 反应旁白"的串联
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from backend import actions
from backend.llm import get_client
from backend.prompts import SYSTEM_PROMPT, TOOLS
from backend.state import (
    GameState, new_state, scene_payload, reset_rooms, ITEMS,
)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
ASSETS_DIR = BASE_DIR / "assets"
VIDEOS_DIR = BASE_DIR / "videos"
SCENE_MAP_PATH = BASE_DIR / "scene_map.json"

app = FastAPI(title="TextRoom — AI 密室逃脱主持 Agent")

# 单局状态（演示用，Day 7 再做存档）
_state: GameState = new_state()

# LLM 客户端 + 调用计数
_llm = get_client()
_llm_call_count = 0          # 累计成功调用次数（用于演示展示）
_llm_attempt_count = 0       # 累计尝试次数（含失败）

# 默认旁白（LLM 不可用时使用）
DEFAULT_OPENING = (
    "你在一间旧书房里醒来。门锁着，窗户钉死了。"
    "桌上落满灰尘，墙上挂着一座老钟。"
    "找到出去的办法。"
)


# ============================================================ 辅助
def _inv_detail() -> list:
    return [
        {"id": iid, "name": ITEMS[iid].name, "icon": ITEMS[iid].icon}
        for iid in _state.inventory
    ]


def _state_summary(state: GameState) -> Dict[str, Any]:
    """喂给 LLM 的精简状态摘要（避免泄露全部数据）。"""
    return {
        "level": state.level,
        "room": state.room,
        "view": state.view,
        "current_closeup": state.current_closeup,
        "progress": state.progress,
        "inventory": [
            {"id": iid, "name": ITEMS[iid].name}
            for iid in state.inventory if iid in ITEMS
        ],
        "clue_count": len(state.clues),
        "clock_fixed": state.clock_fixed,
        "magnet_revealed": state.magnet_revealed,
        "wall_clock_lowered": state.wall_clock_lowered,
        "fish_fed": state.fish_fed,
        "tin_box_opened": state.tin_box_opened,
        "dial_position": state.dial_position,
        "padlock_unlocked": state.padlock_unlocked,
        "keypad_unlocked": state.keypad_unlocked,
        "shutter_opened": state.shutter_opened,
        "finished": state.finished,
    }


def _apply_gm_effects(state: GameState, gm: Dict[str, Any]) -> None:
    """把 LLM 通过 game_master 工具声明的状态变更落到 state 上。"""
    # 1) 新线索（追加）
    for clue in gm.get("clues") or []:
        if isinstance(clue, str) and clue.strip() and clue not in state.clues:
            state.clues.append(clue.strip())
    # 2) 标志位（白名单）
    flags = gm.get("flags") or {}
    if not isinstance(flags, dict):
        flags = {}
    if flags.get("clock_fixed") is True:
        state.clock_fixed = True
    # 第 2 关图片流程：冰箱贴 / 挂钟 / 鱼缸（LLM 在 hint 中可显式置位）
    if flags.get("magnet_revealed") is True:
        state.magnet_revealed = True
    if flags.get("wall_clock_lowered") is True:
        state.wall_clock_lowered = True
    if flags.get("fish_fed") is True:
        state.fish_fed = True
    # 第 3 关进度类标志（铁皮盒/挂锁）不进 LLM 白名单：它们与 turn_dial / use(旧钥匙)
    # 强绑定，AI 提前置位会让刻度盘 UI 消失、旧钥匙无处可用 → 死锁。
    # 通关类（keypad/shutter）同样只能由服务端密码校验与动作驱动，防止 AI 跳关
    # unlocked_objects 当前模型无对应字段 → 记日志，留待后续扩展
    unlocked = gm.get("unlocked_objects") or []
    if unlocked:
        print(f"[llm] AI 请求解锁对象: {unlocked}")


def _llm_call(system: str, user_msg: str, default_narration: str) -> str:
    """调一次 LLM；不可用/失败时返回 default_narration。"""
    global _llm_call_count, _llm_attempt_count
    if not _llm.enabled:
        return default_narration
    _llm_attempt_count += 1
    try:
        gm = _llm.game_master_call(system, user_msg, TOOLS, timeout=12.0)
    except Exception as e:
        print(f"[llm] 调用失败: {e}")
        return default_narration
    if not gm:
        return default_narration
    # 记一次成功调用
    _llm_call_count += 1
    # 把状态变更落到 state
    try:
        _apply_gm_effects(_state, gm)
    except Exception as e:
        print(f"[llm] 应用状态变更失败: {e}")
    narration = gm.get("narration") or default_narration
    return narration.strip() if isinstance(narration, str) else default_narration


def _llm_call_bg(
    background: BackgroundTasks,
    state: GameState,
    system: str,
    user_msg: str,
    default_narration: str,
) -> None:
    """把 LLM 调用扔到 BackgroundTasks 异步跑；结果写入 state.pending_narration。"""
    if not _llm.enabled:
        return

    def _run() -> None:
        global _llm_call_count, _llm_attempt_count
        _llm_attempt_count += 1
        try:
            gm = _llm.game_master_call(system, user_msg, TOOLS, timeout=12.0)
        except Exception as e:
            print(f"[llm] 后台调用失败: {e}")
            return
        if not gm:
            return
        _llm_call_count += 1
        try:
            _apply_gm_effects(state, gm)
        except Exception as e:
            print(f"[llm] 应用状态变更失败: {e}")
        narration = gm.get("narration") or default_narration
        if isinstance(narration, str) and narration.strip():
            state.pending_narration = narration.strip()

    background.add_task(_run)


# ============================================================ 页面与资源
@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/assets/{path:path}")
def assets(path: str):
    try:
        f = (ASSETS_DIR / path).resolve()
        if not str(f).startswith(str(ASSETS_DIR.resolve())):
            return _missing_image()
        if f.is_file():
            return FileResponse(f)
        return _missing_image()
    except Exception:
        return _missing_image()


@app.get("/videos/{path:path}")
def videos(path: str):
    """通关演示视频等大文件：支持浏览器 <video> 直接引用（Range 请求）。"""
    try:
        f = (VIDEOS_DIR / path).resolve()
        if not str(f).startswith(str(VIDEOS_DIR.resolve())):
            raise ValueError
        if f.is_file():
            return FileResponse(f, media_type="video/webm")
        raise ValueError
    except Exception:
        return Response(status_code=404)


def _missing_image():
    p = ASSETS_DIR / "missing.svg"
    if p.is_file():
        return FileResponse(p)
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/scene-map.json")
def scene_map() -> Dict[str, Any]:
    return json.loads(SCENE_MAP_PATH.read_text(encoding="utf-8"))


# ============================================================ 接口
class _BaseResponse(BaseModel):
    llm_calls: int = 0          # 累计成功调用次数（前端 HUD 展示）


class StartResponse(_BaseResponse):
    narration: str
    state: GameState
    scene: Dict[str, Any]


class StateResponse(_BaseResponse):
    state: GameState
    scene: Dict[str, Any]
    inventory_detail: list


class ActionRequest(BaseModel):
    action: str
    params: Dict[str, Any] = Field(default_factory=dict)


class ActionResponse(_BaseResponse):
    narration: str
    state: GameState
    scene: Dict[str, Any]
    inventory_detail: list


class HintResponse(BaseModel):
    hint: str
    llm_calls: int


def reset_state() -> GameState:
    global _state
    reset_rooms()                  # 恢复所有对象的 contains 初始值（防止跨局污染）
    _state = new_state()
    return _state


@app.post("/api/start", response_model=StartResponse)
def start(background: BackgroundTasks) -> StartResponse:
    state = reset_state()
    # 立即返回默认旁白（<100ms），把 LLM 润色扔到后台跑
    user_msg = (
        "玩家刚进入游戏。当前状态：\n"
        f"{json.dumps(_state_summary(state), ensure_ascii=False)}\n"
        "请用 game_master 工具输出开场旁白（30~80 字），并给出一条欢迎性线索。"
    )
    _llm_call_bg(background, state, SYSTEM_PROMPT, user_msg, DEFAULT_OPENING)
    return StartResponse(
        narration=DEFAULT_OPENING,
        state=state,
        scene=scene_payload(state),
        llm_calls=_llm_call_count,
    )


@app.get("/api/state", response_model=StateResponse)
def get_state() -> StateResponse:
    return StateResponse(
        state=_state,
        scene=scene_payload(_state),
        inventory_detail=_inv_detail(),
        llm_calls=_llm_call_count,
    )


@app.post("/api/action", response_model=ActionResponse)
def api_action(req: ActionRequest, background: BackgroundTasks):
    global _state
    handler = actions.ACTIONS.get(req.action)
    if handler is None:
        raise HTTPException(400, f"未知动作：{req.action}")
    try:
        new_state_obj, default_narration = handler(_state, req.params or {})
    except actions.ActionError as e:
        raise HTTPException(400, str(e))
    _state = new_state_obj
    _state.action_count += 1   # 结算统计：总操作步数

    # 立即返回默认旁白（<100ms），把 LLM 润色扔到后台跑；前端轮询 /api/narration/latest 拿到后覆盖
    user_msg = (
        f"玩家执行动作：{req.action}({json.dumps(req.params, ensure_ascii=False)})\n"
        f"系统默认旁白：{default_narration}\n"
        f"动作后状态：{json.dumps(_state_summary(_state), ensure_ascii=False)}\n"
        "请用 game_master 工具输出本回合的反应旁白（30~80 字）。\n"
        "硬性规则：默认旁白中已给出的具体数字（密码、时间、物品位置、计数）必须原样保留，"
        "不可改写、不可省略、不可意译——它们是玩家解谜的关键线索。\n"
        "可在 clues 中按节奏加入隐藏提示（不要剧透答案，不要主动加已完成步骤的线索）。"
    )
    _llm_call_bg(background, _state, SYSTEM_PROMPT, user_msg, default_narration)

    return ActionResponse(
        narration=default_narration,
        state=_state,
        scene=scene_payload(_state),
        inventory_detail=_inv_detail(),
        llm_calls=_llm_call_count,
    )


class NarrationLatestResponse(BaseModel):
    """前端轮询拉取最近一次后台 LLM 润色旁白；拿到即清空，避免重复推送。"""
    narration: Optional[str] = None
    llm_calls: int = 0


@app.get("/api/narration/latest", response_model=NarrationLatestResponse)
def narration_latest() -> NarrationLatestResponse:
    n = _state.pending_narration
    _state.pending_narration = None
    return NarrationLatestResponse(narration=n, llm_calls=_llm_call_count)


@app.post("/api/hint", response_model=HintResponse)
def api_hint() -> HintResponse:
    """玩家主动请求提示（Day 7 才接前端按钮；后端接口先准备好）。"""
    user_msg = (
        "玩家请求提示。当前状态：\n"
        f"{json.dumps(_state_summary(_state), ensure_ascii=False)}\n"
        "请用 game_master 工具输出 1 句温柔的方向性提示（不要给具体答案、不要剧透），"
        "narration 字段放提示文本，clues 字段留空。"
    )
    hint = _llm_call(
        SYSTEM_PROMPT, user_msg,
        "再仔细观察周围，看看有没有能用上的线索。",
    )
    return HintResponse(hint=hint, llm_calls=_llm_call_count)