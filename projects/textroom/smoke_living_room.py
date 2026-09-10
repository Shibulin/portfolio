# -*- coding: utf-8 -*-
"""
Day-X 第 2 关回归 —— 图片流程版
- 探索① 茶几：外卖小票（顺序提示：冰箱→挂钟→相册→鱼缸）+ 鱼食
- 探索② 冰箱贴：揭下红色圆形 → 背面「第1位：3」
- 探索③ 挂钟：太高够不到 → 沙发晾衣杆 use(drying_pole, wall_clock) → 背板「第2位：7」
- 探索④ 相册：电视柜 → 翻开全家福背面「第3位：2」
- 探索⑤ 鱼缸：水浑 → use(fish_food, fish_tank) → 数出 8 条（第4位：8）
- 整理线索 3-7-2-8 → 车库门跨关
"""
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def call(path, body=None):
    method = "POST" if body is not None else "GET"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def post(action, params=None):
    code, body = call("/api/action", {"action": action, "params": params or {}})
    if code != 200:
        raise RuntimeError(f"action {action} 失败：HTTP {code} {body}")
    return body


def post_expect_fail(label, action, params=None):
    """预期失败的请求：返回 (http_code, body)。"""
    print(f"  [预期失败] {label}")
    code, body = call("/api/action", {"action": action, "params": params or {}})
    print(f"    → HTTP {code} {body.get('detail','')}")
    return code, body


def expect(label, cond, detail=None):
    status = "PASS" if cond else "FAIL"
    suffix = f"（{detail}）" if detail and not cond else ""
    print(f"  [{status}] {label}{suffix}")
    if not cond:
        raise AssertionError(label)


def main():
    print("=== START ===")
    call("/api/start", {})

    # ============================================================ 第 1 关：快速通过
    print("\n=== 快速通过第 1 关：组合钥匙 → 桌 → 钟 → 保险箱 397 ===")
    post("look", {"object_id": "bookshelf"})
    post("examine", {"object_id": "bookshelf", "item_id": "old_book"})
    post("pick_up", {"object_id": "bookshelf", "item_id": "key_half_a"})
    post("back")
    post("look", {"object_id": "picture_frame"})
    post("interact", {"object_id": "picture_frame"})
    post("pick_up", {"object_id": "picture_frame", "item_id": "key_half_b"})
    post("back")
    post("combine", {"item_a": "key_half_a", "item_b": "key_half_b"})
    post("look", {"object_id": "desk"})
    post("use", {"item_id": "key_full", "target_id": "desk"})
    post("look", {"object_id": "desk"})
    post("pick_up", {"object_id": "desk", "item_id": "code_paper"})
    post("look", {"object_id": "desk"})
    post("pick_up", {"object_id": "desk", "item_id": "gear"})
    post("look", {"object_id": "clock"})
    post("use", {"item_id": "gear", "target_id": "clock"})
    post("look", {"object_id": "safe"})
    r = post("enter_password", {"target_id": "safe", "code": "397"})
    expect("保险箱开启（safe_unlocked=True）", r["state"]["safe_unlocked"] is True)
    r = post("pick_up", {"object_id": "safe", "item_id": "study_key"})
    expect("拾取后 study_key 入背包", "study_key" in r["state"]["inventory"])
    post("look", {"object_id": "door"})
    r = post("use", {"item_id": "study_key", "target_id": "door"})
    expect("跨入第 2 关", r["state"]["room"] == "living_room" and r["state"]["level"] == 2)
    expect("背包已清空（本关物品本关消耗）", r["state"]["inventory"] == [])
    expect("第 1 关旧线索已清空（线索不跨关）",
           all("画框" not in c and "保险箱" not in c and "齿轮" not in c
               for c in r["state"]["clues"]))

    # ============================================================ 探索① 茶几
    print("\n=== 探索① 茶几：外卖小票（顺序提示）+ 鱼食 ===")
    s = post("look", {"object_id": "main_gate"})
    expect("大门旁白含「焊死」（唯一出口设定）", "焊死" in s["narration"])
    post("back")
    s = post("look", {"object_id": "coffee_table"})
    ids = [it["id"] for it in s["scene"]["items"]]
    expect("茶几 items 含 receipt_note", "receipt_note" in ids)
    expect("茶几 items 含 fish_food", "fish_food" in ids)
    s = post("pick_up", {"object_id": "coffee_table", "item_id": "receipt_note"})
    expect("receipt_note 入背包", "receipt_note" in s["state"]["inventory"])
    s = post("pick_up", {"object_id": "coffee_table", "item_id": "fish_food"})
    expect("fish_food 入背包", "fish_food" in s["state"]["inventory"])
    r = post("inspect", {"item_id": "receipt_note"})
    expect("小票背面含顺序「冰箱 → 挂钟 → 相册 → 鱼缸」",
           "冰箱" in r["narration"] and "挂钟" in r["narration"]
           and "相册" in r["narration"] and "鱼缸" in r["narration"])
    post("back")

    # ============================================================ 探索② 冰箱贴
    print("\n=== 探索② 冰箱贴：揭下红色圆形 → 「第1位：3」 ===")
    s = post("look", {"object_id": "fridge"})
    expect("未揭下时 needs_interaction='揭下冰箱贴'",
           s["scene"].get("needs_interaction") == "揭下冰箱贴")
    expect("未揭下时 items=[]", s["scene"]["items"] == [])
    code, body = post_expect_fail("未揭下时直接拾 fridge_magnet", "pick_up",
                                  {"object_id": "fridge", "item_id": "fridge_magnet"})
    expect("未揭下拾取必 400", code == 400)
    expect("错误信息含「揭下冰箱贴」", "揭下冰箱贴" in str(body.get("detail", "")))
    s = post("interact", {"object_id": "fridge"})
    expect("magnet_revealed=True", s["state"]["magnet_revealed"] is True)
    expect("旁白含「红色圆形」", "红色圆形" in s["narration"])
    s = post("pick_up", {"object_id": "fridge", "item_id": "fridge_magnet"})
    expect("fridge_magnet 入背包", "fridge_magnet" in s["state"]["inventory"])
    r = post("inspect", {"item_id": "fridge_magnet"})
    expect("背面写「第1位：3」", "第1位" in r["narration"] and "3" in r["narration"])
    code, body = post_expect_fail("重复 interact 揭冰箱贴", "interact", {"object_id": "fridge"})
    expect("重复揭必 400", code == 400)
    post("back")

    # ============================================================ 探索③ 挂钟（晾衣杆）
    print("\n=== 探索③ 挂钟：晾衣杆挑下 → 背板「第2位：7」 ===")
    s = post("look", {"object_id": "wall_clock"})
    expect("挂钟初始 items=[]（太高拿不到）", s["scene"]["items"] == [])
    code, body = post_expect_fail("空手用 receipt_note 碰挂钟", "use",
                                  {"item_id": "receipt_note", "target_id": "wall_clock"})
    expect("无关工具必 400", code == 400)
    s = post("look", {"object_id": "sofa"})
    ids = [it["id"] for it in s["scene"]["items"]]
    expect("沙发上有 drying_pole", "drying_pole" in ids)
    s = post("pick_up", {"object_id": "sofa", "item_id": "drying_pole"})
    expect("drying_pole 入背包", "drying_pole" in s["state"]["inventory"])
    post("back")
    post("look", {"object_id": "wall_clock"})
    s = post("use", {"item_id": "drying_pole", "target_id": "wall_clock"})
    expect("wall_clock_lowered=True", s["state"]["wall_clock_lowered"] is True)
    expect("旁白含「挑」+「第2位」", "挑" in s["narration"] and "第2位" in s["narration"])
    ids = [it["id"] for it in s["scene"]["items"]]
    expect("挂钟出现 clock_plaque", "clock_plaque" in ids)
    s = post("pick_up", {"object_id": "wall_clock", "item_id": "clock_plaque"})
    expect("clock_plaque 入背包", "clock_plaque" in s["state"]["inventory"])
    r = post("inspect", {"item_id": "clock_plaque"})
    expect("背板刻「第2位：7」", "第2位" in r["narration"] and "7" in r["narration"])
    code, body = post_expect_fail("重复挑挂钟", "use",
                                  {"item_id": "drying_pole", "target_id": "wall_clock"})
    expect("重复挑必 400（晾衣杆未消耗仍可用）", code == 400)
    post("back")

    # ============================================================ 探索④ 相册
    print("\n=== 探索④ 相册：全家福背面「第3位：2」 ===")
    s = post("look", {"object_id": "tv_cabinet"})
    ids = [it["id"] for it in s["scene"]["items"]]
    expect("电视柜上有 photo_album", "photo_album" in ids)
    s = post("pick_up", {"object_id": "tv_cabinet", "item_id": "photo_album"})
    expect("photo_album 入背包", "photo_album" in s["state"]["inventory"])
    r = post("inspect", {"item_id": "photo_album"})
    expect("照片背面写「第3位：2」", "第3位" in r["narration"] and "2" in r["narration"])
    post("back")

    # ============================================================ 探索⑤ 鱼缸
    print("\n=== 探索⑤ 鱼缸：撒鱼食 → 数出 8 条 ===")
    post("look", {"object_id": "fish_tank"})
    s = post("use", {"item_id": "fish_food", "target_id": "fish_tank"})
    expect("fish_fed=True", s["state"]["fish_fed"] is True)
    expect("旁白含「8 条」", "8 条" in s["narration"])
    expect("fish_food 已消耗", "fish_food" not in s["state"]["inventory"])
    code, body = post_expect_fail("重复撒鱼食", "use",
                                  {"item_id": "fish_food", "target_id": "fish_tank"})
    expect("重复撒必 400", code == 400)
    post("back")

    # ============================================================ 整理线索 → 3728 → 跨关
    print("\n=== 整理线索：3-7-2-8 → 车库门 ===")
    s = post("look", {"object_id": "garage_door"})
    expect("needs_password length=4", s["scene"]["needs_password"] == {"length": 4})
    code, body = post_expect_fail("错密码 1111", "enter_password",
                                  {"target_id": "garage_door", "code": "1111"})
    expect("错密码必 400", code == 400)
    s = post("enter_password", {"target_id": "garage_door", "code": "3728"})
    expect("跨入第 3 关（room=garage，level=3）",
           s["state"]["room"] == "garage" and s["state"]["level"] == 3)
    expect("进度 ≥ 70", s["state"]["progress"] >= 70, detail=f"{s['state']['progress']}%")
    expect("旁白含「密码正确」或「升起」",
           "密码正确" in s["narration"] or "升起" in s["narration"])

    print("\n=== ALL PASS ===")


if __name__ == "__main__":
    main()
