from pathlib import Path
import json
from collections import OrderedDict

# =========================
# 复古换装小屋：自动生成素材清单
# 单文件夹头发分层 + 图层顺序修正版
#
# 最终图层顺序：
# 背景 - 前景装饰 - 翅膀 - 后发 hair_back - 衣服 - 下装 - 上衣 - 身体/脸 - 颈饰品 - 前发 hair
# - 帽子 - 眼镜 - 耳饰 - 脸饰品 - 手持物 - 特效 - 陪伴 - 文字装饰 - 相框
#
# 头发只用一个文件夹：assets/hair
# xxx_front.png  → 前发，显示在“头发”分类里
# xxx_back.png   → 后发，不显示分类按钮，点击对应前发时自动带出
# xxx.png        → 普通头发，显示在“头发”分类里，后发为空
#
# default 规则：
# 文件名包含 default 的素材会排在最前面，作为“恢复默认”展示。
# =========================

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"

# items.js 内部顺序，必须和 index.html 的 LAYER_ORDER / DRAW_ORDER 保持一致
items_order = [
    ("background", "背景"),
    ("front", "前景装饰"),
    ("wing", "翅膀"),
    ("hair_back", "后发"),
    ("clothes", "衣服"),
    ("bottom", "下装"),
    ("top", "上衣"),
    ("body", "身体/脸"),
    ("neck", "颈饰品"),
    ("hair", "头发"),
    ("hat", "帽子"),
    ("glasses", "眼镜"),
    ("earring", "耳饰"),
    ("face", "脸饰品"),
    ("hand", "手持物"),
    ("effect", "特效"),
    ("partner", "陪伴"),
    ("text", "文字装饰"),
    ("frame", "相框"),
]

# 实际存在的素材文件夹
# 注意：hair_back 不单独建文件夹，后发仍从 assets/hair 读取
folder_categories = [
    ("background", "背景"),
    ("front", "前景装饰"),
    ("wing", "翅膀"),
    ("clothes", "衣服"),
    ("bottom", "下装"),
    ("top", "上衣"),
    ("body", "身体/脸"),
    ("neck", "颈饰品"),
    ("hair", "头发"),
    ("hat", "帽子"),
    ("glasses", "眼镜"),
    ("earring", "耳饰"),
    ("face", "脸饰品"),
    ("hand", "手持物"),
    ("effect", "特效"),
    ("partner", "陪伴"),
    ("text", "文字装饰"),
    ("frame", "相框"),
]

allow_ext = [".png", ".gif", ".jpg", ".jpeg", ".webp"]

empty_items = {
    "background": "空白背景",
    "front": "无前景装饰",
    "wing": "无翅膀",
    "clothes": "不穿整套",
    "bottom": "不穿下装",
    "top": "不穿上衣",
    "neck": "无颈饰品",
    "hair": "无头发",
    "hat": "不戴帽子",
    "glasses": "不戴眼镜",
    "earring": "不戴耳饰",
    "face": "无脸饰品",
    "hand": "不拿物品",
    "effect": "无特效",
    "partner": "无陪伴",
    "text": "无文字装饰",
    "frame": "无相框",
}

ASSETS_DIR.mkdir(parents=True, exist_ok=True)

items = OrderedDict()
for category, _ in items_order:
    items[category] = []


def file_time(file_path):
    stat = file_path.stat()
    return max(stat.st_mtime, stat.st_ctime)


def is_default_file(file_path):
    return "default" in file_path.stem.lower()


def is_hair_back(file_path):
    name = file_path.stem.lower()
    return name.endswith("_back") or name.startswith("back_")


def clean_hair_name(file_path):
    name = file_path.stem
    lower = name.lower()

    if lower.endswith("_front"):
        return name[:-6]
    if lower.endswith("_back"):
        return name[:-5]
    if lower.startswith("front_"):
        return name[6:]
    if lower.startswith("back_"):
        return name[5:]

    return name


def make_item_src(category, file_path):
    return f"assets/{category}/{file_path.name}".replace("\\", "/")


def add_empty_if_needed(category):
    if category in empty_items:
        items[category].append({
            "name": empty_items[category],
            "src": ""
        })


def add_files_to_category(category, files, name_func=None, src_category=None):
    src_category = src_category or category

    default_files = [file for file in files if is_default_file(file)]
    normal_files = [file for file in files if not is_default_file(file)]

    default_files = sorted(default_files, key=file_time, reverse=True)
    normal_files = sorted(normal_files, key=file_time, reverse=True)

    # 有 default 时：default 放最前，作为恢复默认展示；空选项放在 default 后面，方便手动取消
    if default_files:
        for file in default_files + normal_files:
            display_name = name_func(file) if name_func else file.stem
            items[category].append({
                "name": display_name,
                "src": make_item_src(src_category, file)
            })

        if category in empty_items:
            items[category].append({
                "name": empty_items[category],
                "src": ""
            })

    # 没有 default 时：空选项作为恢复默认；普通素材按最新时间排序
    else:
        add_empty_if_needed(category)

        for file in normal_files:
            display_name = name_func(file) if name_func else file.stem
            items[category].append({
                "name": display_name,
                "src": make_item_src(src_category, file)
            })


for category, category_name in folder_categories:
    folder = ASSETS_DIR / category
    folder.mkdir(parents=True, exist_ok=True)

    files = []
    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in allow_ext:
            files.append(file)

    if category == "hair":
        hair_front_files = []
        hair_back_files = []

        for file in files:
            if is_hair_back(file):
                hair_back_files.append(file)
            else:
                hair_front_files.append(file)

        # 前发：显示在“头发”分类
        add_files_to_category("hair", hair_front_files, clean_hair_name, src_category="hair")

        # 后发：只进入 ITEMS.hair_back，不显示分类按钮
        default_back_files = [file for file in hair_back_files if is_default_file(file)]
        normal_back_files = [file for file in hair_back_files if not is_default_file(file)]

        default_back_files = sorted(default_back_files, key=file_time, reverse=True)
        normal_back_files = sorted(normal_back_files, key=file_time, reverse=True)

        for file in default_back_files + normal_back_files:
            items["hair_back"].append({
                "name": clean_hair_name(file),
                "src": make_item_src("hair", file)
            })

    else:
        add_files_to_category(category, files)

js_content = "window.ITEMS = "
js_content += json.dumps(items, ensure_ascii=False, indent=2)
js_content += ";\n"

output_file = BASE_DIR / "items.js"
output_file.write_text(js_content, encoding="utf-8")

print("素材清单生成完成：items.js")
print("图层顺序：背景-前景装饰-翅膀-后发-衣服-下装-上衣-身体/脸-颈饰品-前发-帽子-眼镜-耳饰-脸饰品-手持物-特效-陪伴-文字装饰-相框")
print("头发分层规则：assets/hair 内的 *_front 作为前发，*_back 作为后发。")
print("点击前发时，网页会自动带出同名后发。")
print("-" * 60)

for category, category_name in items_order:
    real_count = len([item for item in items.get(category, []) if item["src"]])
    total_count = len(items.get(category, []))

    if category == "hair_back":
        print(f"{category_name}：自动匹配素材 {real_count} 个，不显示为分类按钮")
    else:
        print(f"{category_name}：真实素材 {real_count} 个，列表显示 {total_count} 项")

print("-" * 60)
print("完成。现在回到网页，按 Ctrl + F5 强制刷新。")
