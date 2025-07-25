import re
from utils import split_multi_forces, map_force_to_name

from constants import FORCE_MAP

def sort_forces_by_map(forces):
    """根据 FORCE_MAP 的定义顺序排序"""
    order = list(FORCE_MAP.values())  # ["汉势力","魏势力","蜀势力","吴势力","群势力","晋势力"]
    return sorted(forces, key=lambda f: order.index(f) if f in order else 999)

def parse_factions_from_code(code):
    res = {
        "types": [],
        "所属势力": [],
        "效忠势力": [],
        "伪装势力": []
    }

    # 野心家
    if "AM" in code:
        res["types"].append("野心家")
        inner = re.search(r"\((.*?)\)", code)
        if inner:
            for part in split_multi_forces(inner.group(1)):
                prefix_only = re.match(r"^[A-Z]+", part)
                if prefix_only:
                    nm = map_force_to_name(prefix_only.group(0))
                    if nm:
                        res["效忠势力"].append(nm)

    # 君主（只要包含EM）
    if "EM" in code:
        res["types"].append("君主")
        inner = re.search(r"\((.*?)\)", code)
        if inner:
            for part in split_multi_forces(inner.group(1)):
                prefix_only = re.match(r"^[A-Z]+", part)
                if prefix_only:
                    nm = map_force_to_name(prefix_only.group(0))
                    if nm:
                        res["所属势力"].append(nm)

    # 叛首（只标记叛首）
    if "REB" in code:
        res["types"].append("叛首")
        inner = re.search(r"\((.*?)\)", code)
        if inner:
            for part in split_multi_forces(inner.group(1)):
                prefix_only = re.match(r"^[A-Z]+", part)
                if prefix_only:
                    nm = map_force_to_name(prefix_only.group(0))
                    if nm:
                        res["所属势力"].append(nm)

    # 叛谍
    if "^" in code:
        res["types"].append("叛谍")
        fake, real = code.split("^", 1)
        fake_parts = split_multi_forces(fake)
        real_prefix = re.match(r"^[A-Z&/]+", real)
        real_parts = split_multi_forces(real_prefix.group(0)) if real_prefix else []

        for p in fake_parts:
            prefix_only = re.match(r"^[A-Z]+", p)
            if prefix_only:
                nm = map_force_to_name(prefix_only.group(0))
                if nm:
                    res["伪装势力"].append(nm)
        for p in real_parts:
            prefix_only = re.match(r"^[A-Z]+", p)
            if prefix_only:
                nm = map_force_to_name(prefix_only.group(0))
                if nm:
                    res["所属势力"].append(nm)

    # 隐士
    if code.startswith("YS"):
        res["types"].append("隐士")

    # 普通匹配（没势力才兜底）
    if not res["所属势力"] and not res["效忠势力"] and "^" not in code and not code.startswith("YS"):
        prefix_match = re.match(r"^[A-Z&/]+", code)
        if prefix_match:
            for part in split_multi_forces(prefix_match.group(0)):
                prefix_only = re.match(r"^[A-Z]+", part)
                if prefix_only:
                    nm = map_force_to_name(prefix_only.group(0))
                    if nm:
                        res["所属势力"].append(nm)

    # ✅ 最后统一去重 & 排序
    res["所属势力"] = sort_forces_by_map(list(set(res["所属势力"])))
    res["效忠势力"] = sort_forces_by_map(list(set(res["效忠势力"])))
    res["伪装势力"] = sort_forces_by_map(list(set(res["伪装势力"])))

    return res
