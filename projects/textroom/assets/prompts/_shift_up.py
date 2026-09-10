# -*- coding: utf-8 -*-
"""整体上移全景图内容：裁掉顶部空白条 + 底部补地面底色。
- living_room: 上移 11%（顶部空白 ~22%，物体最低 ~92%）
- garage:      上移 8%（卷帘门顶格前空白 ~8%，物体最低 ~83%）
"""
from PIL import Image
import shutil

BASE = "D:/A-work/WorkBuddy/TextRoom/assets"
JOBS = [
    ("living_room", "panorama.png", 0.11),
    ("garage",      "panorama.png", 0.08),
]

for room, name, ratio in JOBS:
    path = f"{BASE}/{room}/{name}"
    backup = f"{BASE}/prompts/_backup_{room}_{name}"
    shutil.copyfile(path, backup)

    img = Image.open(path).convert("RGB")
    W, H = img.size
    shift = int(H * ratio)

    # 裁掉顶部 shift 行（内容整体上移），底部用原最底行颜色补齐（衔接地面/背景）
    cropped = img.crop((0, shift, W, H))
    bottom_color = cropped.getpixel((W // 2, cropped.height - 2))
    canvas = Image.new("RGB", (W, H), bottom_color)
    canvas.paste(cropped, (0, 0))
    canvas.save(path)
    print(f"{room}: shift={shift}px ({ratio:.0%}), bottom_fill={bottom_color}, backup -> {backup}")
print("done")
