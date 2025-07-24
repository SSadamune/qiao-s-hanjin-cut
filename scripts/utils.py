import re
from constants import FORCE_MAP, COLOR_MEANINGS, FIRST_6_COLS

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|\r\n]+', '_', name).strip()

def get_cell_bg_color(cell):
    if cell.fill and cell.fill.fgColor and cell.fill.fgColor.type == "rgb":
        return cell.fill.fgColor.rgb
    return None

def split_multi_forces(force_str: str):
    """多势力字符串拆分 & /"""
    return re.split(r"[&/]", force_str)

def map_force_to_name(prefix: str):
    """前缀映射中文势力名"""
    return FORCE_MAP.get(prefix, "")

def detect_guest_factions(ws, row_idx, own_factions):
    """检查前6列颜色 → 找客将势力"""
    guest = set()
    for col in FIRST_6_COLS:
        color = get_cell_bg_color(ws.cell(row=row_idx, column=col))
        if not color or color in ("00000000", "FFFFFFFF"):
            continue
        if color in COLOR_MEANINGS:
            color_faction = COLOR_MEANINGS[color]
            if color_faction not in own_factions:
                guest.add(color_faction)
    return list(guest)

def sort_tags_final(sheet_name, package, types, forces, hero_name):
    """
    最终 tags 顺序：
    武将 → sheet名 → 分包 → 武将类型(固定顺序) → 所属势力 → 武将名
    """
    from constants import TYPE_ORDER

    tags = ["武将"]
    if sheet_name:
        tags.append(sheet_name)
    if package:
        tags.append(package)

    # 武将类型（固定顺序）
    for t in TYPE_ORDER:
        if t in types:
            tags.append(t)

    # 所属势力（不含伪装/客将）
    for f in forces:
        if f not in tags:
            tags.append(f)

    tags.append(hero_name)
    return tags
