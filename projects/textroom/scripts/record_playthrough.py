"""录制 TextRoom 三关全流程通关视频（真实 UI 点击驱动）。

用法：
    cd D:/A-work/WorkBuddy/TextRoom
    set PLAYWRIGHT_BROWSERS_PATH=D:/A-work/WorkBuddy/TextRoom/.pw-browsers
    .venv/Scripts/python.exe scripts/record_playthrough.py [输出文件名]

依赖：playwright（已装入 .venv），Chromium（已装到 .pw-browsers）。
"""
import json
import os
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "http://127.0.0.1:8000"
OUT_DIR = ROOT / "videos"
OUT_DIR.mkdir(exist_ok=True)
OUT_NAME = sys.argv[1] if len(sys.argv) > 1 else "textroom_full_playthrough.webm"
OUT_PATH = OUT_DIR / OUT_NAME

JS_SCENE = """() => {
  const d = (typeof lastData !== 'undefined') ? lastData : null;
  if (!d || !d.scene) return null;
  return {mode: d.scene.mode, object_id: d.scene.object_id || null,
          items: (d.scene.items || []).map(i => i.id),
          needs_interaction: d.scene.needs_interaction || null,
          needs_password: d.scene.needs_password || null,
          needs_dial: d.scene.needs_dial || null};
}"""
JS_STATE = """() => {
  const d = (typeof lastData !== 'undefined') ? lastData : null;
  if (!d || !d.state) return null;
  return {room: d.state.room, level: d.state.level, progress: d.state.progress,
          inventory: d.state.inventory, clues: d.state.clues,
          finished: d.state.finished,
          dial_position: d.state.dial_position,
          shutter_opened: d.state.shutter_opened};
}"""


def wait_until(page, js, pred, timeout=6000, step_desc=""):
    """轮询执行 js 直到 pred(结果) 为真。"""
    deadline = time.time() + timeout / 1000
    last = None
    while time.time() < deadline:
        last = page.evaluate(js)
        if pred(last):
            return last
        time.sleep(0.18)
    raise RuntimeError(f"等待超时: {step_desc} -> {last}")


def see(page, desc):
    st = wait_until(page, JS_STATE, lambda s: s is not None, 4000, f"拿到 state @{desc}")
    print(f"  · {desc}  [{st['room']}/L{st['level']} {st['progress']}%] "
          f"inv={st['inventory']} clue={len(st['clues'])}", flush=True)
    return st


def click_hotspot(page, oid, wait=1.0):
    page.locator(f".hotspot[data-id=\"{oid}\"]").click()
    wait_until(page, JS_SCENE,
               lambda sc: sc and sc["mode"] == "closeup" and sc["object_id"] == oid,
               6000, f"进入 {oid} 特写")
    time.sleep(wait)


def click_back(page, wait=0.7):
    page.locator("#closeupClose").click()
    wait_until(page, JS_SCENE, lambda sc: sc and sc["mode"] == "panorama", 6000, "返回全景")
    time.sleep(wait)


def click_act(page, text, exact=False, wait=1.0, timeout=6000, desc=""):
    """在弹窗动作区点击文本匹配的按钮（text 为子串，或 exact 精确匹配）。"""
    loc = page.locator("#closeupActs .act-btn")
    deadline = time.time() + timeout / 1000
    target = None
    while time.time() < deadline:
        for i in range(loc.count()):
            t = loc.nth(i).text_content() or ""
            if (t == text) if exact else (text in t):
                target = loc.nth(i)
                break
        if target:
            break
        time.sleep(0.18)
    if target is None:
        raise RuntimeError(f"找不到动作按钮: {text} @ {desc}")
    target.click()
    time.sleep(wait)
    return target


def click_menu(page, text, exact=False, wait=0.9, timeout=5000):
    """点击弹出的物品菜单/目标选择中的按钮（.act-btn 全局扫描，文本子串）。"""
    loc = page.locator(".act-btn")
    deadline = time.time() + timeout / 1000
    target = None
    while time.time() < deadline:
        n = loc.count()
        # 只挑"可见且处于弹层"的：取最后一个遮罩层里的按钮即可（菜单刚弹出在最上层）
        for i in range(n - 1, -1, -1):
            t = (loc.nth(i).text_content() or "").strip()
            if ((t == text) if exact else (text in t)) and loc.nth(i).is_visible():
                target = loc.nth(i)
                break
        if target:
            break
        time.sleep(0.18)
    if target is None:
        raise RuntimeError(f"找不到菜单按钮: {text}")
    target.click()
    time.sleep(wait)


def open_inv_item(page, item_id, desc=""):
    page.locator(f".inv-item[data-id=\"{item_id}\"]").click()
    time.sleep(0.6)


def combine_items(page, a, b):
    """在背包点击物品 a → 组合 → 选 b。"""
    open_inv_item(page, a, f"组合入口 {a}")
    click_menu(page, "组合", exact=True, wait=0.6)
    # 目标列表里的组合按钮：文案“与 X 组合”，X 就是 b 的名字
    name_b = page.evaluate(
        "(id) => { const d=(typeof lastData!=='undefined')?lastData:null; "
        "const it=(d.inventory_detail||[]).find(x=>x.id===id); return it?it.name:''; }", b)
    click_menu(page, f"与 {name_b} 组合", wait=1.0)


def pick_item(page, obj_id, item_id, desc=""):
    """在已打开的 obj 特写里拾取 item_id（按 scene.items 顺序定位按钮）。"""
    sc = wait_until(page, JS_SCENE,
                    lambda s: s and s["mode"] == "closeup" and item_id in s["items"],
                    6000, f"{item_id} 出现在 {obj_id} 特写")
    idx = sc["items"].index(item_id)
    # 第 idx 个“拾取”按钮
    btns = page.locator("#closeupActs .act-btn")
    deadline = time.time() + 5
    while time.time() < deadline:
        hits = [i for i in range(btns.count())
                if (btns.nth(i).text_content() or "").strip().startswith("拾取")]
        if len(hits) > idx:
            btns.nth(hits[idx]).click()
            break
        time.sleep(0.18)
    # 等物品进背包
    wait_until(page, JS_STATE, lambda s: s and item_id in s["inventory"], 6000,
               f"{item_id} 入背包")
    time.sleep(0.7)


def enter_pwd(page, code):
    """在密码弹窗中逐位点击后按 OK。"""
    for ch in str(code):
        page.locator(f".pad-key[data-k=\"{ch}\"]").click()
        time.sleep(0.15)
    page.locator('.pad-key[data-k="OK"]').click()


def dismiss_gate(page, hold=2.6):
    """白底关卡衔接页：等它出现 → 展示 → 点击任意位置继续。"""
    try:
        page.locator("#levelGate").wait_for(state="visible", timeout=6000)
    except Exception:
        return                      # 没有衔接页（如未跨关）
    time.sleep(hold)
    page.locator("#levelGate").click(force=True)
    time.sleep(1.2)


# ---- 画面节奏：关键画面的停留时长（秒），改这里即可调节视频快慢 ----
COVER_HOLD = 3.0     # 开始游戏界面（点「开始游戏」之前）
ROOM_HOLD  = 2.5     # 进入某关全景后的扫视（让观众看清场景再动手）


def admire(page, seconds, desc=""):
    """纯停留：镜头在当前画面上多留一会儿，不点击、不滚动。"""
    if seconds > 0:
        print(f"  ⏸ {desc} 停留 {seconds:g}s", flush=True)
        time.sleep(seconds)


def cross_room(page, expected_room, desc):
    """跨关动作后：等 room 真正切换 → 点掉衔接页 → 让新关卡全景停留一下。"""
    st = wait_until(page, JS_STATE, lambda s: s and s["room"] == expected_room,
                    8000, f"跨入 {expected_room} @{desc}")
    dismiss_gate(page)
    admire(page, ROOM_HOLD, f"{expected_room} 全景")
    print(f"  · 已进入 {expected_room}  L{st['level']} {st['progress']}%", flush=True)
    return st


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=str(OUT_DIR / "_rec"),
            record_video_size={"width": 1280, "height": 800},
        )
        page = ctx.new_page()
        page.goto(URL)
        # ① 先把「开始游戏」封面完整录进视频（此前一点开始就直接跳过了）
        page.wait_for_selector("#cover-btn", timeout=8000)
        admire(page, COVER_HOLD, "开始游戏界面")
        # ② 点击开始
        page.locator("#cover-btn").click()
        see(page, "开局：书房全景")
        # ③ 进入第 1 关先扫视全景，别一上来就点热点
        admire(page, ROOM_HOLD, "第 1 关 · 书房全景")

        # ============ 第 1 关 · 书房 ============
        # 正确顺序：两截钥匙 → 完整钥匙 → 开书桌（密码纸 + 齿轮）→ 齿轮修钟（指针 3、9）
        #           → 线索齐了才开保险箱 397 → 书房门钥匙 → 开门
        print("== 第 1 关 书房 ==", flush=True)
        # ① 书架：半把钥匙① + 旧书线索（「另一半在画框之后」）
        click_hotspot(page, "bookshelf", 1.6)
        pick_item(page, "bookshelf", "key_half_a", "拾取半把钥匙①")
        click_act(page, "旧书", desc="查看旧书线索")
        time.sleep(1.6)
        click_back(page)

        # ② 画框：掀开 → 半把钥匙②
        click_hotspot(page, "picture_frame", 1.6)
        click_act(page, "掀开画框", desc="掀开画框")
        pick_item(page, "picture_frame", "key_half_b", "拾取半把钥匙②")
        click_back(page)

        # ③ 组合成完整钥匙
        combine_items(page, "key_half_a", "key_half_b")
        see(page, "组合出完整钥匙")

        # ④ 书桌：完整钥匙开锁 → 密码纸（第三位 7）+ 齿轮
        click_hotspot(page, "desk", 1.6)
        open_inv_item(page, "key_full", "书桌解锁")
        click_menu(page, "使用", exact=True)
        time.sleep(1.0)
        pick_item(page, "desk", "code_paper", "拾取密码纸")
        pick_item(page, "desk", "gear", "拾取齿轮")
        open_inv_item(page, "code_paper", "查看密码纸")
        click_menu(page, "查看", exact=True)
        time.sleep(1.6)
        click_back(page)

        # ⑤ 齿轮装回钟表 → 时针 3、分针 9（前两位）
        click_hotspot(page, "clock", 1.6)
        open_inv_item(page, "gear", "安装齿轮")
        click_menu(page, "使用", exact=True)
        time.sleep(1.8)
        click_back(page)

        # ⑥ 保险箱：线索齐备后才是 397 → 书房门钥匙
        click_hotspot(page, "safe", 2.0)
        click_act(page, "输入密码", desc="safe 输错密码")
        enter_pwd(page, "111")
        time.sleep(1.2)                      # 展示错误反馈
        click_act(page, "输入密码", desc="safe 输入线索推出的 397")
        enter_pwd(page, "397")
        time.sleep(1.2)
        pick_item(page, "safe", "study_key", "拾取书房门钥匙")
        click_back(page)

        # 用 study_key 开书房门 → 关卡衔接页
        click_hotspot(page, "door", 1.6)
        open_inv_item(page, "study_key", "开书房门")
        click_menu(page, "使用", exact=True)
        cross_room(page, "living_room", "书房门")

        # ============ 第 2 关 · 客厅 ============
        print("== 第 2 关 客厅 ==", flush=True)
        # 茶几：小票 + 鱼食；查看小票
        click_hotspot(page, "coffee_table", 1.6)
        pick_item(page, "coffee_table", "receipt_note", "拾取外卖小票")
        pick_item(page, "coffee_table", "fish_food", "拾取鱼食")
        open_inv_item(page, "receipt_note", "查看小票")
        click_menu(page, "查看", exact=True)
        time.sleep(1.6)
        click_back(page)

        # 冰箱贴
        click_hotspot(page, "fridge", 1.6)
        click_act(page, "揭下冰箱贴", desc="揭冰箱贴")
        time.sleep(0.6)
        pick_item(page, "fridge", "fridge_magnet", "拾取冰箱贴")
        open_inv_item(page, "fridge_magnet", "查看冰箱贴")
        click_menu(page, "查看", exact=True)
        time.sleep(1.3)
        click_back(page)

        # 沙发：晾衣杆
        click_hotspot(page, "sofa", 1.4)
        pick_item(page, "sofa", "drying_pole", "拾取晾衣杆")
        click_back(page)

        # 挂钟：晾衣杆挑下 → 背板
        click_hotspot(page, "wall_clock", 1.6)
        open_inv_item(page, "drying_pole", "挑挂钟")
        click_menu(page, "使用", exact=True)
        time.sleep(1.0)
        pick_item(page, "wall_clock", "clock_plaque", "拾取挂钟背板")
        open_inv_item(page, "clock_plaque", "查看背板")
        click_menu(page, "查看", exact=True)
        time.sleep(1.3)
        click_back(page)

        # 电视柜：相册
        click_hotspot(page, "tv_cabinet", 1.6)
        pick_item(page, "tv_cabinet", "photo_album", "拾取相册")
        open_inv_item(page, "photo_album", "查看相册")
        click_menu(page, "查看", exact=True)
        time.sleep(1.3)
        click_back(page)

        # 鱼缸：撒鱼食 → 数出 8 条
        click_hotspot(page, "fish_tank", 1.6)
        open_inv_item(page, "fish_food", "喂鱼")
        click_menu(page, "使用", exact=True)
        time.sleep(1.6)
        click_back(page)

        # 车库门：3728 → 关卡衔接页
        click_hotspot(page, "garage_door", 1.6)
        click_act(page, "输入密码", desc="车库门输入密码")
        enter_pwd(page, "3728")
        cross_room(page, "garage", "车库门")

        # ============ 第 3 关 · 车库 ============
        # 正确顺序：贴纸刻度 6 → 铁皮盒转盘到 6 → 旧钥匙 → 工具箱挂锁 → 纸条 529
        #           → 拿到线索后才输电子屏 529 → 面板弹开按 ↑ → 卷帘门升起 → 走出
        print("== 第 3 关 车库 ==", flush=True)
        # ① 遥控器（坏）快速看一眼
        click_hotspot(page, "remote", 1.3)
        click_back(page)

        # ② 汽车：褪色贴纸 → 刻度 6 线索
        click_hotspot(page, "car", 1.6)
        click_act(page, "褪色贴纸", desc="查看褪色贴纸")
        time.sleep(1.6)
        click_back(page)

        # ③ 铁皮盒：向右拧 6 格到刻度 6 → 弹开 → 旧钥匙
        click_hotspot(page, "tool_board", 1.6)
        for i in range(6):
            click_act(page, "向右旋转", wait=0.55, desc=f"刻度盘右转 {i+1}")
        time.sleep(1.2)
        pick_item(page, "tool_board", "old_key", "拾取旧钥匙")
        click_back(page)

        # ④ 工具箱：旧钥匙开挂锁 → 纸条 529（电子屏密码线索）
        click_hotspot(page, "tool_box", 1.6)
        open_inv_item(page, "old_key", "开工具箱挂锁")
        click_menu(page, "使用", exact=True)
        time.sleep(1.0)
        pick_item(page, "tool_box", "note_529", "拾取纸条")
        open_inv_item(page, "note_529", "查看纸条")
        click_menu(page, "查看", exact=True)
        time.sleep(1.6)
        click_back(page)

        # ⑤ 电子屏：拿到纸条后才输密码（先错一次展示反馈 → 再输 529）
        click_hotspot(page, "keypad", 1.6)
        click_act(page, "输入密码", desc="电子屏输错密码")
        enter_pwd(page, "111")
        time.sleep(1.2)
        click_act(page, "输入密码", desc="电子屏输入纸条上的 529")
        enter_pwd(page, "529")
        time.sleep(1.4)

        # ⑥ 上下箭头弹窗：↓ 无动静 → 再开 → ↑ 升起
        click_act(page, "查看电子屏", desc="打开电子屏箭头弹窗")
        page.locator("body .act-btn", has_text="⬇").last.click()
        time.sleep(1.4)                      # 展示「没有任何动静」
        click_act(page, "查看电子屏", desc="再开箭头弹窗")
        page.locator("body .act-btn", has_text="⬆").last.click()
        see(page, "卷帘门升起")
        click_back(page)

        # ⑦ 卷帘门：走出 → 通关（白底）
        click_hotspot(page, "exit_door", 1.8)
        click_act(page, "走出卷帘门", desc="走出卷帘门", timeout=8000)
        st = wait_until(page, JS_STATE, lambda s: s and s["finished"], 8000, "通关结算")
        print(f"  🎉 finished={st['finished']} progress={st['progress']}%", flush=True)
        time.sleep(6.0)

        # 收尾：关 context 落盘视频
        page.wait_for_timeout(400)
        ctx.close()
        browser.close()

    # 视频就位：把录制目录里的 webm 复制为最终文件
    vids = list((OUT_DIR / "_rec").glob("*.webm"))
    if not vids:
        raise RuntimeError("未找到录制视频文件")
    src = max(vids, key=lambda f: f.stat().st_mtime)
    if OUT_PATH.exists():
        OUT_PATH.unlink()
    src.rename(OUT_PATH)
    print(f"视频已保存: {OUT_PATH}  ({OUT_PATH.stat().st_size/1024/1024:.1f} MB)")
    # 清理录制临时目录（保留最终文件）
    import shutil
    shutil.rmtree(OUT_DIR / "_rec", ignore_errors=True)


if __name__ == "__main__":
    main()
