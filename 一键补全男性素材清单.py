# -*- coding: utf-8 -*-
"""
一键补全男性素材清单
作用：
1. 扫描本地真实文件夹：
   - assets/clothes_m
   - assets/top_m
   - assets/bottom_m
2. 把这些文件补进 items.js 对应分类。
3. 自动备份旧 items.js。
4. 自动给 index.html 里的 items.js 加新版本号，避免浏览器缓存旧清单。

使用：
把本文件放在 QQ 网站根目录，也就是 index.html、items.js、assets 文件夹同一层。
然后双击同包里的 bat，或在 cmd 里运行：
python 一键补全男性素材清单.py
"""

from pathlib import Path
import json
import re
import shutil
from datetime import datetime

ROOT = Path(__file__).resolve().parent
ITEMS_PATH = ROOT / "items.js"
INDEX_PATH = ROOT / "index.html"
REPORT_PATH = ROOT / "男性素材补全报告.txt"

IMAGE_EXTS = {".gif", ".png", ".jpg", ".jpeg", ".webp"}

TARGETS = {
    "clothes_m": {
        "folder": ROOT / "assets" / "clothes_m",
        "label": "男装"
    },
    "top_m": {
        "folder": ROOT / "assets" / "top_m",
        "label": "男上衣"
    },
    "bottom_m": {
        "folder": ROOT / "assets" / "bottom_m",
        "label": "男下装"
    }
}


def read_items_js(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError("没有找到 items.js，请确认脚本和 items.js 在同一个文件夹。")

    text = path.read_text(encoding="utf-8", errors="ignore").strip()

    if text.startswith("window.ITEMS = "):
        text = text[len("window.ITEMS = "):]

    if text.endswith(";"):
        text = text[:-1]

    return json.loads(text)


def write_items_js(path: Path, data: dict) -> None:
    output = "window.ITEMS = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    path.write_text(output, encoding="utf-8")


def to_web_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def get_last_number(value: str):
    name = Path(value).stem
    matched = re.search(r"(\d{1,6})(?!.*\d)", name)
    if not matched:
        return None
    return int(matched.group(1))


def sort_key(item: dict):
    src = item.get("src", "")
    if not src:
        return (-2, -1, "")
    if Path(src).name.lower().startswith("default"):
        return (-1, -1, src)
    number = get_last_number(src)
    if number is None:
        return (999999, 999999, src)
    return (0, number, src)


def make_name(label: str, src: str) -> str:
    name = Path(src).stem
    number = get_last_number(src)

    if number is not None:
        return f"{label}{number:03d}"

    # 非数字文件名直接保留一部分，避免中文乱掉
    clean = re.sub(r"[_\-]+", " ", name).strip()
    return f"{label}-{clean}"[:16]


def scan_folder(folder: Path):
    if not folder.exists():
        return []

    files = []
    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in IMAGE_EXTS:
            files.append(file)

    files.sort(key=lambda p: (
        -1 if p.name.lower().startswith("default") else 0,
        get_last_number(p.name) if get_last_number(p.name) is not None else 999999,
        p.name.lower()
    ))
    return files


def bump_index_cache():
    if not INDEX_PATH.exists():
        return "没有找到 index.html，跳过缓存版本号修改。"

    text = INDEX_PATH.read_text(encoding="utf-8", errors="ignore")
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")

    new_text = re.sub(
        r'<script\s+src="items\.js(?:\?v=[^"]*)?"></script>',
        f'<script src="items.js?v=maleAssetsFix_{stamp}"></script>',
        text,
        count=1
    )

    if new_text == text:
        return "index.html 里没有找到 items.js 引用，跳过缓存版本号修改。"

    backup = INDEX_PATH.with_name(f"index_backup_{stamp}.html")
    shutil.copy2(INDEX_PATH, backup)
    INDEX_PATH.write_text(new_text, encoding="utf-8")
    return f"已修改 index.html 的 items.js 缓存版本号，并备份为：{backup.name}"


def main():
    now = datetime.now().strftime("%Y%m%d%H%M%S")

    data = read_items_js(ITEMS_PATH)

    backup_path = ITEMS_PATH.with_name(f"items_backup_{now}.js")
    shutil.copy2(ITEMS_PATH, backup_path)

    report_lines = []
    report_lines.append("男性素材补全报告")
    report_lines.append("=" * 30)
    report_lines.append(f"执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"已备份旧 items.js：{backup_path.name}")
    report_lines.append("")

    total_added = 0

    for category, cfg in TARGETS.items():
        folder = cfg["folder"]
        label = cfg["label"]

        data.setdefault(category, [])
        existing_list = data[category]
        existing_srcs = {str(item.get("src", "")).replace("\\", "/") for item in existing_list if isinstance(item, dict)}

        files = scan_folder(folder)
        added = []

        for file in files:
            src = to_web_path(file)
            if src not in existing_srcs:
                item = {
                    "name": make_name(label, src),
                    "src": src
                }
                existing_list.append(item)
                existing_srcs.add(src)
                added.append(src)

        # 去重，保留第一次出现的项目
        seen = set()
        cleaned = []
        for item in existing_list:
            if not isinstance(item, dict):
                continue
            src = str(item.get("src", "")).replace("\\", "/")
            key = src if src else "__empty__"
            if key in seen:
                continue
            seen.add(key)
            item["src"] = src
            cleaned.append(item)

        cleaned.sort(key=sort_key)
        data[category] = cleaned

        total_added += len(added)

        report_lines.append(f"[{category}] {label}")
        report_lines.append(f"扫描文件夹：{folder.relative_to(ROOT).as_posix() if folder.exists() else folder}")
        report_lines.append(f"文件夹实际图片数：{len(files)}")
        report_lines.append(f"原清单数量：{len(existing_list)}")
        report_lines.append(f"本次新增：{len(added)}")
        report_lines.append(f"补全后清单数量：{len(cleaned)}")

        if added:
            report_lines.append("新增文件：")
            for src in added:
                report_lines.append(f"  + {src}")

        report_lines.append("")

    write_items_js(ITEMS_PATH, data)
    cache_msg = bump_index_cache()

    report_lines.append(cache_msg)
    report_lines.append("")
    report_lines.append(f"总新增素材：{total_added}")
    report_lines.append("")
    report_lines.append("操作完成。请把新的 items.js 和 index.html 上传到 GitHub。")

    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")

    print("\n".join(report_lines))
    print("\n已完成。窗口可以关闭。")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("执行失败：", e)
        print("请确认本脚本放在 index.html、items.js、assets 文件夹同一层。")
        input("按回车退出...")
