"""跑通 TextRoom 三关全流程，并在每个关键画面截一张图，用于挑选作品集用图。

用法：
    cd D:/A-work/WorkBuddy/TextRoom
    set PLAYWRIGHT_BROWSERS_PATH=D:/A-work/WorkBuddy/TextRoom/.pw-browsers
    .venv/Scripts/python.exe scripts/shoot_portfolio.py

产物：D:/A-work/WorkBuddy/TextRoom/portfolio_shots/*.png
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from playwright.sync_api import sync_playwright  # noqa: E402

import record_playthrough as rec  # noqa: E402

SHOT_DIR = ROOT / "portfolio_shots"
SHOT_DIR.mkdir(exist_ok=True)
for f in SHOT_DIR.glob("*.png"):
    f.unlink()

_shots = []


def shot(page, name, note=""):
    path = SHOT_DIR / f"{len(_shots) + 1:02d}-{name}.png"
    page.screenshot(path=str(path))
    _shots.append((path.name, note))
    print(f"  [shot] {path.name}  {note}", flush=True)


def cross_room_shot(page, expected_room, desc, gate_name):
    """跨关：等 room 切换 → 截衔接页 → 点掉 → 在新关全景停留后截图。"""
    rec.wait_until(page, rec.JS_STATE, lambda s: s and s["room"] == expected_room,
                   8000, f"跨入 {expected_room} @{desc}")
    time.sleep(1.0)
    try:
        page.locator("#levelGate").wait_for(state="visible", timeout=5000)
    except Exception:
        pass
    else:
        shot(page, gate_name, "关卡衔接页（白底黑字）")
        time.sleep(0.8)
        page.locator("#levelGate").click(force=True)
    time.sleep(1.6)
    rec.admire(page, rec.ROOM_HOLD, f"{expected_room} 全景")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
        )
        page = ctx.new_page()
        page.goto(rec.URL)
        page.wait_for_selector("#cover-btn", timeout=10000)
        time.sleep(2.0)

        # ---------- 封面 ----------
        shot(page, "cover", "封面 · 开始游戏")

        page.locator("#cover-btn").click()
        rec.see(page, "开局：书房全景")
        rec.admire(page, rec.ROOM_HOLD, "书房全景")
        shot(page, "study-panorama", "L1 书房全景（热点 + 右侧栏 + 旁白）")

        # ---------- L1 书房 ----------
        print("== L1 书房 ==", flush=True)
        rec.click_hotspot(page, "bookshelf", 1.6)
        shot(page, "study-bookshelf", "书架特写 · 半把钥匙① + 旧书")
        rec.pick_item(page, "bookshelf", "key_half_a", "拾取半把钥匙①")
        rec.click_act(page, "旧书", desc="查看旧书线索")
        time.sleep(1.6)
        shot(page, "study-oldbook-clue", "旧书线索（旁白 + 线索入栏）")
        rec.click_back(page)

        rec.click_hotspot(page, "picture_frame", 1.6)
        rec.click_act(page, "掀开画框", desc="掀开画框")
        rec.pick_item(page, "picture_frame", "key_half_b", "拾取半把钥匙②")
        rec.click_back(page)

        rec.open_inv_item(page, "key_half_a", "组合入口")
        time.sleep(0.6)
        shot(page, "study-inventory-menu", "背包道具菜单（查看/使用/组合）")
        rec.click_menu(page, "组合", exact=True, wait=0.6)
        name_b = page.evaluate(
            "(id) => { const d=lastData; const it=(d.inventory_detail||[])"
            ".find(x=>x.id===id); return it?it.name:''; }", "key_half_b")
        rec.click_menu(page, f"与 {name_b} 组合", wait=1.2)
        shot(page, "study-combine-result", "组合成功 · 完整钥匙 + 旁白")
        rec.see(page, "组合出完整钥匙")

        rec.click_hotspot(page, "desk", 1.6)
        rec.open_inv_item(page, "key_full", "书桌解锁")
        rec.click_menu(page, "使用", exact=True)
        time.sleep(1.2)
        shot(page, "study-desk-unlocked", "书桌解锁 · 密码纸 + 齿轮")
        rec.pick_item(page, "desk", "code_paper", "拾取密码纸")
        rec.pick_item(page, "desk", "gear", "拾取齿轮")
        rec.open_inv_item(page, "code_paper", "查看密码纸")
        rec.click_menu(page, "查看", exact=True)
        time.sleep(1.6)
        shot(page, "study-code-paper", "查看密码纸 · 第三位 = 7")
        rec.click_back(page)

        rec.click_hotspot(page, "clock", 1.6)
        rec.open_inv_item(page, "gear", "安装齿轮")
        rec.click_menu(page, "使用", exact=True)
        time.sleep(2.0)
        shot(page, "study-clock-hands", "齿轮修复座钟 · 指针 3 和 9")
        rec.click_back(page)

        rec.click_hotspot(page, "safe", 2.0)
        rec.click_act(page, "输入密码", desc="safe 输错密码")
        rec.enter_pwd(page, "111")
        time.sleep(1.2)
        shot(page, "study-safe-wrong", "密码错误反馈")
        rec.click_act(page, "输入密码", desc="safe 输入 397")
        for ch in "39":
            page.locator(f'.pad-key[data-k="{ch}"]').click()
            time.sleep(0.15)
        shot(page, "study-safe-keypad", "保险箱密码盘 · 输入 397")
        page.locator('.pad-key[data-k="7"]').click()
        time.sleep(0.2)
        page.locator('.pad-key[data-k="OK"]').click()
        time.sleep(1.6)
        shot(page, "study-safe-open", "保险箱打开 · 书房门钥匙")
        rec.pick_item(page, "safe", "study_key", "拾取书房门钥匙")
        rec.click_back(page)

        rec.click_hotspot(page, "door", 1.6)
        rec.open_inv_item(page, "study_key", "开书房门")
        rec.click_menu(page, "使用", exact=True)
        cross_room_shot(page, "living_room", "书房门", "gate-to-livingroom")
        shot(page, "living-panorama", "L2 客厅全景")

        # ---------- L2 客厅 ----------
        print("== L2 客厅 ==", flush=True)
        rec.click_hotspot(page, "coffee_table", 1.6)
        rec.pick_item(page, "coffee_table", "receipt_note", "拾取外卖小票")
        rec.pick_item(page, "coffee_table", "fish_food", "拾取鱼食")
        rec.open_inv_item(page, "receipt_note", "查看小票")
        rec.click_menu(page, "查看", exact=True)
        time.sleep(1.6)
        shot(page, "living-receipt", "外卖小票 · 取件顺序线索")
        rec.click_back(page)

        rec.click_hotspot(page, "fridge", 1.6)
        rec.click_act(page, "揭下冰箱贴", desc="揭冰箱贴")
        time.sleep(0.8)
        rec.pick_item(page, "fridge", "fridge_magnet", "拾取冰箱贴")
        rec.open_inv_item(page, "fridge_magnet", "查看冰箱贴")
        rec.click_menu(page, "查看", exact=True)
        time.sleep(1.3)
        shot(page, "living-magnet", "冰箱贴 · 数字线索")
        rec.click_back(page)

        rec.click_hotspot(page, "sofa", 1.4)
        rec.pick_item(page, "sofa", "drying_pole", "拾取晾衣杆")
        rec.click_back(page)

        rec.click_hotspot(page, "wall_clock", 1.6)
        rec.open_inv_item(page, "drying_pole", "挑挂钟")
        rec.click_menu(page, "使用", exact=True)
        time.sleep(1.0)
        rec.pick_item(page, "wall_clock", "clock_plaque", "拾取挂钟背板")
        rec.open_inv_item(page, "clock_plaque", "查看背板")
        rec.click_menu(page, "查看", exact=True)
        time.sleep(1.3)
        shot(page, "living-clock-plaque", "挂钟背板 · 数字线索")
        rec.click_back(page)

        rec.click_hotspot(page, "tv_cabinet", 1.6)
        rec.pick_item(page, "tv_cabinet", "photo_album", "拾取相册")
        rec.open_inv_item(page, "photo_album", "查看相册")
        rec.click_menu(page, "查看", exact=True)
        time.sleep(1.3)
        shot(page, "living-album", "相册 · 数字线索")
        rec.click_back(page)

        rec.click_hotspot(page, "fish_tank", 1.6)
        rec.open_inv_item(page, "fish_food", "喂鱼")
        rec.click_menu(page, "使用", exact=True)
        time.sleep(1.8)
        shot(page, "living-fishtank", "鱼缸喂鱼 · 数出 8 条")
        rec.click_back(page)

        rec.click_hotspot(page, "garage_door", 1.6)
        rec.click_act(page, "输入密码", desc="车库门输入密码")
        for ch in "372":
            page.locator(f'.pad-key[data-k="{ch}"]').click()
            time.sleep(0.12)
        page.locator('.pad-key[data-k="8"]').click()
        time.sleep(0.2)
        shot(page, "living-garagedoor-keypad", "车库门密码盘 · 输入 3728")
        page.locator('.pad-key[data-k="OK"]').click()
        cross_room_shot(page, "garage", "车库门", "gate-to-garage")
        shot(page, "garage-panorama", "L3 车库全景")

        # ---------- L3 车库 ----------
        print("== L3 车库 ==", flush=True)
        rec.click_hotspot(page, "remote", 1.3)
        shot(page, "garage-remote", "遥控器（损坏）")
        rec.click_back(page)

        rec.click_hotspot(page, "car", 1.6)
        rec.click_act(page, "褪色贴纸", desc="查看褪色贴纸")
        time.sleep(1.6)
        shot(page, "garage-sticker", "褪色贴纸 · 刻度 6 线索")
        rec.click_back(page)

        rec.click_hotspot(page, "tool_board", 1.6)
        for i in range(6):
            rec.click_act(page, "向右旋转", wait=0.55, desc=f"刻度盘右转 {i+1}")
            if i == 3:
                time.sleep(0.3)
        time.sleep(1.2)
        shot(page, "garage-toolbox-open", "铁皮盒弹开 · 旧钥匙")
        rec.pick_item(page, "tool_board", "old_key", "拾取旧钥匙")
        rec.click_back(page)

        rec.click_hotspot(page, "tool_box", 1.6)
        rec.open_inv_item(page, "old_key", "开工具箱挂锁")
        rec.click_menu(page, "使用", exact=True)
        time.sleep(1.0)
        rec.pick_item(page, "tool_box", "note_529", "拾取纸条")
        rec.open_inv_item(page, "note_529", "查看纸条")
        rec.click_menu(page, "查看", exact=True)
        time.sleep(1.6)
        shot(page, "garage-note529", "纸条 · 密码线索 529")
        rec.click_back(page)

        rec.click_hotspot(page, "keypad", 1.6)
        rec.click_act(page, "输入密码", desc="电子屏输错密码")
        rec.enter_pwd(page, "111")
        time.sleep(1.2)
        shot(page, "garage-keypad-wrong", "电子屏错误反馈")
        rec.click_act(page, "输入密码", desc="电子屏输入 529")
        rec.enter_pwd(page, "529")
        time.sleep(1.6)
        shot(page, "garage-keypad-open", "电子屏 529 已输入· 解锁成功")
        rec.click_act(page, "查看电子屏", desc="打开电子屏箭头弹窗")
        time.sleep(0.8)
        shot(page, "garage-arrows-panel", "电子屏弹窗 · 上下箭头")
        page.locator("body .act-btn", has_text="⬇").last.click()
        time.sleep(1.4)
        shot(page, "garage-arrow-down", "按↓ 无动静")
        rec.click_act(page, "查看电子屏", desc="再开箭头弹窗")
        page.locator("body .act-btn", has_text="⬆").last.click()
        time.sleep(1.6)
        shot(page, "garage-arrow-up-shutter", "按↑ 卷帘门升起")
        rec.see(page, "卷帘门升起")
        rec.click_back(page)

        rec.click_hotspot(page, "exit_door", 1.8)
        rec.click_act(page, "走出卷帘门", desc="走出卷帘门", timeout=8000)
        rec.wait_until(page, rec.JS_STATE, lambda s: s and s["finished"], 8000, "通关结算")
        time.sleep(2.0)
        shot(page, "ending", "通关结算页")
        time.sleep(1.0)

        ctx.close()
        browser.close()

    print(f"\n共 {len(_shots)} 张截图 -> {SHOT_DIR}")


if __name__ == "__main__":
    main()
