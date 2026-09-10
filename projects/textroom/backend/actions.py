# -*- coding: utf-8 -*-
"""
TextRoom · 服务端动作处理（Day 3）
- 所有改状态的动作都在这里实现
- 服务端校验（铁律③）：未拾取不能用、组合须合法、目标必须存在、必须先特写才能拾取
- 后续接 LLM（第 4 天函数调用）只能调用这里的函数，不能直接改 state
"""
from typing import Any, Dict, Tuple
import time

from backend.state import GameState, ROOMS, ITEMS, combine_result, PASSWORDS, Interactable


class ActionError(Exception):
    """校验失败 → main.py 转为 HTTP 400。"""


def _obj(room_id: str, obj_id: str) -> Interactable:
    for o in ROOMS[room_id].objects:
        if o.id == obj_id:
            return o
    raise ActionError(f"对象不存在：{obj_id}")


def _clue(state: GameState, text: str) -> None:
    """记录线索：同一条线索只能获得一次（去重）。"""
    if text not in state.clues:
        state.clues.append(text)


# --------------------------------------------------------------- 基础动作
def look(state: GameState, obj_id: str) -> Tuple[GameState, str]:
    """查看一个对象（进入特写视图）。"""
    obj = _obj(state.room, obj_id)
    if not obj.inspectable:
        raise ActionError(f"{obj.name} 不可查看")
    state.view = "closeup"
    state.current_closeup = obj_id
    state.discovered.add(obj_id)
    # 特殊旁白：第 2 关大门（世界设定：从外面焊死，车库门是唯一出口）
    if state.room == "living_room" and obj_id == "main_gate":
        return state, (
            "你推了推大门——纹丝不动。凑近一看，门轴被人从外面焊死了，"
            "从里面根本打不开。这个房间唯一的出口，是那扇带电子锁的车库门。"
        )
    # 特殊旁白：第 3 关遥控器（损坏装饰物）
    if state.room == "garage" and obj_id == "remote":
        return state, (
            "你捡起车载遥控器——外壳裂开一条缝，掰开电池仓一看：空的，触点还锈了。"
            "这台遥控器彻底报废了，只能另想办法。"
        )
    # 特殊旁白：第 3 关卷帘门（唯一出口；升起后可走出 → 通关结算）
    if state.room == "garage" and obj_id == "exit_door":
        if state.shutter_opened:
            if not state.finished:
                return state, (
                    "卷帘门已完全升起，外面的光洒了进来。"
                    "点击「走出卷帘门」，逃离这间密室。"
                )
            return state, "你已站在卷帘门外——自由的空气。"
        return state, (
            "你推了推卷帘门——死死压在轨道上。旁边的电子屏亮着「---」。"
            "这扇卷帘门，是整间车库唯一的出口。"
        )
    return state, f"你走近{obj.name}。"


def back(state: GameState) -> Tuple[GameState, str]:
    """从特写退回全景。"""
    state.view = "panorama"
    state.current_closeup = None
    return state, "你回到房间中央。"


def pick_up(state: GameState, obj_id: str, item_id: str) -> Tuple[GameState, str]:
    """拾取物品（必须先进入该对象的特写视图）。"""
    obj = _obj(state.room, obj_id)
    if state.view != "closeup" or state.current_closeup != obj_id:
        raise ActionError(f"请先查看 {obj.name} 才能拾取物品")
    # requires_interaction 拦截（如未掀开画框前不能拾取里面的钥匙）
    if obj.requires_interaction:
        flag = obj.interaction_flag
        if flag and not getattr(state, flag, False):
            label = obj.interaction_label or "先操作"
            raise ActionError(f"需要先「{label}」才能拾取物品")
    # unlocked_by_item 拦截（如未先用完整钥匙开书桌抽屉，不能拾取里面的物品）
    if obj.unlocked_by_item:
        flag = obj.is_locked_flag
        if flag and not getattr(state, flag, False):
            raise ActionError(obj.unlock_description or "该对象尚未解锁")
    # 密码锁拦截（如保险箱未输对密码，不能直接拾取里面的物品——唯一开法是密码）
    if state.room == "study" and obj_id == "safe" and not state.safe_unlocked:
        raise ActionError("保险箱锁着——先输入正确的 3 位密码才能打开")
    if item_id not in obj.contains:
        raise ActionError(f"{obj.name} 下没有这个物品")
    # 物品本身是否可拾取（仅可查看的，如旧书、密封信封）
    item = ITEMS.get(item_id)
    if item is not None and not item.pickable:
        raise ActionError(
            f"「{item.name}」不可直接拾取——需要先用工具打开或查看"
        )
    if item_id in state.picked_up:
        raise ActionError(f"{ITEMS[item_id].name} 已经拾取过了")
    obj.contains.remove(item_id)
    state.inventory.append(item_id)
    state.picked_up.add(item_id)
    _clue(state, f"拾取 {ITEMS[item_id].name}")
    state.progress = min(100, state.progress + 5)
    return state, f"你拿起了 {ITEMS[item_id].name}。"


def interact(state: GameState, obj_id: str) -> Tuple[GameState, str]:
    """触发对象的互动步骤（如掀开画框）。翻转 state 上的指定 bool 标志位。"""
    obj = _obj(state.room, obj_id)
    if state.view != "closeup" or state.current_closeup != obj_id:
        raise ActionError(f"请先查看 {obj.name}")
    if not obj.requires_interaction:
        raise ActionError(f"{obj.name} 不需要额外操作")
    flag = obj.interaction_flag
    if not flag:
        raise ActionError(f"{obj.name} 未配置 interaction_flag")
    if flag == "picture_frame_opened":
        if state.picture_frame_opened:
            raise ActionError("画框已经掀开了")
        state.picture_frame_opened = True
        _clue(state, "掀开画框，露出暗格")
        return state, "你把画框从墙上掀开，墙里露出一个暗格——里面藏着一枚半截钥匙。"
    # ---- 图片流程：第 2 关冰箱贴 ----
    if flag == "magnet_revealed":
        if state.magnet_revealed:
            raise ActionError("冰箱贴已经揭下来了")
        state.magnet_revealed = True
        _clue(state, "揭下红色圆形冰箱贴")
        return state, (
            "冰箱门上贴着三枚冰箱贴。你把那枚有点翘边的红色圆形揭了下来"
            "——翻过来，背面用马克笔写着字。"
        )
    # ---- 电子屏卷帘门已改由 press_arrow 驱动（可反复开关），interact 不再处理 ----
    if flag == "shutter_opened":
        raise ActionError("电子屏请通过上下箭头操作")
    raise ActionError(f"未实现的 interaction_flag：{flag}")


def press_arrow(state: GameState, direction: str) -> Tuple[GameState, str]:
    """第 3 关电子屏上下箭头（须先输对 529，玻璃面板弹开）。

    按当前卷帘门状态分流：
      - 门未开：↑ 升起卷帘门；↓ 没有任何动静
      - 门已开：↑ 没有任何动静；↓ 落下卷帘门（可反复开关）
    """
    if state.room != "garage":
        raise ActionError("这里没有电子屏")
    if not state.keypad_unlocked:
        raise ActionError(
            "玻璃面板还严严实实地盖着按键，电子屏显示「---」——"
            "先用上下键调出正确的 3 位密码再按确认。"
        )
    if state.view != "closeup" or state.current_closeup != "keypad":
        raise ActionError("请先查看电子屏再按箭头")
    if direction not in ("up", "down"):
        raise ActionError("只能按「向上箭头」或「向下箭头」")

    if direction == "up":
        if state.shutter_opened:
            return state, "卷帘门已经升到顶了——再按向上箭头，电机只空转了一声，没有别的动静。"
        state.shutter_opened = True
        _clue(state, "电子屏按下向上箭头，卷帘门缓缓升起")
        state.progress = min(100, state.progress + 10)
        return state, (
            "你按下向上箭头——绿灯闪了一下，卷帘门在电机声中缓缓升起！"
            "外面的光洒了进来。（此刻按下向下箭头，可以把门重新落下去。）"
        )
    # down
    if not state.shutter_opened:
        return state, "你按下向下箭头——没有任何动静，卷帘门纹丝不动。"
    state.shutter_opened = False
    _clue(state, "电子屏按下向下箭头，卷帘门落回轨道")
    return state, (
        "你按下向下箭头——卷帘门轰隆隆落下，重新死死压回轨道。"
        "（再按向上箭头可以重新升起。）"
    )


def examine_scene_item(state: GameState, obj_id: str, item_id: str) -> Tuple[GameState, str]:
    """查看场景上的物品（不可拾取时），只看不拿。如查看书架上的旧书。"""
    if state.view != "closeup" or state.current_closeup != obj_id:
        raise ActionError("请先进入对象特写视图")
    obj = _obj(state.room, obj_id)
    if item_id not in obj.contains:
        raise ActionError(f"{obj.name} 下没有这个物品")
    item = ITEMS.get(item_id)
    if not item:
        raise ActionError("物品不存在")
    _clue(state, f"查看 {item.name}：{item.description}")
    return state, f"{item.name}：{item.description}"


def inspect_item(state: GameState, item_id: str) -> Tuple[GameState, str]:
    """查看背包物品的说明。"""
    if item_id not in state.inventory:
        raise ActionError("物品不在背包里")
    if item_id == "receipt_note":
        return state, (
            "外卖小票。背面是爸爸的字迹："
            "「密码按老规矩找：**冰箱 → 挂钟 → 相册 → 鱼缸**」。"
        )
    return state, f"{ITEMS[item_id].name}：{ITEMS[item_id].description}"


def combine(state: GameState, a_id: str, b_id: str) -> Tuple[GameState, str]:
    """按硬编码规则表组合两个物品。"""
    if a_id == b_id:
        raise ActionError("不能与自己组合")
    for iid in (a_id, b_id):
        if iid not in state.inventory:
            raise ActionError(f"背包中没有 {ITEMS[iid].name if iid in ITEMS else iid}")
    result = combine_result(a_id, b_id)
    if not result:
        raise ActionError(f"{ITEMS[a_id].name} 与 {ITEMS[b_id].name} 无法组合")
    state.inventory.remove(a_id)
    state.inventory.remove(b_id)
    state.inventory.append(result)
    state.picked_up.add(result)
    _clue(state, 
        f"组合 {ITEMS[a_id].name} + {ITEMS[b_id].name} → {ITEMS[result].name}"
    )
    state.progress = min(100, state.progress + 10)
    return state, f"你把两半拼在一起，得到了 {ITEMS[result].name}！"


# --------------------------------------------------------------- 物品使用
def use(state: GameState, item_id: str, target_id: str) -> Tuple[GameState, str]:
    """把物品使用到指定对象 / 其它物品上。

    方案 ②：target 允许两种——
      - 房间对象：必须 closeup（"道具到了使用地点才可以用"）
      - 背包内物品：不强制 closeup（用于日历擦净等"物品→物品"操作）
    """
    if item_id not in state.inventory:
        raise ActionError(
            f"背包中没有 {ITEMS[item_id].name if item_id in ITEMS else item_id}"
        )

    # ============================================================
    # 分支 A：物品 → 背包内物品（当前无此规则，统一拒绝）
    # ============================================================
    if target_id in state.inventory:
        raise ActionError(
            f"你试着把「{ITEMS[item_id].name}」用在「{ITEMS[target_id].name}」上，但没什么反应。"
            " 也许它们没有可配合的用途。"
        )

    # ============================================================
    # 分支 B：物品 → 房间对象（原"必须 closeup"逻辑）
    # ============================================================
    target = _obj(state.room, target_id)
    if state.view != "closeup" or state.current_closeup != target_id:
        item_name = ITEMS[item_id].name if item_id in ITEMS else item_id
        raise ActionError(
            f"请先走近「{target.name}」（点击进入特写）后再使用「{item_name}」。"
        )

    # ---------- 第 1 关 书房 ----------
    if item_id == "key_full" and target_id == "desk":
        state.inventory.remove("key_full")
        state.used.add("key_full")
        desk = _obj(state.room, "desk")
        state.desk_unlocked = True
        # 把抽屉里的物品正式搬到 desk.contains（之前是 ROOMS 默认，玩家容易跳过开锁就拿走）
        for iid in ("code_paper", "gear"):
            if iid not in desk.contains:
                desk.contains.append(iid)
        _clue(state, "用完整钥匙打开书桌抽屉，得到密码纸与齿轮")
        state.progress = min(100, state.progress + 15)
        return state, "抽屉咔哒一声打开了，里面有密码纸和一个小齿轮。"

    if item_id == "gear" and target_id == "clock":
        state.inventory.remove("gear")
        state.used.add("gear")
        state.clock_fixed = True
        # 隐晦版：只描述指针指向，不直接报"3 时 45 分"或"前两位密码"——让玩家自己拼
        _clue(state, "齿轮装上后钟表重新走动——时针指 3、分针指 9")
        state.progress = min(100, state.progress + 10)
        return state, "你把齿轮装进钟表。咔嚓一声，时针稳稳指 3、分针指 9。"

    if item_id == "study_key" and target_id == "door":
        state.inventory.remove("study_key")
        state.used.add("study_key")
        # 跨关：进入第 2 关，背包清空（本关物品均在本关消耗）；线索不跨关，一并清空
        state.room = "living_room"
        state.level = 2
        state.view = "panorama"
        state.current_closeup = None
        state.inventory.clear()
        state.clues.clear()
        _clue(state, "打开书房门，进入客厅")
        state.progress = 40
        return state, "门打开，你走进了客厅。"

    # ---------- 第 2 关 客厅（图片流程版） ----------
    # ---- use(drying_pole, wall_clock) → 挑下挂钟，注入 clock_plaque ----
    if item_id == "drying_pole" and target_id == "wall_clock":
        if state.wall_clock_lowered:
            raise ActionError("挂钟已经挑下来了")
        state.wall_clock_lowered = True
        clock = _obj(state.room, "wall_clock")
        if "clock_plaque" not in clock.contains:
            clock.contains.append("clock_plaque")
        _clue(state, "用晾衣杆挑下挂钟，背板刻着「第2位：7」")
        state.progress = min(100, state.progress + 10)
        return state, (
            "挂钟挂得太高，你举起晾衣杆小心一挑——挂钟稳稳落进手里。"
            "翻过背面：木牌上刻着一行小字「第2位：7」。"
        )

    # ---- use(fish_food, fish_tank) → 撒鱼食，数出 8 条 ----
    if item_id == "fish_food" and target_id == "fish_tank":
        if state.fish_fed:
            raise ActionError("鱼已经吃饱了")
        state.inventory.remove("fish_food")
        state.used.add("fish_food")
        state.fish_fed = True
        _clue(state, "撒下鱼食，鱼聚拢游过来——正好 8 条（第4位：8）")
        state.progress = min(100, state.progress + 10)
        return state, (
            "你撕开鱼食撒向鱼缸——浑水里的鱼纷纷聚拢游过来抢食。"
            "凑近数一数：1、2、3……正好 8 条（第4位：8）。"
        )

    # ---------- 第 3 关 车库（图片流程版） ----------
    # ---- use(old_key, tool_box) → 旧钥匙开挂锁，注入 note_529 ----
    if item_id == "old_key" and target_id == "tool_box":
        if state.padlock_unlocked:
            raise ActionError("挂锁已经打开了")
        state.inventory.remove("old_key")
        state.used.add("old_key")
        state.padlock_unlocked = True
        box = _obj(state.room, "tool_box")
        if "note_529" not in box.contains:
            box.contains.append("note_529")
        _clue(state, "用旧钥匙打开工具箱挂锁，里面压着一张皱纸条")
        state.progress = min(100, state.progress + 10)
        return state, (
            "旧钥匙插进挂锁的老式钥匙孔——严丝合缝。咔哒一声，挂锁弹开，"
            "掀开工具箱盖：里面压着一张皱巴巴的纸条。"
        )

    raise ActionError(
        f"你试着把「{ITEMS[item_id].name}」用在「{target.name}」上，但没什么反应。"
        " 也许这把钥匙 / 这个工具不是用在它身上的——换个对象试试？"
    )


# --------------------------------------------------------------- 密码与刻度盘
def enter_password(state: GameState, target_id: str, code: str) -> Tuple[GameState, str]:
    """向某个对象输入数字密码（保险箱 / 车库门 / 出口门）。"""
    key = f"{state.room}.{target_id}"
    expected = PASSWORDS.get(key)
    if expected is None:
        raise ActionError(f"{target_id} 没有数字密码锁")
    if code != expected:
        state.attempts[target_id] = state.attempts.get(target_id, 0) + 1
        raise ActionError(
            f"密码错误（已尝试 {state.attempts[target_id]} 次），保险箱纹丝不动"
            if target_id == "safe"
            else f"密码错误（已尝试 {state.attempts[target_id]} 次）"
        )
    # 成功分支
    if state.room == "study" and target_id == "safe":
        # 唯一开法 = 密码；开锁后钥匙留在箱内，需自行拾取（有且只有一把）
        if state.safe_unlocked:
            return state, "保险箱已经打开了——里面那把书房门钥匙还等着你拿。"
        state.safe_unlocked = True
        _clue(state, "用密码 397 打开保险箱，里面有一把书房门钥匙")
        state.progress = min(100, state.progress + 20)
        return state, "保险箱咔嗒一声打开了——里面躺着一把书房门钥匙。"
    if state.room == "living_room" and target_id == "garage_door":
        # 第 2 关 C+：3728 正确 → 跨关直接进入车库（车库门是唯一出口）
        state.attempts["garage_door"] = state.attempts.get("garage_door", 0) + 1
        # 跨关（线索不跨关，先清空）
        state.clues.clear()
        _clue(state, "用密码 3728 打开车库门，进入车库")
        state.room = "garage"
        state.level = 3
        state.view = "panorama"
        state.current_closeup = None
        state.inventory.clear()
        state.progress = 70
        return state, "电子屏叮的一声「密码正确」——车库门慢慢升起。你迈过门槛，走进车库。"
    if state.room == "garage" and target_id == "keypad":
        # 第 3 关图片流程：电子屏 529 正确 → 绿灯亮、玻璃面板弹开（不直接通关，
        # 还需 interact(keypad) 按向上箭头升起卷帘门，再走出卷帘门结算）
        if state.keypad_unlocked:
            return state, "电子屏已经亮着绿灯，玻璃面板弹开着——该按下向上箭头了。"
        state.attempts["keypad"] = state.attempts.get("keypad", 0) + 1
        state.keypad_unlocked = True
        _clue(state, "电子屏密码 529 正确，绿灯亮起，玻璃面板弹开")
        state.progress = min(100, state.progress + 15)
        return state, (
            "最后一位数字落定，你按下确认键——屏幕亮起绿灯，"
            "透明玻璃面板「咔」地弹开，露出上、下两个箭头键。"
        )
    raise ActionError("密码正确但此场景未配置后续动作")


def turn_dial(state: GameState, obj_id: str, direction: str) -> Tuple[GameState, str]:
    """第 3 关：铁皮盒旋转刻度盘，向左/向右每次转一格（1-12 循环，0=起始）。

    图片流程：汽车引擎盖内侧的褪色贴纸画着老式旋钮停在刻度 6
    → 刻度盘正好停在 6 时盒子弹开（注入旧钥匙）；停错刻度则毫无反应。
    """
    obj = _obj(state.room, obj_id)
    if state.view != "closeup" or state.current_closeup != obj_id:
        raise ActionError(f"请先查看 {obj.name} 再转动刻度盘")
    if obj_id != "tool_board":
        raise ActionError(f"{obj.name} 上没有刻度盘")
    if direction not in ("left", "right"):
        raise ActionError("只能「向左旋转」或「向右旋转」")
    if state.tin_box_opened:
        raise ActionError("铁皮盒已经打开了")
    if direction == "right":
        # 0 → 1；12 → 1（循环）
        state.dial_position = 1 if state.dial_position in (0, 12) else state.dial_position + 1
        dir_text = "向右"
    else:
        # 0 → 12；1 → 12（循环）
        state.dial_position = 12 if state.dial_position in (0, 1) else state.dial_position - 1
        dir_text = "向左"
    if state.dial_position == 6:
        state.tin_box_opened = True
        board = _obj(state.room, "tool_board")
        if "old_key" not in board.contains:
            board.contains.append("old_key")
        _clue(state, "铁皮盒刻度盘转到 6，盒子弹开，里面有把旧钥匙")
        state.progress = min(100, state.progress + 10)
        return state, (
            "刻度盘正好停在 6——「咔哒」！盒盖中央的锁舌缩了回去，"
            "旧铁皮盒弹开了，里面躺着一把旧钥匙。"
        )
    return state, (
        f"你{dir_text}旋转一格，刻度盘停在 {state.dial_position}——盒子毫无反应。"
        "（贴纸上那个老式旋钮，好像停在某个刻度上……）"
    )


def walk_out(state: GameState) -> Tuple[GameState, str]:
    """第 3 关终局：卷帘门升起后，走出卷帘门 → 通关结算（game_over）。"""
    if state.room != "garage":
        raise ActionError("这里没有卷帘门")
    if not state.shutter_opened:
        raise ActionError("卷帘门还死死压在轨道上——先在电子屏调出正确的 3 位密码")
    if state.finished:
        return state, "你已经逃出密室了。"
    state.finished = True
    state.progress = 100
    elapsed = max(0, int(time.time() - state.started_at))
    minutes, seconds = divmod(elapsed, 60)
    explore_count = len(state.discovered)
    _clue(state, "走出卷帘门，逃出密室")
    return state, (
        "你侧身走出缓缓升起的卷帘门——外面是自由的空气。"
        f"逃出密室！用时 {minutes} 分 {seconds} 秒，"
        f"共探索了 {explore_count} 处、执行了 {state.action_count} 步操作。"
    )


# --------------------------------------------------------------- 分发表
ACTIONS: Dict[str, Any] = {
    "look":              lambda s, p: look(s, p["object_id"]),
    "back":              lambda s, p: back(s),
    "pick_up":           lambda s, p: pick_up(s, p["object_id"], p["item_id"]),
    "inspect":           lambda s, p: inspect_item(s, p["item_id"]),
    # 查看场景上的非拾取物品（如书架里的旧书 / 引擎盖上的褪色贴纸）
    "examine":           lambda s, p: examine_scene_item(s, p["object_id"], p["item_id"]),
    # 对象的互动步骤（如掀开画框 / 按电子屏向上箭头）
    "interact":          lambda s, p: interact(s, p["object_id"]),
    # 第 3 关电子屏上下箭头（门未开：↑开↓无动静；门已开：↑无动静↓关）
    "press_arrow":       lambda s, p: press_arrow(s, p["direction"]),
    "combine":           lambda s, p: combine(s, p["item_a"], p["item_b"]),
    "use":               lambda s, p: use(s, p["item_id"], p["target_id"]),
    "enter_password":    lambda s, p: enter_password(s, p["target_id"], p["code"]),
    # 第 3 关：铁皮盒旋转刻度盘（向左/向右每次一格，正好停在 6 才弹开）
    "turn_dial":         lambda s, p: turn_dial(s, p["object_id"], p["direction"]),
    # 第 3 关终局：走出卷帘门 → 通关结算
    "walk_out":          lambda s, p: walk_out(s),
}
