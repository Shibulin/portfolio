"""Day 4 烟雾测试：三关密码全流程。
不走 LLM（直接操作），只验证后端动作路由与密码校验。
当前版（L3 图片流程）：
- 保险箱与钟表解耦：未修钟也能输密码
- 第 2 关：小票顺序 → 冰箱贴3/挂钟7/相册2/鱼缸8 → 3728 跨关
- 第 3 关：贴纸刻度6 → 铁皮盒 → 旧钥匙 → 挂锁 → 纸条529 → 电子屏 → 向上箭头 → 卷帘门逃出
"""
import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def call(path: str, body):
    method = "POST"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"_error": e.code, "_detail": body}


def expect(label, cond, detail=""):
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {label}" + (f"  ({detail})" if detail else ""))
    if not cond:
        sys.exit(1)


def reset():
    return call("/api/start", {})


def action(act, **params):
    return call("/api/action", {"action": act, "params": params})


# ============================================================ 第 1 关
print("=== 第 1 关 书房：抽屉锁 + 保险箱与钟表解耦 ===")
s = reset()
expect("开局在书房", s["state"]["room"] == "study")

print("\n  步骤 A：保险箱与钟表解耦 —— 钟未修也能直接输密码")
s = action("look", object_id="safe")
expect("进入保险箱特写", s["scene"]["mode"] == "closeup")
expect("未开箱时 items=[]（钥匙不可直接拾取）", s["scene"]["items"] == [])
expect("未开箱时显示密码提示", "密码" in (s["scene"]["prereq_hint"] or ""))
expect("未修钟时已显示 needs_password=3", s["scene"]["needs_password"] == {"length": 3})
# 输入错误密码仍然要拦截
r = action("enter_password", target_id="safe", code="999")
expect("错密码 400", "_error" in r and r["_error"] == 400)

print("\n  步骤 B：拿钥匙 + 组合 + 开抽屉 + 拿密码纸 + 拿齿轮")
action("back")
action("look", object_id="bookshelf")
action("pick_up", object_id="bookshelf", item_id="key_half_a")
action("look", object_id="picture_frame")
action("interact", object_id="picture_frame")
s = action("pick_up", object_id="picture_frame", item_id="key_half_b")
expect("钥匙②入背包", "key_half_b" in s["state"]["inventory"])
s = action("combine", item_a="key_half_a", item_b="key_half_b")
expect("组合得到完整钥匙", "key_full" in s["state"]["inventory"])

print("\n  步骤 B2：use 必须先 closeup 到目标")
action("back")
r = call("/api/action", {"action": "use", "params": {"item_id": "key_full", "target_id": "desk"}})
expect("panorama 下 use(key_full, desk) 必 400",
       "_error" in r and r["_error"] == 400, detail=str(r.get("_detail", ""))[:120])
expect("错误提示含'走近'", "走近" in str(r.get("_detail", "")))
# 走到别的对象的特写下 use → 也必须被拦截
action("look", object_id="bookshelf")
r = call("/api/action", {"action": "use", "params": {"item_id": "key_full", "target_id": "desk"}})
expect("closeup(bookshelf) 下 use(...,desk) 必 400",
       "_error" in r and r["_error"] == 400, detail=str(r.get("_detail", ""))[:120])

print("\n  步骤 B3：书桌必须先用 key_full 解锁")
action("look", object_id="desk")
r = action("look", object_id="desk")
expect("未开锁时 scene.items 为空", r["scene"]["items"] == [])
expect("未开锁时 needs_item_for_unlock=key_full",
       r["scene"].get("needs_item_for_unlock") == "key_full")
s = action("use", item_id="key_full", target_id="desk")
expect("用 key_full 后 desk_unlocked=True", s["state"]["desk_unlocked"] is True)
s = action("pick_up", object_id="desk", item_id="code_paper")
expect("拾取 code_paper 后入背包", "code_paper" in s["state"]["inventory"])
s = action("pick_up", object_id="desk", item_id="gear")
expect("拾取 gear 后入背包", "gear" in s["state"]["inventory"])

print("\n  步骤 C：保险箱与钟表解耦：钟未修也能直接 397")
# 不用先修钟也能输密码；唯一开法 = 密码 → 开箱后手动拾取（有且只有一把）
s = action("enter_password", target_id="safe", code="397")
expect("保险箱 397 直接通过（钟表不再是前置）",
       s["state"]["safe_unlocked"] is True)
expect("开箱后钥匙未自动入背包（需拾取）", "study_key" not in s["state"]["inventory"])
s = action("look", object_id="safe")
s = action("pick_up", object_id="safe", item_id="study_key")
expect("拾取后 study_key 入背包", "study_key" in s["state"]["inventory"])
expect("进度 ≥ 50%", s["state"]["progress"] >= 50, detail=f"{s['state']['progress']}%")

# ============================================================ 第 2 关
print("\n=== 第 2 关 客厅：图片流程（小票顺序 → 冰箱贴3/挂钟7/相册2/鱼缸8）===")
# 进客厅
action("look", object_id="door")
s = action("use", item_id="study_key", target_id="door")
expect("进入客厅", s["state"]["room"] == "living_room" and s["state"]["level"] == 2)
expect("背包已清空（本关物品本关消耗）", s["state"]["inventory"] == [])

print("\n  步骤 D：茶几 —— 外卖小票（顺序提示）+ 鱼食")
s = action("look", object_id="coffee_table")
ids = [it["id"] for it in s["scene"]["items"]]
expect("coffee_table 含 receipt_note", "receipt_note" in ids)
expect("coffee_table 含 fish_food", "fish_food" in ids)
s = action("pick_up", object_id="coffee_table", item_id="receipt_note")
expect("receipt_note 入背包", "receipt_note" in s["state"]["inventory"])
s = action("pick_up", object_id="coffee_table", item_id="fish_food")
expect("fish_food 入背包", "fish_food" in s["state"]["inventory"])
s = action("inspect", item_id="receipt_note")
expect("小票背面含顺序「冰箱→挂钟→相册→鱼缸」",
       all(x in s["narration"] for x in ("冰箱", "挂钟", "相册", "鱼缸")))
action("back")

print("\n  步骤 D2：冰箱贴 —— 未揭下拦截 → interact → 拾取 → 第1位：3")
s = action("look", object_id="fridge")
expect("fridge 未揭时 needs_interaction='揭下冰箱贴'",
       s["scene"].get("needs_interaction") == "揭下冰箱贴")
expect("fridge 未揭时 items=[]", s["scene"]["items"] == [])
r = call("/api/action", {"action": "pick_up", "params": {
    "object_id": "fridge", "item_id": "fridge_magnet"}})
expect("未揭下直接拾必 400", "_error" in r and r["_error"] == 400)
expect("错误信息含『揭下冰箱贴』", "揭下冰箱贴" in str(r.get("_detail", "")))
s = action("interact", object_id="fridge")
expect("magnet_revealed=True", s["state"]["magnet_revealed"] is True)
s = action("pick_up", object_id="fridge", item_id="fridge_magnet")
expect("fridge_magnet 入背包", "fridge_magnet" in s["state"]["inventory"])
s = action("inspect", item_id="fridge_magnet")
expect("冰箱贴背面「第1位：3」", "第1位" in s["narration"] and "3" in s["narration"])
action("back")

print("\n  步骤 D3：挂钟 —— 晾衣杆挑下 → 第2位：7")
s = action("look", object_id="wall_clock")
expect("挂钟初始 items=[]（太高）", s["scene"]["items"] == [])
r = call("/api/action", {"action": "use", "params": {
    "item_id": "receipt_note", "target_id": "wall_clock"}})
expect("无关工具碰挂钟必 400", "_error" in r and r["_error"] == 400)
s = action("look", object_id="sofa")
ids = [it["id"] for it in s["scene"]["items"]]
expect("沙发上有 drying_pole", "drying_pole" in ids)
s = action("pick_up", object_id="sofa", item_id="drying_pole")
expect("drying_pole 入背包", "drying_pole" in s["state"]["inventory"])
action("back")
action("look", object_id="wall_clock")
s = action("use", item_id="drying_pole", target_id="wall_clock")
expect("wall_clock_lowered=True", s["state"]["wall_clock_lowered"] is True)
ids = [it["id"] for it in s["scene"]["items"]]
expect("挂钟注入 clock_plaque", "clock_plaque" in ids)
s = action("pick_up", object_id="wall_clock", item_id="clock_plaque")
expect("clock_plaque 入背包", "clock_plaque" in s["state"]["inventory"])
s = action("inspect", item_id="clock_plaque")
expect("背板刻「第2位：7」", "第2位" in s["narration"] and "7" in s["narration"])
action("back")

print("\n  步骤 D4：相册 —— 翻开全家福 → 第3位：2")
s = action("look", object_id="tv_cabinet")
ids = [it["id"] for it in s["scene"]["items"]]
expect("电视柜上有 photo_album", "photo_album" in ids)
s = action("pick_up", object_id="tv_cabinet", item_id="photo_album")
expect("photo_album 入背包", "photo_album" in s["state"]["inventory"])
s = action("inspect", item_id="photo_album")
expect("照片背面「第3位：2」", "第3位" in s["narration"] and "2" in s["narration"])
action("back")

print("\n  步骤 E：鱼缸 —— 撒鱼食 → 数出 8 条（第4位：8）")
action("look", object_id="fish_tank")
s = action("use", item_id="fish_food", target_id="fish_tank")
expect("fish_fed=True", s["state"]["fish_fed"] is True)
expect("旁白含「8 条」", "8 条" in s["narration"])
expect("fish_food 已消耗", "fish_food" not in s["state"]["inventory"])
action("back")

print("\n  步骤 H：错密码 400 + 对密码 3728 → 直接跨关")
s = action("look", object_id="garage_door")
expect("needs_password length=4", s["scene"]["needs_password"] == {"length": 4})
r = action("enter_password", target_id="garage_door", code="1234")
expect("错密码 400", "_error" in r and r["_error"] == 400)
s = action("enter_password", target_id="garage_door", code="3728")
expect("跨入第 3 关（room=garage，level=3）",
       s["state"]["room"] == "garage" and s["state"]["level"] == 3)
expect("进度 ≥ 70", s["state"]["progress"] >= 70, detail=f"{s['state']['progress']}%")
expect("narration 含「密码正确」或「升起」",
       "密码正确" in s["narration"] or "升起" in s["narration"])
expect("narration 不再含「焊死」", "焊死" not in s["narration"])

# ============================================================ 第 3 关
print("\n=== 第 3 关 车库：贴纸刻度6 → 铁皮盒 → 旧钥匙 → 挂锁 → 纸条529 → 电子屏 → 卷帘门 ===")

print("\n  步骤 I：浏览 —— 遥控器损坏 + 电子屏待机")
s = action("look", object_id="remote")
expect("遥控器旁白含「电池仓」（损坏设定）",
       "电池仓" in s["narration"] or "裂开" in s["narration"])
r = call("/api/action", {"action": "start_radio_unlock", "params": {}})
expect("旧音响动作已删除 → 400", "_error" in r and r["_error"] == 400)
action("back")
s = action("look", object_id="keypad")
expect("keypad needs_password length=3",
       s["scene"]["needs_password"] == {"length": 3})
expect("未输密码前无向上箭头互动", s["scene"].get("needs_interaction") is None)
r = action("interact", object_id="keypad")
expect("未输密码按箭头必 400（玻璃面板盖着）",
       "_error" in r and r["_error"] == 400)
r = action("enter_password", target_id="keypad", code="111")
expect("keypad 错密码 400", "_error" in r and r["_error"] == 400)
action("back")

print("\n  步骤 J：汽车 → 引擎盖 → 褪色贴纸（刻度 6 线索）")
s = action("look", object_id="car")
ids = [it["id"] for it in s["scene"]["items"]]
expect("car 含 car_sticker（不可拾取）",
       any(it["id"] == "car_sticker" and it["pickable"] is False for it in s["scene"]["items"]))
r = call("/api/action", {"action": "pick_up", "params": {
    "object_id": "car", "item_id": "car_sticker"}})
expect("贴纸不可拾取 → 400", "_error" in r and r["_error"] == 400)
s = action("examine", object_id="car", item_id="car_sticker")
expect("贴纸旁白含「刻度 6」", "6" in s["narration"] and "旋钮" in s["narration"])
action("back")

print("\n  步骤 K：挂墙工具板 → 铁皮盒刻度盘（向左/向右逐步旋转）→ 旧钥匙")
s = action("look", object_id="tool_board")
expect("tool_board 初始 items=[]（盒子锁着）", s["scene"]["items"] == [])
expect("needs_dial 显示起始位置 0",
       s["scene"].get("needs_dial") == {"position": 0})
r = call("/api/action", {"action": "turn_dial", "params": {
    "object_id": "tool_board", "direction": "up"}})
expect("非法方向（up）→ 400", "_error" in r and r["_error"] == 400)
r = action("turn_dial", object_id="tool_board", direction="left")
expect("从 0 向左一格 → 循环到 12，盒子未开",
       r["state"]["dial_position"] == 12 and r["state"]["tin_box_opened"] is False)
expect("旁白报当前刻度 12", "停在 12" in r["narration"])
r = action("turn_dial", object_id="tool_board", direction="right")
expect("从 12 向右一格 → 循环回 1", r["state"]["dial_position"] == 1)
# 连续向右拧到 6：1→2→3→4→5→6
for pos in (2, 3, 4, 5):
    r = action("turn_dial", object_id="tool_board", direction="right")
    expect(f"向右拧到 {pos}，盒子未开",
           r["state"]["dial_position"] == pos and r["state"]["tin_box_opened"] is False)
r = action("turn_dial", object_id="tool_board", direction="right")
expect("正好停在 6 → tin_box_opened=True",
       r["state"]["dial_position"] == 6 and r["state"]["tin_box_opened"] is True)
ids = [it["id"] for it in r["scene"]["items"]]
expect("tool_board 注入 old_key", "old_key" in ids)
expect("打开后 needs_dial 消失", r["scene"].get("needs_dial") is None)
r = action("turn_dial", object_id="tool_board", direction="right")
expect("已打开后再转 → 400", "_error" in r and r["_error"] == 400)
s = action("pick_up", object_id="tool_board", item_id="old_key")
expect("old_key 入背包", "old_key" in s["state"]["inventory"])
action("back")

print("\n  步骤 L：工具箱 → 挂锁 → 纸条 529")
s = action("look", object_id="tool_box")
expect("未开锁时 tool_box items=[]", s["scene"]["items"] == [])
action("back")
r = call("/api/action", {"action": "use", "params": {
    "item_id": "old_key", "target_id": "tool_box"}})
expect("未进特写就 use 必 400", "_error" in r and r["_error"] == 400)
action("look", object_id="tool_box")
s = action("use", item_id="old_key", target_id="tool_box")
expect("padlock_unlocked=True", s["state"]["padlock_unlocked"] is True)
expect("old_key 已消耗", "old_key" not in s["state"]["inventory"])
ids = [it["id"] for it in s["scene"]["items"]]
expect("tool_box 注入 note_529", "note_529" in ids)
s = action("pick_up", object_id="tool_box", item_id="note_529")
expect("note_529 入背包", "note_529" in s["state"]["inventory"])
s = action("inspect", item_id="note_529")
expect("纸条写着「5 2 9」", all(x in s["narration"] for x in ("5", "2", "9")))
action("back")

print("\n  步骤 M：电子屏 529 → 面板弹开 → 上下箭头弹窗（关门态：↓无动静/↑开门）")
s = action("look", object_id="keypad")
s = action("enter_password", target_id="keypad", code="529")
expect("keypad_unlocked=True", s["state"]["keypad_unlocked"] is True)
expect("尚未通关（还需按箭头+走出）", s["state"]["finished"] is False)
expect("narration 含「绿灯」与「弹开」",
       "绿灯" in s["narration"] and "弹开" in s["narration"])
expect("面板弹开后 needs_interaction='查看电子屏（上下箭头）'",
       s["scene"].get("needs_interaction") == "查看电子屏（上下箭头）")
r = action("press_arrow", direction="left")
expect("非法方向（left）→ 400", "_error" in r and r["_error"] == 400)
r = action("press_arrow", direction="down")
expect("门未开按 ↓ → 无动静（shutter 仍 False）",
       "_error" not in r and r["state"]["shutter_opened"] is False
       and "没有任何动静" in r["narration"])
r = action("press_arrow", direction="up")
expect("门未开按 ↑ → shutter_opened=True",
       "_error" not in r and r["state"]["shutter_opened"] is True
       and "升起" in r["narration"])

print("\n  步骤 M2：门已开 → ↑无动静 / ↓关门 / 再 ↑重开（可反复开关）")
r = action("press_arrow", direction="up")
expect("门已开按 ↑ → 无动静（shutter 仍 True）",
       "_error" not in r and r["state"]["shutter_opened"] is True
       and ("升到顶" in r["narration"] or "没有别的动静" in r["narration"]))
r = action("press_arrow", direction="down")
expect("门已开按 ↓ → 卷帘门落下（shutter_opened=False）",
       "_error" not in r and r["state"]["shutter_opened"] is False
       and "落下" in r["narration"])
s = action("look", object_id="exit_door")
expect("关门后 exit_door 不显示「走出卷帘门」",
       s["scene"].get("needs_interaction") is None)
action("look", object_id="keypad")
r = action("press_arrow", direction="up")
expect("再按 ↑ 重新升起", r["state"]["shutter_opened"] is True)

print("\n  步骤 N：查看卷帘门 → 走出卷帘门 → game_over 结算")
s = action("back")
s = action("look", object_id="exit_door")
expect("查看卷帘门尚未通关（需点击走出）", s["state"]["finished"] is False)
expect("卷帘门特写显示「走出卷帘门」按钮",
       s["scene"].get("needs_interaction") == "走出卷帘门")
r = call("/api/action", {"action": "walk_out", "params": {}})
expect("走出卷帘门 → finished=True", r["state"]["finished"] is True)
expect("进度 100", r["state"]["progress"] == 100, detail=f"{r['state']['progress']}%")
expect("结算旁白含「用时」与「逃出」",
       "用时" in r["narration"] and "逃出" in r["narration"])
r = call("/api/action", {"action": "walk_out", "params": {}})
expect("重复走出幂等（已通关提示）", "已经逃出" in r["narration"])

print("\n=== 🎉 smoke_day4 全部 PASS（三关全流程） ===")
