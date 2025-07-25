# monarch_cache.py

from constants import COL_CODE, COL_NAME, SKIP_PREFIXES
from parsers import parse_factions_from_code

def scan_all_monarch_names(wb, target_sheets):
    """预扫描所有君主武将名"""
    monarch_names = set()
    for sheet_name in target_sheets:
        ws = wb[sheet_name]
        for row_idx in range(2, ws.max_row + 1):
            if ws.row_dimensions[row_idx].hidden:
                continue
            code_cell = ws.cell(row=row_idx, column=COL_CODE)
            code = str(code_cell.value).strip() if code_cell.value else ""
            if not code or code.startswith(SKIP_PREFIXES):
                continue
            hero_cell = ws.cell(row=row_idx, column=COL_NAME)
            hero_name = str(hero_cell.value).strip() if hero_cell.value else ""
            if not hero_name:
                continue
            parsed = parse_factions_from_code(code)
            if "君主" in parsed["types"]:
                monarch_names.add(hero_name)
    return monarch_names
