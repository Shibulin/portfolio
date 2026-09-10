# -*- coding: utf-8 -*-
"""
smoke_study_locked.py —— 第 1 关「书桌抽屉必须用完整钥匙打开」回归
- 验证未解锁前 pick_up code_paper / gear 被拦截
- 验证未带 key_full 时 use(key_full, desk) 失败
- 验证 use(key_full, desk) 后能正常拾取
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


def expect(label, cond):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {label}")
    if not cond:
        raise AssertionError(label)


def main():
    print("=== START（locked 模式重置一局） ===")
    call("/api/start", {})

    print("\n--- #A 走到组合钥匙步骤：list 书架 + 掀开画框 + 组合 ---")
    post("look", {"object_id": "bookshelf"})
    post("pick_up", {"object_id": "bookshelf", "item_id": "key_half_a"})
    post("look", {"object_id": "picture_frame"})
    post("interact", {"object_id": "picture_frame"})
    post("pick_up", {"object_id": "picture_frame", "item_id": "key_half_b"})
    post("combine", {"item_a": "key_half_a", "item_b": "key_half_b"})

    print("\n--- #B 未开锁：scene 隐藏 contains ---")
    # 当前已在 closeup(picture_frame)，先 back 再 look(desk)
    post("back")
    payload = post("look", {"object_id": "desk"})
    scene = payload["scene"]
    print("items:", scene["items"], "needs_item_for_unlock:", scene.get("needs_item_for_unlock"),
          "prereq_hint:", scene.get("prereq_hint"))
    expect("未开锁时 desk.items 为空", scene["items"] == [])
    expect("needs_item_for_unlock=key_full", scene.get("needs_item_for_unlock") == "key_full")
    expect("prereq_hint 含'完整钥匙'", scene.get("prereq_hint") and "完整钥匙" in scene["prereq_hint"])

    print("\n--- #C 未开锁时 pick_up code_paper 必须 400 ---")
    code, body = call("/api/action", {
        "action": "pick_up",
        "params": {"object_id": "desk", "item_id": "code_paper"},
    })
    print("HTTP", code, "detail:", body.get("detail"))
    expect("越权拾取 code_paper 返回 400", code == 400)
    expect("错误含'完整钥匙'", "完整钥匙" in body.get("detail", ""))

    print("\n--- #D use(key_full, desk) → 解锁 + contains 注入 ---")
    r = post("use", {"item_id": "key_full", "target_id": "desk"})
    print("narration:", r["narration"][:80])
    expect("desk_unlocked=True", r["state"]["desk_unlocked"] is True)
    expect("use 后 inventory 不含 code_paper（需后续拾取）",
           "code_paper" not in r["state"]["inventory"])
    # 重新 look desk，应能看到 contains 中有 code_paper / gear
    payload = post("look", {"object_id": "desk"})
    items = payload["scene"]["items"]
    print("items:", items)
    expect("解锁后 desk.items 含 code_paper", any(it["id"] == "code_paper" for it in items))
    expect("解锁后 desk.items 含 gear", any(it["id"] == "gear" for it in items))
    expect("needs_item_for_unlock 已被清空", payload["scene"].get("needs_item_for_unlock") is None)

    print("\n--- #F 拾取两个物品 → 进入保险箱 ---")
    post("pick_up", {"object_id": "desk", "item_id": "code_paper"})
    r = post("pick_up", {"object_id": "desk", "item_id": "gear"})
    expect("code_paper 入背包", "code_paper" in r["state"]["inventory"])
    expect("gear 入背包", "gear" in r["state"]["inventory"])

    print("\n--- #G 保险箱与钟表解耦：未修钟也能直接 397 → 得 study_key ---")
    # 验证：保险箱不再以"修钟"为前置；唯一开法 = 密码，开箱后手动拾取（有且只有一把）
    post("look", {"object_id": "safe"})
    r = post("look", {"object_id": "safe"})
    expect("未输密码时 items=[]（钥匙不可直接拾取）", r["scene"]["items"] == [])
    code, body = call("/api/action", {
        "action": "pick_up", "params": {"object_id": "safe", "item_id": "study_key"}})
    expect("越权拾取 → 400", code == 400)
    r = post("enter_password", {"target_id": "safe", "code": "397"})
    print("narration:", r["narration"][:80])
    expect("safe_unlocked=True（未修钟也能直接通过）",
           r["state"]["safe_unlocked"] is True)
    expect("开箱后钥匙未自动入背包（需拾取）", "study_key" not in r["state"]["inventory"])
    r = post("pick_up", {"object_id": "safe", "item_id": "study_key"})
    expect("拾取后 study_key 入背包", "study_key" in r["state"]["inventory"])
    expect("钟未修（clock_fixed=False）", r["state"]["clock_fixed"] is False)

    print("\n=== 🎉 smoke_study_locked 全部 PASS ===")


if __name__ == "__main__":
    main()
