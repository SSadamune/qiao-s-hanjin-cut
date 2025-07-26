"""
预扫描所有武将名，用于后续武将笔记生成。
"""

from constants import COL_CODE, COL_NAME, COL_SYNERGY
from utils import is_valid_hero_row
from parsers import parse_factions_from_code


def scan_all_heroes(wb, target_sheets):
    """
    扫描所有武将，返回包含编号、姓名、珠联璧合、是否君主、是否野心家的字典列表
    """
    heroes = []
    for sheet_name in target_sheets:
        ws = wb[sheet_name]
        for row_idx in range(2, ws.max_row + 1):
            if ws.row_dimensions[row_idx].hidden:
                continue
            if not is_valid_hero_row(ws, row_idx):
                continue
            code = str(ws.cell(row=row_idx, column=COL_CODE).value).strip()
            hero_name = (
                str(ws.cell(row=row_idx, column=COL_NAME).value)
                .strip()
                .replace("&", "_")
            )
            synergy_cell = ws.cell(row=row_idx, column=COL_SYNERGY).value
            if synergy_cell:
                synergy_list = [
                    s.strip()
                    for s in str(synergy_cell)
                    .replace("，", ",")
                    .replace("、", ",")
                    .replace("&", "_")
                    .split(",")
                    if s.strip()
                ]
            else:
                synergy_list = []
            parsed = parse_factions_from_code(code)
            is_monarch = "君主" in parsed["types"]
            is_ambitious = "野心家" in parsed["types"]
            heroes.append(
                {
                    "code": code,
                    "name": hero_name,
                    "synergy": synergy_list,
                    "is_monarch": is_monarch,
                    "is_ambitious": is_ambitious,
                }
            )
    return heroes
