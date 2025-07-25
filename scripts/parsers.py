"""
解析武将编号字符串，提取类型、势力等结构化信息的工具函数。
"""

import re
from utils import split_multi_forces

from constants import FORCE_MAP


def sort_forces_by_map(forces):
    """根据 FORCE_MAP 的定义顺序排序"""
    order = list(
        FORCE_MAP.values()
    )  # ["汉势力","魏势力","蜀势力","吴势力","群势力","晋势力"]
    return sorted(forces, key=lambda f: order.index(f) if f in order else 999)


def extract_valid_force(part: str):
    """从分割后的字符串中提取有效势力（支持 QUNXXX 等未确定数字的编号）"""
    for k, v in FORCE_MAP.items():
        if part.startswith(k):
            return v
    return None


def parse_factions_from_code(code: str):
    """解析编号字符串，提取武将类型、所属/效忠/伪装势力等信息"""
    res = {"types": [], "所属势力": [], "效忠势力": [], "伪装势力": []}

    # 野心家（包含 AM 即是）
    if "AM" in code:
        if "野心家" not in res["types"]:
            res["types"].append("野心家")

        # 如果括号里有内容 → 解析为效忠势力
        inner = re.search(r"\((.*?)\)", code)
        if inner:
            for part in split_multi_forces(inner.group(1)):
                nm = extract_valid_force(part)
                if nm:
                    res["效忠势力"].append(nm)

    # 君主（只要包含 EM）
    if "EM" in code:
        if "君主" not in res["types"]:
            res["types"].append("君主")

        # 括号里的势力
        inner = re.search(r"\((.*?)\)", code)
        if inner:
            for part in split_multi_forces(inner.group(1)):
                nm = extract_valid_force(part)
                if nm:
                    res["所属势力"].append(nm)

    # 叛首
    if "REB(" in code:
        if "叛首" not in res["types"]:
            res["types"].append("叛首")

        inner = re.search(r"\((.*?)\)", code)
        if inner:
            for part in split_multi_forces(inner.group(1)):
                nm = extract_valid_force(part)
                if nm:
                    res["所属势力"].append(nm)

    # 叛谍（^ 前伪装，^ 后真实）
    if "^" in code:
        if "叛谍" not in res["types"]:
            res["types"].append("叛谍")

        fake, real = code.split("^", 1)

        # ^ 前 → 伪装势力
        for part in split_multi_forces(fake):
            nm = extract_valid_force(part)
            if nm:
                res["伪装势力"].append(nm)

        # ^ 后 → 真实势力（只取前缀部分）
        real_prefix = re.match(r"^[A-Z&/]+", real)
        if real_prefix:
            for part in split_multi_forces(real_prefix.group(0)):
                nm = extract_valid_force(part)
                if nm:
                    res["所属势力"].append(nm)

    # 隐士
    if code.startswith("YS"):
        if "隐士" not in res["types"]:
            res["types"].append("隐士")

    # ✅ 普通解析
    if not res["效忠势力"] and "^" not in code and not code.startswith("YS"):
        prefix_match = re.match(r"^[A-Z&/]+", code)
        if prefix_match:
            for part in split_multi_forces(prefix_match.group(0)):
                nm = extract_valid_force(part)
                if nm:
                    res["所属势力"].append(nm)

    # ✅ 最后统一去重 & 排序
    res["所属势力"] = sort_forces_by_map(list(set(res["所属势力"])))
    res["效忠势力"] = sort_forces_by_map(
        [
            f for f in set(res["效忠势力"]) if f not in res["所属势力"]
        ]  # 如果和所属势力重复就剔除（野君司马懿）
    )
    res["伪装势力"] = sort_forces_by_map(list(set(res["伪装势力"])))

    return res
