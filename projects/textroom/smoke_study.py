# -*- coding: utf-8 -*-
"""
Day-4 第 1 关回归（修复后）
- 验证：旧书引导 + 画框掀开前置 + 密码纸信息 + 钟表 3 时 45 分精度
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
    print("=== START ===")
    call("/api/start", {})

    print("\n--- #1 书架特写：旧书 + 钥匙① (旧书 pickable=False) ---")
    r = post("look", {"object_id": "bookshelf"})
    items = r["scene"]["items"]
    print("narration:", r["narration"][:80])
    expect("书架包含旧书", any(it["id"] == "old_book" for it in items))
    expect("旧书 pickable=False", any(it["id"] == "old_book" and it.get("pickable") is False for it in items))
    expect("书架包含半把钥匙①", any(it["id"] == "key_half_a" for it in items))

    print("\n--- #1b 查看旧书（examine，不进背包） ---")
    r = post("examine", {"object_id": "bookshelf", "item_id": "old_book"})
    print("narration:", r["narration"][:120])
    expect("examine 含「画框之后」", "画框之后" in r["narration"] or "画框" in r["narration"])
    expect("旧书未入背包", "old_book" not in r["state"]["inventory"])

    print("\n--- #2 画框未掀开：钥匙② 不可见 ---")
    r = post("look", {"object_id": "picture_frame"})
    print("items:", r["scene"]["items"])
    expect("画框未掀开时 items=[]", r["scene"]["items"] == [])
    expect("needs_interaction='掀开画框'", r["scene"]["needs_interaction"] == "掀开画框")

    print("\n--- #2b 越权拾取被拦截 ---")
    code, body = call("/api/action", {
        "action": "pick_up",
        "params": {"object_id": "picture_frame", "item_id": "key_half_b"},
    })
    expect("越权 pick_up 返回 400", code == 400)
    expect("错误信息含'掀开画框'", "掀开画框" in body.get("detail", ""))

    print("\n--- #2c interact 后，钥匙② 可见 ---")
    r = post("interact", {"object_id": "picture_frame"})
    items = r["scene"]["items"]
    print("narration:", r["narration"][:80])
    print("items:", items)
    expect("掀开后钥匙②出现", any(it["id"] == "key_half_b" for it in items))

    print("\n--- 走完钥匙组合 → 开桌 → 拿齿轮 + 密码纸 ---")
    post("back")
    post("look", {"object_id": "bookshelf"})
    post("pick_up", {"object_id": "bookshelf", "item_id": "key_half_a"})
    post("look", {"object_id": "picture_frame"})
    post("pick_up", {"object_id": "picture_frame", "item_id": "key_half_b"})
    post("combine", {"item_a": "key_half_a", "item_b": "key_half_b"})
    # 必须先 look(desk) 进特写，再 use
    post("look", {"object_id": "desk"})
    r = post("use", {"item_id": "key_full", "target_id": "desk"})
    expect("抽屉打开后背**不含**密码纸（需重新 look + pick_up）",
           "code_paper" not in r["state"]["inventory"])
    expect("抽屉打开后背**不含**齿轮（需重新 look + pick_up）",
           "gear" not in r["state"]["inventory"])
    expect("desk_unlocked=True", r["state"]["desk_unlocked"] is True)
    # 抽屉解锁后，重新 look desk，并分别拾取
    post("look", {"object_id": "desk"})
    r = post("pick_up", {"object_id": "desk", "item_id": "code_paper"})
    expect("拾取 code_paper 后入背包", "code_paper" in r["state"]["inventory"])
    r = post("pick_up", {"object_id": "desk", "item_id": "gear"})
    expect("拾取 gear 后入背包", "gear" in r["state"]["inventory"])

    print("\n--- #4 装齿轮旁白：时针 3 / 分针 9（隐晦化后不报「3 时 45 分」） ---")
    post("look", {"object_id": "clock"})
    r = post("use", {"item_id": "gear", "target_id": "clock"})
    print("narration:", r["narration"])
    # 隐晦化：只描述指针指 3、9，不再直接报「3 时 45 分」
    expect("旁白含「时针」", "时针" in r["narration"])
    expect("旁白含「分针」", "分针" in r["narration"])
    expect("旁白含「指 3」", "指 3" in r["narration"])
    expect("旁白含「指 9」", "指 9" in r["narration"])
    expect("隐晦化后旁白不再报「3 时 45 分」",
           "3 时 45 分" not in r["narration"] and "3时45分" not in r["narration"])
    # state.clues 里也只保留隐晦版描述
    clue_texts = " ".join(r["state"]["clues"])
    expect("clue 含「时针指 3、分针指 9」",
           "时针指 3" in clue_texts and "分针指 9" in clue_texts)

    print("\n--- #3 inspect 密码纸：含「第三位」+「7」+「三位数」（隐晦化） ---")
    r = post("inspect", {"item_id": "code_paper"})
    print("narration:", r["narration"])
    expect("密码纸 inspection 含「第三位」", "第三位" in r["narration"])
    expect("密码纸 inspection 含「7」", "7" in r["narration"])
    expect("密码纸 inspection 含「三位数」", "三位数" in r["narration"])
    # 不再直接说「第三位是 7」
    expect("隐晦化后不再直接报「第三位是 7」",
           "第三位是 7" not in r["narration"] and "第三位 — 7" in r["narration"])

    print("\n--- 保险箱 397：唯一开法 = 密码 → 开箱后手动拾取（有且只有一把） ---")
    post("look", {"object_id": "safe"})
    r = post("look", {"object_id": "safe"})
    expect("未输密码时 items=[]（钥匙不可直接拾取）", r["scene"]["items"] == [])
    r = post("enter_password", {"target_id": "safe", "code": "397"})
    print("narration:", r["narration"])
    expect("safe_unlocked=True", r["state"]["safe_unlocked"] is True)
    expect("开箱后钥匙未自动入背包（需拾取）", "study_key" not in r["state"]["inventory"])
    r = post("pick_up", {"object_id": "safe", "item_id": "study_key"})
    expect("拾取后 study_key 入背包", "study_key" in r["state"]["inventory"])

    print("\n=== 🎉 全部 PASS ===")


if __name__ == "__main__":
    main()
