"""
工具函数，包含文件名处理、颜色获取、势力映射等常用功能。
"""

import re
from constants import (
    FORCE_MAP,
    COLOR_MEANINGS,
    FIRST_6_COLS,
    TYPE_ORDER,
    COL_CODE,
    COL_NAME,
    SKIP_PREFIXES,
)


def hero_link(hero):
    """生成指向武将页面的链接"""
    return f"[[{sanitize_filename(hero['code'])} {hero['name'].replace('&', '_')}]]"


def sanitize_filename(name: str) -> str:
    """将文件名中的非法字符替换为下划线，并去除首尾空格"""
    return re.sub(r'[\\/:*?"<>|\r\n]+', "_", name).strip()


def get_cell_bg_color(cell):
    """获取单元格的背景色RGB（如有），否则返回None"""
    if cell.fill and cell.fill.fgColor and cell.fill.fgColor.type == "rgb":
        return cell.fill.fgColor.rgb
    return None


def split_multi_forces(force_str: str):
    """多势力字符串拆分 & /"""
    return re.split(r"[&/]", force_str)


def map_force_to_name(prefix: str):
    """前缀映射中文势力名"""
    return FORCE_MAP.get(prefix, "")


def detect_guest_factions(ws, row_idx, own_forces, disguise_forces):
    """检查前6列颜色 → 找客将势力（仅FORCE_MAP中的六势力，按 FORCE_MAP 顺序排序）"""
    guest = set()
    excluded_forces = set(own_forces) | set(disguise_forces)
    valid_force_names = list(FORCE_MAP.values())  # 顺序: 汉 魏 蜀 吴 群 晋

    for col in FIRST_6_COLS:
        color = get_cell_bg_color(ws.cell(row=row_idx, column=col))
        if not color or color in ("00000000", "FFFFFFFF"):
            continue

        if color in COLOR_MEANINGS:
            color_force = COLOR_MEANINGS[color]
            # 只判断六势力，且排除本武将的所属和伪装势力
            if color_force in valid_force_names and color_force not in excluded_forces:
                guest.add(color_force)

    # 排序，保证输出顺序符合 FORCE_MAP
    ordered_guest = sorted(guest, key=valid_force_names.index)
    return ordered_guest


def force_sort_key(force_name: str):
    """按照 FORCE_MAP 的顺序返回排序 key"""
    order = list(FORCE_MAP.values())
    try:
        return order.index(force_name)
    except ValueError:
        return 999


def sort_tags_final(
    sheet_name,  # sheet 名
    package,  # 分包
    types,  # 武将类型
    hero_name,  # 武将名
    force_tags,  # 所属势力列表
    loyalty_tags,  # 效忠势力列表
    disguise_forces,  # 伪装势力列表
    guest_tags,  # 客将势力列表
):
    """
    最终 tags 顺序：
    武将 → sheet名 → 分包 → 武将类型(固定顺序) →
    势力:{势力名} (FORCE_MAP顺序) →
    效忠:{势力名} →
    客将:{势力名} →
    伪装:{势力名} →
    武将名
    """
    valid_force_order = list(FORCE_MAP.values())  # 汉/魏/蜀/吴/群/晋
    tags = []

    # 1️⃣ 固定头部
    tags.append("武将")
    if sheet_name:
        tags.append(sheet_name)
    if package:
        tags.append(package)

    # 2️⃣ 武将类型（固定顺序）
    for t in TYPE_ORDER:
        if t in types:
            tags.append(t)

    # 3️⃣ 所属势力（FORCE_MAP 顺序）
    for f in sorted(force_tags, key=valid_force_order.index):
        single = f[0]
        tags.append(f"势力：{single}")

    # 4️⃣ 效忠势力
    for f in sorted(loyalty_tags, key=valid_force_order.index):
        single = f[0]
        tags.append(f"效忠：{single}")

    # 5️⃣ 客将势力
    for f in sorted(guest_tags, key=valid_force_order.index):
        single = f[0]
        tags.append(f"客将：{single}")

    # 6️⃣ 伪装势力
    for f in sorted(disguise_forces, key=valid_force_order.index):
        single = f[0]
        tags.append(f"伪装：{single}")

    # 7️⃣ 武将名
    tags.append(hero_name)

    # ✅ 最后进行全局去重，保留第一个出现的顺序
    seen = set()
    unique_tags = []
    for t in tags:
        if t not in seen:
            unique_tags.append(t)
            seen.add(t)

    return unique_tags


def is_valid_hero_row(ws, row_idx):
    """判断指定行是否为有效武将（编号和姓名均非空，编号无前缀）"""
    code_cell = ws.cell(row=row_idx, column=COL_CODE)
    name_cell = ws.cell(row=row_idx, column=COL_NAME)
    if not code_cell.value or not name_cell.value:
        return False
    code = str(code_cell.value).strip()
    if code.startswith(SKIP_PREFIXES):
        return False
    return True
