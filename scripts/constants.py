# 颜色 → 含义
COLOR_MEANINGS = {
    "FFFFEEAD": "汉势力",
    "FFC5CAD3": "群势力",
    "FFC7DCFF": "魏势力",
    "FFF2C7FF": "晋势力",
    "FFFFC9C7": "蜀势力",
    "FFC3EAD5": "吴势力",
    "FFFFE270": "君主",
    "FF5E2281": "野心家",
    "FFF3F5F7": "隐士"
}

# 允许正常识别的颜色集合（快速判断）
KNOWN_COLORS = set(COLOR_MEANINGS.keys())
