# -*- coding: utf-8 -*-
"""一次性回归脚本：跑通第 1 关完整动作链，验证 Day 3 后端逻辑。"""
import json
import urllib.request

BASE = "http://127.0.0.1:8000"


def call(path, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method="POST" if body is not None else "GET",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def action(act, **params):
    print(f"\n=== {act}({params}) ===")
    res = call("/api/action", {"action": act, "params": params})
    print("旁白：", res["narration"])
    print("背包：", [i["name"] for i in res["inventory_detail"]])
    print("线索数：", len(res["state"]["clues"]), "  进度：", res["state"]["progress"], "%")
    print("场景：", res["scene"]["mode"], "/", res["scene"].get("object_name") or res["scene"]["room_name"])
    return res


# 开局
print("=== START ===")
start = call("/api/start", {})
print("旁白：", start["narration"])
print("文字按钮：", [o["name"] for o in start["scene"]["objects"]])

# 用 /api/state 拿到背包详情
st = call("/api/state", None)
print("背包：", [i["name"] for i in st["inventory_detail"]])

# 第 1 关 流程
action("look", object_id="bookshelf")
action("pick_up", object_id="bookshelf", item_id="key_half_a")
action("back")
action("look", object_id="picture_frame")
action("pick_up", object_id="picture_frame", item_id="key_half_b")
action("back")
action("combine", item_a="key_half_a", item_b="key_half_b")
action("use", item_id="key_full", target_id="desk")
action("use", item_id="gear", target_id="clock")
# 保险箱（密码入口 Day 4 做，这里先 look 验证）
action("look", object_id="safe")
# 期望：进客厅（需要先有书房门钥匙，先手动加 Day 4 才能拿；这里停在书房状态）
print("\n=== Done. State snapshot ===")
final = call("/api/state", None)
print("room =", final["state"]["room"], "level =", final["state"]["level"])
print("progress =", final["state"]["progress"], "%")
print("clock_fixed =", final["state"]["clock_fixed"])
print("inventory =", [i["name"] for i in final["inventory_detail"]])
