# -*- coding: utf-8 -*-
"""
一次性脚本：生成 21 张特写/全景 + 1 张缺失兜底占位图（SVG）。
后续批量 AI 出图时直接覆盖同名文件即可，无需改代码。
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# 三关（panorama + objects）
LAYOUT = {
    "study": {
        "panorama": "旧书房 · 全景",
        "objects": {
            "bookshelf":     "书架",
            "desk":          "书桌",
            "picture_frame": "画框",
            "clock":         "钟表",
            "safe":          "保险箱",
            "door":          "书房门",
        },
    },
    "living_room": {
        "panorama": "客厅 · 全景",
        "objects": {
            "main_gate":    "大门（外面锁死）",
            "garage_door":  "车库门 · 电子锁",
            "coffee_table": "茶几",
            "tv_cabinet":   "电视柜抽屉",
            "wall_frame":   "墙面相框",
            "sofa":         "沙发垫",
            "fireplace":    "壁炉",
        },
    },
    "garage": {
        "panorama": "车库 · 全景",
        "objects": {
            "exit_door":  "出口门 · 遥控门",
            "keypad":     "电子屏 · 上下键",
            "remote":     "遥控器（坏）",
            "car":        "汽车 · 车载音响",
            "sun_visor":  "遮阳板",
            "glove_box":  "手套箱",
        },
    },
}

# 三关的色调（占位色块，便于一眼分辨关卡）
PALETTE = {
    "study":       ("#3b2a1f", "#c9a86a"),  # 暗棕底 + 金色字
    "living_room": ("#1f2d3b", "#8fb5d6"),  # 暗蓝底 + 浅蓝字
    "garage":      ("#1a1a22", "#9a8fb5"),  # 暗紫底 + 淡紫字
}


def svg(room: str, label: str, is_panorama: bool) -> str:
    bg, fg = PALETTE[room]
    sub = "全景插画占位" if is_panorama else "特写占位"
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" width="1600" height="900">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{bg}"/>
      <stop offset="1" stop-color="#000"/>
    </linearGradient>
  </defs>
  <rect width="1600" height="900" fill="url(#g)"/>
  <rect x="40" y="40" width="1520" height="820" fill="none" stroke="{fg}" stroke-width="3" stroke-dasharray="12 8"/>
  <text x="800" y="430" text-anchor="middle" font-family="Microsoft YaHei, sans-serif"
        font-size="64" fill="{fg}" font-weight="bold">{label}</text>
  <text x="800" y="510" text-anchor="middle" font-family="Microsoft YaHei, sans-serif"
        font-size="28" fill="{fg}" opacity="0.75">房间：{room}</text>
  <text x="800" y="560" text-anchor="middle" font-family="Microsoft YaHei, sans-serif"
        font-size="22" fill="{fg}" opacity="0.55">{sub} · 16:9 · 待 AI 出图后替换</text>
</svg>
'''


def missing_svg() -> str:
    return '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" width="1600" height="900">
  <rect width="1600" height="900" fill="#2a2436"/>
  <text x="800" y="470" text-anchor="middle" font-family="Microsoft YaHei, sans-serif"
        font-size="48" fill="#c9a86a">[ 图片缺失占位 ]</text>
</svg>
'''


def main() -> None:
    count = 0
    for room, cfg in LAYOUT.items():
        room_dir = ROOT / room
        room_dir.mkdir(parents=True, exist_ok=True)
        # panorama
        p = room_dir / "panorama.svg"
        p.write_text(svg(room, cfg["panorama"], is_panorama=True), encoding="utf-8")
        count += 1
        # objects
        for oid, name in cfg["objects"].items():
            p = room_dir / f"{oid}.svg"
            p.write_text(svg(room, name, is_panorama=False), encoding="utf-8")
            count += 1
    (ROOT / "missing.svg").write_text(missing_svg(), encoding="utf-8")
    count += 1
    print(f"OK · 生成 {count} 张占位图")


if __name__ == "__main__":
    main()
