# -*- coding: utf-8 -*-
"""
生成素材清单_四字诗意命名版_男女分类.py

用途：
1. 扫描 assets 文件夹，生成 items.js。
2. 支持男女分类：
   - assets/clothes_f  女衣服
   - assets/clothes_m  男衣服
   - assets/top_f      女上衣
   - assets/top_m      男上衣
   - assets/bottom_f   女下装
   - assets/bottom_m   男下装
   - assets/hair_f     女头发
   - assets/hair_m     男头发
3. 只对衣服/上衣/下装/头发分男女，其它素材仍共用。
4. 兼容旧结构：
   - assets/clothes
   - assets/top
   - assets/bottom
   - assets/hair
   这些旧文件夹仍然会被扫描。
5. 不改真实素材文件名，只改网页里显示的中文名。
6. 自动维护“素材中文命名表_四字版.json”。
"""

from pathlib import Path
import json
import re
import hashlib
import colorsys

try:
    from PIL import Image, ImageSequence
except Exception:
    Image = None
    ImageSequence = None

ROOT = Path(__file__).resolve().parent
ASSETS_DIR = ROOT / "assets"
NAME_MAP_FILE = ROOT / "素材中文命名表_四字版.json"
OUTPUT_JS = ROOT / "items.js"

IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

ITEMS_ORDER = [
    "background",
    "front",
    "wing",

    "hair_back",
    "hair_back_f",
    "hair_back_m",

    "clothes",
    "clothes_f",
    "clothes_m",

    "bottom",
    "bottom_f",
    "bottom_m",

    "top",
    "top_f",
    "top_m",

    "body",
    "neck",

    "hair",
    "hair_f",
    "hair_m",

    "hat",
    "glasses",
    "earring",
    "face",
    "hand",
    "effect",
    "partner",
    "text",
    "frame",
]

BASE_CATEGORY = {
    "clothes_f": "clothes",
    "clothes_m": "clothes",
    "top_f": "top",
    "top_m": "top",
    "bottom_f": "bottom",
    "bottom_m": "bottom",
    "hair_f": "hair",
    "hair_m": "hair",
    "hair_back_f": "hair_back",
    "hair_back_m": "hair_back",
}

COLOR_WORDS = {
    "white": ["月白", "雪瓷", "云白", "珍珠", "霜羽", "象牙", "银雾", "素雪", "玉色", "白露"],
    "pink": ["樱粉", "桃绯", "蔷薇", "莓粉", "胭脂", "糖粉", "绯樱", "玫粉", "粉雾", "桃雪"],
    "red": ["玫瑰", "朱砂", "绛红", "红茶", "石榴", "暮莓", "赤霞", "枫红", "红绒", "绯月"],
    "orange": ["橘灯", "焦糖", "暖橙", "蜜杏", "夕橙", "南瓜", "琥珀", "杏茶", "橙花", "蜜橘"],
    "yellow": ["鹅黄", "奶油", "金铃", "柠黄", "麦穗", "蜜金", "星砂", "金柠", "浅金", "月黄"],
    "green": ["薄荷", "青柠", "森绿", "豆蔻", "翠羽", "青苔", "竹影", "青萝", "绿萤", "草木"],
    "cyan": ["海盐", "水色", "湖青", "冰蓝", "浅潮", "玻璃", "晴川", "青瓷", "水雾", "蓝潮"],
    "blue": ["天蓝", "雾蓝", "鲸蓝", "星河", "海湾", "蓝莓", "夜航", "晴蓝", "蓝梦", "冰海"],
    "purple": ["藤紫", "鸢尾", "紫藤", "暮紫", "丁香", "星葡", "紫雾", "莓紫", "月紫", "紫晶"],
    "brown": ["栗子", "可可", "茶棕", "咖啡", "榛果", "木樨", "焦栗", "奶茶", "松木", "棕糖"],
    "gray": ["银灰", "雾灰", "烟蓝", "月影", "冷银", "铅云", "灰羽", "雾银", "石灰", "烟雨"],
    "black": ["墨夜", "黑曜", "乌木", "夜雾", "鸦羽", "暗星", "玄月", "黑糖", "墨蓝", "夜幕"],
    "colorful": ["虹光", "流彩", "糖果", "万花", "幻彩", "星爆", "霓虹", "彩梦", "珠光", "幻糖"],
}

MOODS = ["清晨", "午后", "黄昏", "午夜", "雨后", "雪夜", "晴窗", "旧梦", "夏末", "冬信", "春潮", "秋函", "微醺", "星落", "月眠", "风起", "海雾", "花信", "灯火", "远行", "晚安", "初见", "回声", "慢闪", "余温", "漂流", "长夏", "雾港", "薄暮", "晴光", "夜雨", "春白", "雪光", "云上", "微光", "深海", "北窗", "南风", "旧信", "游园"]
MOTIFS = ["玻璃", "星屑", "花窗", "邮票", "糖纸", "胶片", "珍珠", "丝带", "月桂", "风铃", "贝壳", "烟火", "唱片", "纸鹤", "蝴蝶", "猫眼", "水晶", "云朵", "香槟", "琉璃", "旧信", "绒球", "流苏", "玫瑰", "小熊", "兔耳", "银链", "花束", "星轨", "雪绒", "海盐", "汽水", "绸缎", "花园", "舞会", "剧院", "梦境", "礼盒", "橱窗", "电波", "闪片", "徽章", "蕾丝", "羽毛", "果冻", "蜜糖", "樱桃", "蓝莓", "夜航", "童话", "雨伞", "信笺", "香水", "塔楼", "旋律", "烟波", "软糖", "冰沙", "烛光", "魔法", "航线", "书页", "雪松", "露珠", "日记", "星灯", "霓虹", "茶会", "花火", "银河"]
STYLE_WORDS = ["复古", "甜酷", "学院", "梦幻", "奶油", "哥特", "童话", "港风", "森系", "海盐", "洛丽", "电波", "古典", "轻盈", "闪耀", "软糯", "俏皮", "清冷", "华丽", "日常", "舞会", "假日", "漫画", "偶像", "雪国", "糖果", "暗黑", "花园", "剧场", "未来"]

CATEGORY_NOUNS = {
    "background": ["房间", "街角", "花园", "剧场", "窗景", "海岸", "城堡", "小屋", "月台", "天幕", "糖铺", "茶室", "舞厅", "车站", "露台", "阁楼", "游园", "星港", "梦廊", "书房", "庭院", "灯街", "回廊", "幻境", "客厅", "沙龙", "店铺", "云阶", "夜市", "画室"],
    "front": ["前景", "帘幕", "花枝", "云边", "光斑", "门框", "花影", "窗纱", "边饰", "屏风", "落花", "雪幕", "灯串", "星帘", "梦雾", "藤蔓", "礼花", "水纹", "前帘", "光幕"],
    "wing": ["羽翼", "蝶翼", "光翼", "星翼", "薄翼", "梦翼", "花翼", "云翼", "月翼", "幻翼", "白羽", "黑羽", "流光", "翅影", "星羽", "云翅"],
    "hair": ["长发", "短发", "卷发", "马尾", "公主", "蓬发", "侧发", "波头", "发辫", "披发", "挑染", "刘海", "层发", "绒发", "娃发", "睡发", "漫发", "院发", "偶发", "发尾"],
    "hair_back": ["后发", "发影", "后卷", "背发", "后束", "发片", "垂发", "后层", "发尾", "发帘"],
    "clothes": ["礼裙", "套装", "衣裙", "制服", "舞裙", "洋装", "斗篷", "睡衣", "茶裙", "公主", "机车", "学院", "偶像", "魔裙", "哥裙", "旗袍", "水手", "外套", "派装", "旅装", "兔装", "熊装", "婚纱", "毛装", "运动", "侦探", "女仆", "乐队", "甜裙", "古裙"],
    "top": ["上衣", "针织", "外套", "衬衫", "背心", "披肩", "毛衣", "夹克", "吊带", "卫衣", "罩衫", "蕾衫", "上装", "斗篷", "花衫", "院衫", "短袖", "长袖", "围肩", "纱衣"],
    "bottom": ["半裙", "短裙", "长裙", "裤装", "灯裤", "褶裙", "纱裙", "瓜裤", "短裤", "花裙", "院裙", "蓬裙", "鱼裙", "底裙", "裙摆", "牛裙", "动裤", "小裙", "裙裤", "闲裤"],
    "body": ["素身", "娃身", "基础", "站姿", "脸型", "默认", "微笑", "小脸", "肤色", "角色", "模特", "人偶", "清爽", "暖肤", "冷白"],
    "neck": ["项链", "围巾", "颈饰", "领结", "锁链", "珠链", "丝巾", "铃铛", "颈带", "花环", "围脖", "披领", "吊坠", "绒围", "星链", "月链", "项圈", "短链", "缎带", "颈环"],
    "hat": ["帽子", "礼帽", "发冠", "贝帽", "兔帽", "结帽", "皇冠", "花帽", "织帽", "发箍", "头饰", "鸭帽", "睡帽", "巫帽", "发带", "猫耳", "水帽", "王冠", "花冠", "发饰"],
    "glasses": ["眼镜", "墨镜", "圆镜", "星镜", "框镜", "镜片", "护镜", "镜框", "心镜", "院镜", "古镜", "细镜", "透镜", "彩镜", "茶镜"],
    "earring": ["耳坠", "耳环", "耳饰", "星耳", "珠坠", "蝶耳", "铃耳", "花耳", "晶坠", "月耳", "流苏", "糖耳", "圆坠", "银针", "心耳"],
    "face": ["脸饰", "贴纸", "腮红", "面饰", "花贴", "星贴", "泪痣", "猫须", "心贴", "彩绘", "眼妆", "额饰", "雀斑", "表情", "亮片"],
    "hand": ["手持", "花束", "雨伞", "玩偶", "权杖", "气球", "魔棒", "信封", "糖果", "手袋", "扇子", "礼物", "咖杯", "话筒", "小旗", "相机", "玫瑰", "书本", "星杖", "灯笼"],
    "effect": ["特效", "光效", "星光", "泡泡", "闪粉", "花火", "落雪", "流光", "心光", "魔阵", "彩带", "烟花", "光环", "电波", "梦雾", "星雨", "旋光", "亮片", "光斑", "浮光"],
    "partner": ["陪伴", "伙伴", "宠物", "玩偶", "精灵", "小熊", "小兔", "猫咪", "鸟儿", "小狗", "蘑菇", "云宠", "星伴", "花灵", "气球", "海豹", "狐狸", "鹿鹿", "机器", "幽灵"],
    "text": ["字牌", "签名", "贴文", "标语", "弹幕", "话语", "告白", "闪字", "标题", "手写", "心情", "标识", "留言", "歌词", "问候", "注释", "横幅", "招牌", "字条", "短句"],
    "frame": ["相框", "边框", "画框", "镜框", "胶框", "花框", "星框", "晶框", "窗框", "幕框", "信框", "宝框", "蕾框", "古框", "卡框", "银框", "糖框", "霓框", "透框", "念框"],
}

CHINESE_SUFFIX = list("一二三四五六七八九十甲乙丙丁子丑寅卯辰巳午未申酉戌亥春夏秋冬星月花雪风云雨梦茶糖银金")

def stable_index(key, n, salt=""):
    h = hashlib.md5((key + salt).encode("utf-8")).hexdigest()
    return int(h[:8], 16) % n

def is_hair_back(rel_path):
    stem = Path(rel_path).stem.lower()
    return stem.endswith("_back") or "_back" in stem or stem.startswith("back_")

def is_hair_front(rel_path):
    stem = Path(rel_path).stem.lower()
    return stem.endswith("_front") or "_front" in stem or stem.startswith("front_")

def normalize_key_for_hair(src):
    name = Path(src).stem.lower()
    name = re.sub(r"(_front|_back)$", "", name)
    name = re.sub(r"^(front_|back_)", "", name)
    return name

def item_category_from_path(path):
    rel = path.relative_to(ASSETS_DIR).as_posix()
    top = rel.split("/")[0]

    if top == "hair" and is_hair_back(rel):
        return "hair_back"

    if top == "hair_f" and is_hair_back(rel):
        return "hair_back_f"

    if top == "hair_m" and is_hair_back(rel):
        return "hair_back_m"

    return top

def base_category(cat):
    return BASE_CATEGORY.get(cat, cat)

def get_image_signature(img_path):
    if Image is None:
        return "colorful", "normal", "medium"

    try:
        with Image.open(img_path) as im:
            try:
                frame = next(ImageSequence.Iterator(im))
            except Exception:
                frame = im
            rgba = frame.convert("RGBA")
            rgba.thumbnail((80, 80))
            pixels = list(rgba.getdata())
            rgb_pixels = [(r, g, b) for r, g, b, a in pixels if a > 20]
            if not rgb_pixels:
                rgb_pixels = [(r, g, b) for r, g, b, a in pixels]
            if len(rgb_pixels) > 2500:
                step = max(1, len(rgb_pixels) // 2500)
                rgb_pixels = rgb_pixels[::step]
            avg_r = sum(p[0] for p in rgb_pixels) / len(rgb_pixels)
            avg_g = sum(p[1] for p in rgb_pixels) / len(rgb_pixels)
            avg_b = sum(p[2] for p in rgb_pixels) / len(rgb_pixels)
            h, s, v = colorsys.rgb_to_hsv(avg_r / 255, avg_g / 255, avg_b / 255)
            hue = h * 360
            brightness = (avg_r + avg_g + avg_b) / 3
            if s < 0.10:
                color = "white" if brightness > 222 else ("black" if brightness < 75 else "gray")
            elif brightness < 55:
                color = "black"
            elif hue < 15 or hue >= 345:
                color = "red"
            elif hue < 42:
                color = "orange"
            elif hue < 70:
                color = "yellow"
            elif hue < 155:
                color = "green"
            elif hue < 190:
                color = "cyan"
            elif hue < 250:
                color = "blue"
            elif hue < 300:
                color = "purple"
            elif hue < 345:
                color = "pink"
            else:
                color = "colorful"
            bright_tag = "light" if brightness > 185 else ("dark" if brightness < 95 else "normal")
            sat_tag = "vivid" if s > 0.45 else ("soft" if s < 0.18 else "medium")
            return color, bright_tag, sat_tag
    except Exception:
        return "colorful", "normal", "medium"

def default_name(cat, src):
    if "default" not in Path(src).stem.lower():
        return None

    bc = base_category(cat)
    return {
        "background": "默认背景", "front": "默认前景", "wing": "默认羽翼",
        "hair": "默认发型", "hair_back": "默认后发", "clothes": "默认衣装",
        "bottom": "默认下装", "top": "默认上衣", "body": "默认素身",
        "neck": "默认颈饰", "hat": "默认帽子", "glasses": "默认眼镜",
        "earring": "默认耳饰", "face": "默认脸饰", "hand": "默认手持",
        "effect": "默认特效", "partner": "默认陪伴", "text": "默认文字",
        "frame": "默认相框",
    }.get(bc, "默认素材")

def candidate_names(cat, rel, path):
    src = "assets/" + rel.replace("\\", "/")
    bc = base_category(cat)
    color_key, bright_tag, sat_tag = get_image_signature(path)
    color_words = COLOR_WORDS.get(color_key, COLOR_WORDS["colorful"])
    nouns = CATEGORY_NOUNS.get(bc, ["素材"])
    key = src

    pools = [color_words, MOTIFS, MOODS, STYLE_WORDS]

    if bright_tag == "dark":
        pools.insert(0, ["墨夜", "黑曜", "夜雾", "暗星", "玄月", "深海", "月影", "夜幕"])
    elif bright_tag == "light":
        pools.insert(0, ["月白", "雪瓷", "云白", "晴窗", "微光", "春白", "雪光", "银雾"])

    if sat_tag == "vivid":
        pools.insert(0, ["霓虹", "闪耀", "糖果", "流彩", "星爆", "幻彩", "电波", "花火"])
    elif sat_tag == "soft":
        pools.insert(0, ["奶油", "轻盈", "雾感", "温柔", "柔纱", "旧梦", "微光", "云朵"])

    candidates = []

    for salt_i, pool in enumerate(pools):
        for j in range(min(len(pool), 18)):
            a = pool[(stable_index(key, len(pool), f"a{salt_i}") + j) % len(pool)]
            b = nouns[(stable_index(key, len(nouns), f"b{salt_i}") + j * 3) % len(nouns)]
            candidates.append(a + b)

    for j in range(20):
        a = MOTIFS[(stable_index(key, len(MOTIFS), "motif2") + j * 5) % len(MOTIFS)]
        b = nouns[(stable_index(key, len(nouns), "noun2") + j * 7) % len(nouns)]
        candidates.append(a + b)

    clean = []
    for n in candidates:
        n = n.replace("小小", "小").replace("默认", "初始")
        if len(n) == 4 and n not in clean:
            clean.append(n)
    return clean

def build_name(cat, rel, path, global_used):
    src = "assets/" + rel.replace("\\", "/")
    dn = default_name(cat, src)
    if dn and len(dn) <= 5 and dn not in global_used:
        global_used.add(dn)
        return dn

    for name in candidate_names(cat, rel, path):
        if len(name) == 4 and name not in global_used:
            global_used.add(name)
            return name

    for base in candidate_names(cat, rel, path):
        if len(base) == 4:
            for s in CHINESE_SUFFIX:
                name = base + s
                if len(name) <= 5 and name not in global_used:
                    global_used.add(name)
                    return name

    bc = base_category(cat)
    category_char = {
        "background": "景", "front": "前", "wing": "翼", "hair_back": "后",
        "clothes": "衣", "bottom": "裙", "top": "衫", "body": "身", "neck": "颈",
        "hair": "发", "hat": "帽", "glasses": "镜", "earring": "耳", "face": "脸",
        "hand": "手", "effect": "效", "partner": "伴", "text": "字", "frame": "框",
    }.get(bc, "物")
    chars = list("甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥")
    idx = stable_index(src, 9999, "fallback")
    base = category_char + chars[idx % len(chars)] + chars[(idx // 7) % len(chars)] + chars[(idx // 17) % len(chars)]
    if base not in global_used:
        global_used.add(base)
        return base
    for s in CHINESE_SUFFIX:
        name = base + s
        if len(name) <= 5 and name not in global_used:
            global_used.add(name)
            return name
    return base[:4]

def sort_items(items):
    def sort_key(item):
        stem = Path(item["src"]).stem.lower()
        is_default = 0 if "default" in stem else 1
        nums = re.findall(r"\d+", stem)
        num = int(nums[-1]) if nums else 10**9
        return (is_default, num, item["src"])
    return sorted(items, key=sort_key)

def main():
    if not ASSETS_DIR.exists():
        print("没有找到 assets 文件夹。请把本脚本放在网站根目录，与 assets 同级。")
        return

    if NAME_MAP_FILE.exists():
        try:
            name_map = json.loads(NAME_MAP_FILE.read_text(encoding="utf-8"))
        except Exception:
            name_map = {}
    else:
        name_map = {}

    all_files = sorted([p for p in ASSETS_DIR.rglob("*") if p.is_file() and p.suffix.lower() in IMG_EXTS])
    existing_srcs = {"assets/" + p.relative_to(ASSETS_DIR).as_posix() for p in all_files}
    name_map = {k: v for k, v in name_map.items() if k in existing_srcs and isinstance(v, str) and len(v) <= 5}

    global_used = set(name_map.values())

    for p in all_files:
        rel = p.relative_to(ASSETS_DIR).as_posix()
        src = "assets/" + rel
        cat = item_category_from_path(p)
        if cat not in ITEMS_ORDER:
            continue
        if src not in name_map:
            name_map[src] = build_name(cat, rel, p, global_used)

    # 前后发统一：前发四字，后发五字
    hair_base_to_front_name = {}
    for src, nm in list(name_map.items()):
        top = src.split("/")[1] if "/" in src else ""
        if top in ("hair", "hair_f", "hair_m") and is_hair_front(src):
            gender_suffix = ""
            if top == "hair_f":
                gender_suffix = "_f"
            elif top == "hair_m":
                gender_suffix = "_m"
            hair_base_to_front_name[(top, normalize_key_for_hair(src))] = nm

    for src in list(name_map.keys()):
        parts = src.split("/")
        top = parts[1] if len(parts) > 1 else ""
        if top in ("hair", "hair_f", "hair_m") and is_hair_back(src):
            key = (top, normalize_key_for_hair(src))
            if key in hair_base_to_front_name:
                proposed = hair_base_to_front_name[key] + "后"
                if len(proposed) <= 5 and proposed not in set(v for k, v in name_map.items() if k != src):
                    name_map[src] = proposed

    NAME_MAP_FILE.write_text(json.dumps(name_map, ensure_ascii=False, indent=2), encoding="utf-8")

    items = {cat: [] for cat in ITEMS_ORDER}

    for src in sorted(name_map.keys()):
        p = ROOT / src
        if not p.exists():
            continue
        cat = item_category_from_path(p)
        if cat in items:
            items[cat].append({"name": name_map[src], "src": src})

    for cat in items:
        items[cat] = sort_items(items[cat])

    OUTPUT_JS.write_text("window.ITEMS = " + json.dumps(items, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")

    all_names = [it["name"] for arr in items.values() for it in arr]
    too_long = [n for n in all_names if len(n) > 5]

    print("已生成 items.js")
    print(f"素材数量：{len(all_names)}")
    print(f"唯一名称：{len(set(all_names))}")
    print(f"超过五字：{len(too_long)}")
    print("支持男女分类：clothes_f / clothes_m / top_f / top_m / bottom_f / bottom_m / hair_f / hair_m")

if __name__ == "__main__":
    main()
