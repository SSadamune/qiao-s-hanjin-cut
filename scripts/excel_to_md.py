import os
import re
from openpyxl import load_workbook
from zhconv import convert
from constants import COLOR_MEANINGS  # 势力颜色映射

VAULT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXCEL_PATH = os.path.join(VAULT_PATH, "resources", "乔剪国战表格.xlsx")
OUTPUT_DIR = os.path.join(VAULT_PATH, "notes", "武将")

# 体力值映射
HP_MAP = {"696": 1.5, "6969": 2.0, "69696": 2.5}

# 跳过的编号前缀
SKIP_PREFIXES = ("黑桃", "梅花", "红桃", "方片", "EMA", "Z.")

# 势力映射
FORCE_MAP = {
    "HAN": "汉势力",
    "WEI": "魏势力",
    "SHU": "蜀势力",
    "WU": "吴势力",
    "QUN": "群势力",
    "JIN": "晋势力"
}

# 武将类型固定顺序
TYPE_ORDER = ["君主", "野心家", "叛首", "叛谍", "客将", "隐士", "可君主升变"]

TARGET_SHEETS = [
    "官方范围",
    "兵情篇",
    "豪门贵胄",
    "异军突起",
    "小型扩展",
    "他山之玉"
]

# Excel 列常量
COL_PACKAGE = 1
COL_CODE = 2
COL_NAME = 3
COL_TITLE = 4
COL_HP = 5
COL_SYNERGY = 6
COL_LEADERSHIP = 7
COL_SKILL1_NAME = 8
COL_SKILL1_DESC = 9
COL_SKILL2_NAME = 10
COL_SKILL2_DESC = 11
COL_SKILL3_NAME = 12
COL_SKILL3_DESC = 13

FIRST_6_COLS = [COL_PACKAGE, COL_CODE, COL_NAME, COL_TITLE, COL_HP, COL_SYNERGY]

# ------------------- 工具 -------------------

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|\r\n]+', '_', name).strip()

def get_cell_bg_color(cell):
    if cell.fill and cell.fill.fgColor and cell.fill.fgColor.type == "rgb":
        return cell.fill.fgColor.rgb
    return None

def split_multi_forces(force_str: str):
    return re.split(r"[&/]", force_str)

def map_force_to_name(prefix: str):
    return FORCE_MAP.get(prefix, "")

def detect_guest_factions(ws, row_idx, own_factions):
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
    tags = ["武将"]
    if sheet_name:
        tags.append(sheet_name)
    if package:
        tags.append(package)
    for t in TYPE_ORDER:
        if t in types:
            tags.append(t)
    for f in forces:
        if f not in tags:
            tags.append(f)
    tags.append(hero_name)
    return tags

# ------------------- 武将解析 -------------------

def parse_factions_from_code(code):
    res = {
        "types": [],
        "所属势力": [],
        "效忠势力": [],
        "伪装势力": []
    }

    # 野心家
    if "AM" in code:
        if "野心家" not in res["types"]:
            res["types"].append("野心家")
        # 野心家括号内容 = 效忠势力
        inner = re.search(r"\((.*?)\)", code)
        if inner:
            for part in split_multi_forces(inner.group(1)):
                nm = map_force_to_name(part)
                if nm:
                    res["效忠势力"].append(nm)

    # 君主（包含 EM 且不以 EMA 开头）
    if "EM" in code and not code.startswith("EMA"):
        if "君主" not in res["types"]:
            res["types"].append("君主")
        # 仅括号内容定义所属势力（没有括号就不写所属势力）
        inner = re.search(r"\((.*?)\)", code)
        if inner:
            for part in split_multi_forces(inner.group(1)):
                nm = map_force_to_name(part)
                if nm:
                    res["所属势力"].append(nm)

    # 叛首
    if "REB(" in code:
        if "君主" not in res["types"]:
            res["types"].append("君主")
        if "叛首" not in res["types"]:
            res["types"].append("叛首")
        inner = re.search(r"\((.*?)\)", code)
        if inner:
            for part in split_multi_forces(inner.group(1)):
                nm = map_force_to_name(part)
                if nm:
                    res["所属势力"].append(nm)

    # 叛谍
    if "^" in code:
        if "叛谍" not in res["types"]:
            res["types"].append("叛谍")
        fake, real = code.split("^", 1)
        fake_parts = split_multi_forces(fake)
        real_prefix = re.match(r"^[A-Z&/]+", real)
        real_parts = split_multi_forces(real_prefix.group(0)) if real_prefix else []
        res["伪装势力"] = [map_force_to_name(p) for p in fake_parts if map_force_to_name(p)]
        res["所属势力"] = [map_force_to_name(p) for p in real_parts if map_force_to_name(p)]

    # 隐士
    if code.startswith("YS"):
        if "隐士" not in res["types"]:
            res["types"].append("隐士")

    # 普通武将默认匹配势力（君主无括号时不推颜色，也不额外匹配）
    if (
        not res["所属势力"]
        and not res["效忠势力"]
        and "^" not in code
        and not code.startswith("YS")
        and "EM" not in code  # 如果是君主没括号，不补默认势力
    ):
        prefix_match = re.match(r"^[A-Z&/]+", code)
        if prefix_match:
            for part in split_multi_forces(prefix_match.group(0)):
                nm = map_force_to_name(part)
                if nm:
                    res["所属势力"].append(nm)

    return res

# ------------------- 核心处理 -------------------

def scan_all_monarch_names(wb):
    monarch_names = set()
    for sheet_name in TARGET_SHEETS:
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

def process_sheet(ws, sheet_name, monarch_names):
    current_package = None
    generated_count = 0

    for row_idx in range(2, ws.max_row + 1):
        if ws.row_dimensions[row_idx].hidden:
            continue

        pkg_val = ws.cell(row=row_idx, column=COL_PACKAGE).value
        if pkg_val:
            current_package = str(pkg_val).strip()

        code_cell = ws.cell(row=row_idx, column=COL_CODE)
        code = str(code_cell.value).strip() if code_cell.value else ""
        hero_cell = ws.cell(row=row_idx, column=COL_NAME)
        hero_name = str(hero_cell.value).strip() if hero_cell.value else ""

        if not code or not hero_name or code.startswith(SKIP_PREFIXES):
            continue

        # 称号转简体
        raw_title = ws.cell(row=row_idx, column=COL_TITLE).value
        title = convert(str(raw_title), 'zh-cn') if raw_title else ""

        raw_hp = ws.cell(row=row_idx, column=COL_HP).value
        raw_hp = str(raw_hp).strip() if raw_hp else ""
        hp_value = HP_MAP.get(raw_hp, raw_hp)

        synergy = ws.cell(row=row_idx, column=COL_SYNERGY).value
        synergy = str(synergy).strip() if synergy else ""

        leadership = ws.cell(row=row_idx, column=COL_LEADERSHIP).value
        leadership = str(leadership).strip() if leadership else ""

        skill1_name = ws.cell(row=row_idx, column=COL_SKILL1_NAME).value or ""
        skill1_desc = ws.cell(row=row_idx, column=COL_SKILL1_DESC).value or ""
        skill2_name = ws.cell(row=row_idx, column=COL_SKILL2_NAME).value or ""
        skill2_desc = ws.cell(row=row_idx, column=COL_SKILL2_DESC).value or ""
        skill3_name = ws.cell(row=row_idx, column=COL_SKILL3_NAME).value or ""
        skill3_desc = ws.cell(row=row_idx, column=COL_SKILL3_DESC).value or ""

        # --- 势力&类型解析 ---
        parsed = parse_factions_from_code(code)
        types = parsed["types"][:]
        own_factions = parsed["所属势力"] + parsed["伪装势力"]

        guest_factions = []
        # 仅当不是君主/野心家/隐士才检测客将
        if (
            "君主" not in types
            and "野心家" not in types
            and "隐士" not in types
        ):
            guest_factions = detect_guest_factions(ws, row_idx, own_factions)
            if guest_factions:
                types.append("客将")

        # 如果不是君主，但名字在君主缓存里 → 可君主升变
        if "君主" not in types and hero_name in monarch_names:
            types.append("可君主升变")

        forces_for_tags = parsed["所属势力"]

        # tags
        all_tags = sort_tags_final(sheet_name, current_package, types, forces_for_tags, hero_name)

        # aliases
        aliases = [hero_name] + ([title] if title else [])

        # YAML
        yaml_lines = ["---"]
        yaml_lines.append(f"编号: {code}")
        yaml_lines.append(f"姓名: {hero_name}")
        if title:
            yaml_lines.append(f"称号: {title}")
        if hp_value:
            yaml_lines.append(f"体力值: {hp_value}")
        if synergy:
            yaml_lines.append(f"珠联璧合: {synergy}")
        if leadership:
            yaml_lines.append(f"统领能力: {leadership}")

        yaml_lines.append("tags:")
        for t in all_tags:
            yaml_lines.append(f"  - {t}")

        yaml_lines.append("aliases:")
        for a in aliases:
            yaml_lines.append(f"  - {a}")
        yaml_lines.append("---\n")

        # Body
        header_title = f"{title + '-' if title else ''}{hero_name}"
        body_lines = [f"# {header_title}\n"]

        if title:
            body_lines.append(f"**编号**: {code}  ")

        if types:
            body_lines.append(f"**武将类型**: {', '.join(types)}  ")
        if parsed["所属势力"]:
            body_lines.append(f"**所属势力**: {', '.join(parsed['所属势力'])}  ")
        if parsed["效忠势力"]:
            body_lines.append(f"**效忠势力**: {', '.join(parsed['效忠势力'])}  ")
        if parsed["伪装势力"]:
            body_lines.append(f"**伪装势力**: {', '.join(parsed['伪装势力'])}  ")
        if guest_factions:
            body_lines.append(f"**客将势力**: {', '.join(guest_factions)}  ")

        if hp_value:
            body_lines.append(f"**体力值**: {hp_value}  ")
        if synergy:
            body_lines.append(f"**珠联璧合**: {synergy}  ")
        if leadership:
            body_lines.append(f"**统领能力**: {leadership}  ")

        body_lines.append("\n---\n")

        if skill1_name.strip():
            body_lines.append(f"## {skill1_name.strip()}")
            if skill1_desc.strip():
                body_lines.append(skill1_desc.strip())
            body_lines.append("\n---\n")
        if skill2_name.strip():
            body_lines.append(f"## {skill2_name.strip()}")
            if skill2_desc.strip():
                body_lines.append(skill2_desc.strip())
            body_lines.append("\n---\n")
        if skill3_name.strip():
            body_lines.append(f"## {skill3_name.strip()}")
            if skill3_desc.strip():
                body_lines.append(skill3_desc.strip())
            body_lines.append("\n---\n")

        md_content = "\n".join(yaml_lines + body_lines).strip() + "\n"
        safe_filename = sanitize_filename(f"{code} {hero_name}.md")
        filepath = os.path.join(OUTPUT_DIR, safe_filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)

        generated_count += 1
        print(f"✅ 生成/覆盖: {safe_filename}")

    return generated_count

def main():
    print(f"📖 加载 Excel: {EXCEL_PATH}")
    wb = load_workbook(EXCEL_PATH)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    monarch_names = scan_all_monarch_names(wb)
    print(f"📌 缓存君主武将名: {len(monarch_names)} 个")

    total_count = 0
    for sheet_name in TARGET_SHEETS:
        print(f"\n🔄 解析 Sheet: {sheet_name}")
        ws = wb[sheet_name]
        count = process_sheet(ws, sheet_name, monarch_names)
        total_count += count

    print(f"\n🎉 所有武将笔记已生成完毕！共生成 {total_count} 条")

if __name__ == "__main__":
    main()
