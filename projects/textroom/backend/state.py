# -*- coding: utf-8 -*-
"""
TextRoom · 状态模型（独立模块）
================================
第 2 天任务：把"游戏状态"从 main.py 抽出，定义完整结构。
所有状态以后端为唯一来源（铁律①），后续 LLM 函数调用与校验都基于此模块。

数据结构设计原则：
- 数据与行为分离：本文件只定义数据形状与纯函数操作，不混入 HTTP/IO
- 不可变复制：操作函数返回新状态，避免隐式副作用
- 可扩展：三关剧本（study / living_room / garage）的物品、对象、谜题规则全部硬编码在此
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Set, Tuple
from pydantic import BaseModel, Field


# --------------------------------------------------------------- 物品与对象
class Item(BaseModel):
    """可拾取/使用的物品。"""
    id: str                       # 全局唯一物品 ID
    name: str                     # 中文名（背包显示）
    icon: str                     # emoji 图标（背包卡片）
    description: str = ""         # 简述（玩家拾取 / 查看时显示）
    # 物品的初始归属：哪个房间、哪个可交互对象下
    initial_room: str
    initial_object: str           # 该对象 ID（必在此对象下才能拾取）
    # 物品的拾取属性（旧书等参考物不可拾取，只查看）
    pickable: bool = True


class Interactable(BaseModel):
    """场景中可交互的对象（如书架、保险箱）。"""
    id: str                       # 房间内唯一
    room: str
    name: str                     # 中文名（文字按钮显示）
    closeup_image: str            # 特写图路径
    # 该对象身上"挂着"的物品 ID 列表（初始可见可拾取集合）
    contains: List[str] = Field(default_factory=list)
    # 是否可拾取物品 / 是否仅作旁白（大门外面锁死）
    pickable: bool = True
    inspectable: bool = True
    # ---- 第 1 关画框专用：需要先"掀开"才能拾取隐藏物品 ----
    requires_interaction: bool = False          # 该对象是否需要先触发 interact 才能拾取
    interaction_label: Optional[str] = None     # 触发按钮的文案（如 "掀开画框"）
    interaction_flag:  Optional[str] = None     # 触发后修改 state 上哪个 bool 字段名
    # ---- 第 1 关书桌专用：需要先用某个物品"开锁"才能拾取 ----
    unlocked_by_item: Optional[str] = None      # 解锁所需物品 ID（如 "key_full"）
    is_locked_flag: Optional[str] = None        # 解锁后 state 上对应的 bool 字段名
    unlock_description: str = "这里锁着，需要特定物品"


class Room(BaseModel):
    """房间定义。"""
    id: str
    name: str
    panorama: str                 # 全景图路径
    objects: List[Interactable] = Field(default_factory=list)


# --------------------------------------------------------------- 关卡剧本
# 三关剧本硬编码（与图片生成清单/任务书完全一致）。
# 物品初始归属依据任务书第 3 章「完整游玩流程」表逐行核对。
ITEMS: Dict[str, Item] = {
    # ---------- 第 1 关 旧书房 ----------
    "key_half_a": Item(
        id="key_half_a", name="半把钥匙①", icon="🔑",
        description="断成两截的黄铜钥匙中的前半截。",
        initial_room="study", initial_object="bookshelf",
    ),
    "key_half_b": Item(
        id="key_half_b", name="半把钥匙②", icon="🔑",
        description="断成两截的黄铜钥匙中的后半截。",
        initial_room="study", initial_object="picture_frame",
    ),
    "old_book": Item(
        # 书架上的参考物：只能查看，不能拾取。线索 = 「另一半在画框之后」
        id="old_book", name="旧书", icon="📖",
        description="一本泛黄的小说。翻到最后，夹着一张小纸条，上面用铅笔写着：「另一半在画框之后」。",
        initial_room="study", initial_object="bookshelf",
        pickable=False,
    ),
    "key_full": Item(
        id="key_full", name="完整钥匙", icon="🗝",
        description="两半拼合而成，正好能打开书桌抽屉。",
        initial_room="study", initial_object="desk",  # 组合后视为出现在书桌
    ),
    "code_paper": Item(
        id="code_paper", name="密码纸", icon="📜",
        # 隐晦版：只暗示"第三位 + 三位数 + 一个 7"，不直接报完整密码，让玩家必须自己拼
        description="角落潦草写着「第三位 — 7」，其它字迹被水渍模糊。纸张背面用铅笔划了一道：「三位数」。",
        initial_room="study", initial_object="desk",
    ),
    "gear": Item(
        id="gear", name="齿轮", icon="⚙️",
        description="从抽屉取出的小齿轮——正好是钟表丢失的那个齿轮。",
        initial_room="study", initial_object="desk",
    ),
    "study_key": Item(
        id="study_key", name="书房门钥匙", icon="🔑",
        description="从保险箱取出，能打开通往客厅的房门。",
        initial_room="study", initial_object="safe",
    ),
    # ---------- 第 2 关 客厅：图片流程版（小票顺序 → 冰箱贴3 / 挂钟7 / 相册2 / 鱼缸8） ----------
    # 4 个数字来源（顺序提示在外卖小票背面：冰箱 → 挂钟 → 相册 → 鱼缸）：
    #   位1 → 3（红色圆形冰箱贴背面）→ fridge_magnet
    #   位2 → 7（挂钟背面刻字，需晾衣杆挑下）→ clock_plaque
    #   位3 → 2（相册里全家福背面）→ photo_album
    #   位4 → 8（撒鱼食后数鱼）→ fish_fed（无物品，直接记线索）
    "receipt_note": Item(
        id="receipt_note", name="外卖小票", icon="🧾",
        description="旧报纸下压着的外卖小票。背面是爸爸的字迹："
                    "「密码按老规矩找：冰箱 → 挂钟 → 相册 → 鱼缸」。",
        initial_room="living_room", initial_object="coffee_table",
    ),
    "fish_food": Item(
        id="fish_food", name="鱼食", icon="🐟",
        description="一袋没开封的鱼食——鱼缸那么浑，也许能用得上。",
        initial_room="living_room", initial_object="coffee_table",
    ),
    "drying_pole": Item(
        id="drying_pole", name="晾衣杆", icon="🪝",
        description="搭在沙发上的晾衣杆，足够长——墙上高的地方也许够得到。",
        initial_room="living_room", initial_object="sofa",
    ),
    "fridge_magnet": Item(
        id="fridge_magnet", name="红色圆形冰箱贴", icon="🧲",
        description="有点翘边的红色圆形冰箱贴。翻过背面，用马克笔写着：「第1位：3」。",
        initial_room="living_room", initial_object="fridge",
    ),
    # 挂钟挑下来后才出现的背板刻字（由 use(drying_pole, wall_clock) 注入）
    "clock_plaque": Item(
        id="clock_plaque", name="挂钟背板", icon="🕰",
        description="挑下来的挂钟背板。木牌上刻着一行小字：「第2位：7」。",
        initial_room="living_room", initial_object="wall_clock",
    ),
    "photo_album": Item(
        id="photo_album", name="全家福相册", icon="📷",
        description="电视柜上的相册，翻开夹着一张全家福。照片背面用圆珠笔写着：「第3位：2」。",
        initial_room="living_room", initial_object="tv_cabinet",
    ),
    # ---------- 第 3 关 车库：图片流程版（贴纸刻度6 → 铁皮盒 → 旧钥匙 → 挂锁 → 纸条529 → 电子屏 → 卷帘门） ----------
    # 线索链：汽车引擎盖内侧褪色贴纸（老式旋钮停在刻度 6）
    #   → 挂墙工具板旁的铁皮盒刻度盘转到 6 → 弹开得旧钥匙
    #   → 旧钥匙开工具箱挂锁 → 纸条「5 2 9」→ 电子屏输 529 → 面板弹开按向上箭头 → 卷帘门升起逃出
    "car_sticker": Item(
        id="car_sticker", name="褪色贴纸", icon="🏷️",
        description="引擎盖内侧磁性吸着的一张褪色贴纸，上面画着一个老式旋钮——指针停在刻度 6。",
        initial_room="garage", initial_object="car",
        pickable=False,   # 只能查看，不能揭走（贴纸已脆化）
    ),
    "old_key": Item(
        id="old_key", name="旧钥匙", icon="🗝",
        description="铁皮盒里的旧钥匙，头是老式样式——工具箱上那把挂锁的锁孔看着正合适。",
        initial_room="garage", initial_object="tool_board",  # 刻度盘转到 6 后才注入
    ),
    "note_529": Item(
        id="note_529", name="皱纸条", icon="📜",
        description="一张皱巴巴的纸条，用油笔写着三个数字：「5 2 9」。",
        initial_room="garage", initial_object="tool_box",    # 挂锁打开后才注入
    ),
}


ROOMS: Dict[str, Room] = {
    "study": Room(
        id="study", name="旧书房",
        panorama="/assets/study/panorama.png",
        objects=[
            Interactable(id="bookshelf", room="study", name="书架",
                         closeup_image="/assets/study/bookshelf.png",
                         contains=["key_half_a", "old_book"]),
            Interactable(id="desk", room="study", name="书桌",
                         closeup_image="/assets/study/desk.png",
                         contains=[],   # 默认锁住为空；use(key_full,desk) 后注入
                         # 第 1 关修订：抽屉锁住，必须先用「完整钥匙」开锁才能拾取内部物品
                         unlocked_by_item="key_full",
                         is_locked_flag="desk_unlocked",
                         unlock_description="书桌抽屉锁着，要用完整钥匙才能打开。"),
            Interactable(id="picture_frame", room="study", name="画框",
                         closeup_image="/assets/study/picture_frame.png",
                         contains=["key_half_b"],
                         # 第 1 关修订：必须先"掀开画框"才能拾取里面的半把钥匙②
                         requires_interaction=True,
                         interaction_label="掀开画框",
                         interaction_flag="picture_frame_opened"),
            Interactable(id="clock", room="study", name="钟表",
                         closeup_image="/assets/study/clock.png",
                         contains=[]),
            Interactable(id="safe", room="study", name="保险箱",
                         closeup_image="/assets/study/safe.png",
                         contains=["study_key"]),
            Interactable(id="door", room="study", name="书房门",
                         closeup_image="/assets/study/door.png",
                         contains=[]),
        ],
    ),
    "living_room": Room(
        id="living_room", name="客厅",
        panorama="/assets/living_room/panorama.png",
        objects=[
            Interactable(id="main_gate", room="living_room", name="大门",
                         closeup_image="/assets/living_room/main_gate.png",
                         contains=[], pickable=False, inspectable=True),
            Interactable(id="garage_door", room="living_room", name="车库门",
                         closeup_image="/assets/living_room/garage_door.png",
                         contains=[]),
            Interactable(id="coffee_table", room="living_room", name="茶几",
                         closeup_image="/assets/living_room/coffee_table.png",
                         # 图片流程：茶几上有外卖小票（顺序提示）+ 鱼食
                         contains=["receipt_note", "fish_food"]),
            Interactable(id="fridge", room="living_room", name="冰箱门",
                         closeup_image="/assets/living_room/fridge.png",
                         # 图片流程：三枚冰箱贴，红色那枚要"揭下"才能拿
                         contains=["fridge_magnet"],
                         requires_interaction=True,
                         interaction_label="揭下冰箱贴",
                         interaction_flag="magnet_revealed"),
            Interactable(id="wall_clock", room="living_room", name="墙上挂钟",
                         closeup_image="/assets/living_room/wall_clock.png",
                         # 图片流程：挂得太高够不到；use(drying_pole) 后注入 clock_plaque
                         contains=[]),
            Interactable(id="tv_cabinet", room="living_room", name="电视柜",
                         closeup_image="/assets/living_room/tv_cabinet.png",
                         # 图片流程：电视柜上放着相册
                         contains=["photo_album"]),
            Interactable(id="sofa", room="living_room", name="沙发",
                         closeup_image="/assets/living_room/sofa.png",
                         # 图片流程：沙发上搭着晾衣杆
                         contains=["drying_pole"]),
            Interactable(id="fish_tank", room="living_room", name="角落鱼缸",
                         closeup_image="/assets/living_room/fish_tank.png",
                         # 图片流程：水浑看不清；use(fish_food) 后数鱼
                         contains=[]),
        ],
    ),
    "garage": Room(
        id="garage", name="车库",
        panorama="/assets/garage/panorama.png",
        objects=[
            Interactable(id="exit_door", room="garage", name="卷帘门",
                         closeup_image="/assets/garage/exit_door.png",
                         contains=[], pickable=False),
            Interactable(id="keypad", room="garage", name="电子屏",
                         closeup_image="/assets/garage/keypad.png",
                         # 图片流程：3 位密码（上下键+确认键）；输对 529 后玻璃面板弹开，
                         # 露出上下箭头 → 「查看电子屏」弹窗 ↑开/↓关 卷帘门（可反复）
                         contains=[],
                         requires_interaction=True,
                         interaction_label="查看电子屏（上下箭头）",
                         interaction_flag="shutter_opened"),
            Interactable(id="remote", room="garage", name="遥控器",
                         closeup_image="/assets/garage/remote.png",
                         # 图片流程：外壳裂开、电池仓空 → 损坏装饰物，无法使用
                         contains=[]),
            Interactable(id="car", room="garage", name="汽车",
                         closeup_image="/assets/garage/car.png",
                         # 图片流程：引擎盖没扣严一掀就开，内侧磁性吸着褪色贴纸（刻度 6 线索）
                         contains=["car_sticker"]),
            Interactable(id="tool_board", room="garage", name="挂墙工具板",
                         closeup_image="/assets/garage/tool_board.png",
                         # 图片流程：板旁墙上挂着旧铁皮盒，旋转刻度盘 1-12（停在 0）
                         # turn_dial(tool_board, 6) 后注入 old_key
                         contains=[]),
            Interactable(id="tool_box", room="garage", name="工具箱",
                         closeup_image="/assets/garage/tool_box.png",
                         # 图片流程：挂着老式钥匙孔挂锁；use(old_key, tool_box) 后注入 note_529
                         contains=[]),
        ],
    ),
}


# 初始 contains 模板（reset 时用，确保跨局不污染）
_INITIAL_CONTAINS: Dict[str, List[str]] = {
    obj.id: list(obj.contains) for room in ROOMS.values() for obj in room.objects
}


def reset_rooms() -> None:
    """把每个对象的 contains 恢复为模块加载时的初始值。"""
    for room in ROOMS.values():
        for obj in room.objects:
            obj.contains = list(_INITIAL_CONTAINS.get(obj.id, []))


# --------------------------------------------------------------- 谜题规则
# 组合规则：服务端硬编码（铁律③：AI 只能查表调用，不能发明组合）
CombineRule = Tuple[str, str]                       # 顺序无关的两个物品 ID
COMBINE_RULES: Dict[CombineRule, str] = {
    ("key_half_a", "key_half_b"): "key_full",
}
def combine_result(a: str, b: str) -> Optional[str]:
    return COMBINE_RULES.get((a, b)) or COMBINE_RULES.get((b, a))


# 关卡密码（按任务书"(1).md"修订版核对）
PASSWORDS: Dict[str, str] = {
    "study.safe":     "397",   # 保险箱（指针 3、9 + 密码纸 7）
    "living_room.garage_door": "3728",  # 客厅车库门（3-7-2-8）
    "garage.keypad": "529",     # 电子屏（上下键+确认键，来源=工具箱纸条 5 2 9）
}


# --------------------------------------------------------------- 游戏状态
class GameState(BaseModel):
    """后端唯一权威状态。"""
    # ---------- 进度 ----------
    level: int = 1                                        # 当前关卡 1-3
    room: str = "study"                                   # 当前房间 ID
    progress: int = 0                                     # 0-100
    finished: bool = False
    # ---------- 视图 ----------
    view: Literal["panorama", "closeup"] = "panorama"     # 当前画面模式
    current_closeup: Optional[str] = None                 # 特写时显示哪个对象
    # ---------- 背包 ----------
    inventory: List[str] = Field(default_factory=list)    # 物品 ID 列表（按拾取顺序）
    # ---------- 线索（已查看/发现的提示） ----------
    clues: List[str] = Field(default_factory=list)        # 文本型线索
    # ---------- 状态机 ----------
    discovered: Set[str] = Field(default_factory=set)     # 已查看（打开过特写）的对象 ID
    picked_up: Set[str] = Field(default_factory=set)      # 已拾取的物品 ID（防重复拾取）
    used: Set[str] = Field(default_factory=set)           # 已使用/消耗的物品 ID
    # ---------- 关卡校验用 ----------
    attempts: Dict[str, int] = Field(default_factory=dict)  # 密码尝试次数（target_id -> count）
    # ---------- 第 1 关特殊：钟表是否装好齿轮 ----------
    clock_fixed: bool = False
    # ---------- 第 1 关特殊：书桌抽屉是否已用完整钥匙打开 ----------
    desk_unlocked: bool = False
    # ---------- 第 1 关特殊：保险箱是否已用密码打开（唯一开法；打开后才能拾取书房门钥匙） ----------
    safe_unlocked: bool = False
    # ---------- 第 1 关特殊：画框是否已"掀开"（遮蔽画内钥匙的） ----------
    picture_frame_opened: bool = False
    # ---------- 第 2 关特殊（图片流程版） ----------
    # 冰箱贴是否已"揭下" → 才能拾 fridge_magnet
    magnet_revealed: bool = False
    # 挂钟是否已用晾衣杆挑下来 → wall_clock.contains 注入 clock_plaque
    wall_clock_lowered: bool = False
    # 鱼食是否已撒向鱼缸 → 数出 8 条（第4位）
    fish_fed: bool = False
    # ---------- 第 3 关特殊（图片流程版） ----------
    # 铁皮盒刻度盘是否已转到刻度 6 → tool_board.contains 注入 old_key
    tin_box_opened: bool = False
    # 铁皮盒刻度盘当前位置（0=起始未对齐；向左/向右每次转一格，1-12 循环）
    dial_position: int = 0
    # 工具箱挂锁是否已用旧钥匙打开 → tool_box.contains 注入 note_529
    padlock_unlocked: bool = False
    # 电子屏 529 是否已输对 → 玻璃面板弹开，露出向上箭头
    keypad_unlocked: bool = False
    # 向上箭头是否已按下 → 卷帘门升起（之后 look(exit_door) 走出 → 通关）
    shutter_opened: bool = False
    # ---------- 结算统计：开局时间戳与动作步数 ----------
    started_at: float = Field(default_factory=lambda: __import__("time").time())
    action_count: int = 0
    # ---------- LLM 后台润色旁白：最近一次跑完的结果；前端轮询拉取 ----------
    pending_narration: Optional[str] = None    # 由 BackgroundTask 写入；前端 GET /api/narration/latest 拉取


# 工厂：初始化一局新游戏
def new_state() -> GameState:
    return GameState()


# --------------------------------------------------------------- 派生信息
def visible_objects(state: GameState) -> List[Interactable]:
    """当前房间的可交互对象列表（供文字按钮区渲染）。"""
    return ROOMS[state.room].objects


def object_by_id(state: GameState, obj_id: str) -> Optional[Interactable]:
    for o in ROOMS[state.room].objects:
        if o.id == obj_id:
            return o
    return None


def scene_payload(state: GameState) -> Dict[str, Any]:
    """发给前端的场景信息（全景或特写）。

    特写模式下额外携带：
      - items: 该对象上当前可拾取/可查看的物品（含 id/name/icon/pickable）
      - interactive_targets: 同房间其它可作为"使用"目标的对象
      - needs_password: 是否需要密码输入（数字密码锁）
      - needs_radio: 是否是车载音响（按预设键解锁）
      - needs_interaction: 是否需要先点"操作按钮"才能拾取（如掀开画框）
      - prereq_hint: 前置条件未满足时的中文提示
    """
    room = ROOMS[state.room]
    if state.view == "panorama":
        # 全景：列出当前房间所有可交互对象（不再有第 2 关的隐藏 vent_duct）
        objs = [
            {"id": o.id, "name": o.name}
            for o in room.objects
        ]
        return {
            "mode": "panorama",
            "room_id": room.id,
            "room_name": room.name,
            "image": room.panorama,
            "objects": objs,
        }
    obj = object_by_id(state, state.current_closeup or "")

    # 是否被 requires_interaction 阻挡（如画框未掀开 → contains 不显示）
    interaction_blocked = False
    if obj and obj.requires_interaction:
        flag = obj.interaction_flag
        if flag and not getattr(state, flag, False):
            interaction_blocked = True

    # 是否被 unlocked_by_item 阻挡（书桌未开锁 → contains 不显示）
    locked_blocked = False
    if obj and obj.unlocked_by_item:
        flag = obj.is_locked_flag
        if flag and not getattr(state, flag, False):
            locked_blocked = True

    # 是否被密码锁阻挡（保险箱未输对密码 → contains 不显示，只能先输密码；
    # 有且只有一把钥匙：唯一获取路径 = 输对密码 → 拾取）
    password_blocked = False
    if obj and state.room == "study" and obj.id == "safe":
        password_blocked = not state.safe_unlocked

    items = []
    if obj and not interaction_blocked and not locked_blocked and not password_blocked:
        for iid in obj.contains:
            if iid in state.picked_up:
                continue
            item = ITEMS.get(iid)
            if item:
                items.append({
                    "id": item.id, "name": item.name, "icon": item.icon,
                    "pickable": item.pickable,
                })
    targets = [
        {"id": o.id, "name": o.name}
        for o in room.objects
        if o.id != (obj.id if obj else None) and o.inspectable
    ]
    payload = {
        "mode": "closeup",
        "room_id": room.id,
        "room_name": room.name,
        "object_id": obj.id if obj else None,
        "object_name": obj.name if obj else None,
        "image": obj.closeup_image if obj else room.panorama,
        "items": items,
        "interactive_targets": targets,
        "needs_password": None,
        "needs_dial": None,
        "needs_interaction": None,
        "needs_item_for_unlock": None,
        "prereq_hint": None,
    }
    # 互动前置（如：掀开画框）
    if interaction_blocked and obj:
        payload["needs_interaction"] = obj.interaction_label or "操作"
    # 工具解锁提示（如：书桌需要完整钥匙）
    if locked_blocked and obj:
        payload["needs_item_for_unlock"] = obj.unlocked_by_item
        payload["prereq_hint"] = obj.unlock_description
    # 密码锁提示（如：保险箱必须先输密码）
    if password_blocked and obj:
        payload["prereq_hint"] = "保险箱锁着——需要输入 3 位数字密码才能打开。"
    # 密码输入：保险箱（3 位）/ 车库门（4 位）/ 电子屏（3 位）
    key = f"{state.room}.{obj.id if obj else ''}"
    if key in PASSWORDS:
        payload["needs_password"] = {"length": len(PASSWORDS[key])}
    # 已用密码打开的对象：不再显示密码输入，改显示「已打开」状态
    if state.room == "study" and obj and obj.id == "safe" and state.safe_unlocked:
        payload["needs_password"] = None
        remaining = [iid for iid in obj.contains if iid not in state.picked_up]
        payload["prereq_hint"] = (
            "🔓 保险箱已打开——里面还放着书房门钥匙，点击下方按钮拾取。" if remaining
            else "🔓 保险箱已打开，里面已经空了。")
    # 第 3 关电子屏双阶段：输对 529 前只显示密码输入；输对后面板弹开 →
    # 一直显示「查看电子屏」按钮（弹窗内 ↑/↓ 按当前门态分流：关门时 ↑开↓无动静，开门时 ↑无动静↓关）
    if state.room == "garage" and obj and obj.id == "keypad":
        if state.keypad_unlocked:
            payload["needs_password"] = None   # 已解锁，不再重复要密码
            payload["needs_interaction"] = obj.interaction_label or "查看电子屏"
            payload["prereq_hint"] = "玻璃面板已经弹开，露出上、下两个箭头键。"
        else:
            # 未输对密码前，玻璃面板盖着按键 → 不显示箭头互动
            payload["needs_interaction"] = None
    # 第 3 关铁皮盒刻度盘：未打开时显示「向左/向右旋转」双按钮 + 当前刻度
    if state.room == "garage" and obj and obj.id == "tool_board" and not state.tin_box_opened:
        payload["needs_dial"] = {"position": state.dial_position}
    # 第 3 关卷帘门：升起后（未走出）显示「走出卷帘门」按钮（点击 → look 触发通关结算）
    if state.room == "garage" and obj and obj.id == "exit_door" \
            and state.shutter_opened and not state.finished:
        payload["needs_interaction"] = "走出卷帘门"
    return payload
