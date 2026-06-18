# -*- coding: utf-8 -*-
"""
一键创建男女素材文件夹.py

把本脚本放到网站根目录双击运行。
会自动创建：
assets/clothes_f
assets/clothes_m
assets/top_f
assets/top_m
assets/bottom_f
assets/bottom_m
assets/hair_f
assets/hair_m
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"

folders = [
    "clothes_f", "clothes_m",
    "top_f", "top_m",
    "bottom_f", "bottom_m",
    "hair_f", "hair_m",
]

ASSETS.mkdir(exist_ok=True)

for name in folders:
    path = ASSETS / name
    path.mkdir(exist_ok=True)
    print("已创建/已存在：", path)

print("完成。")
