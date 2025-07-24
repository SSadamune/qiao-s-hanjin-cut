import os
import re
from openpyxl import load_workbook
from zhconv import convert

VAULT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXCEL_PATH = os.path.join(VAULT_PATH, "resources", "乔剪国战表格.xlsx")
OUTPUT_DIR = os.path.join(VAULT_PATH, "notes", "武将")

HP_MAP = {"696": 1.5, "6969": 2.0, "69696": 2.5}
SKIP_PREFIXES = ("黑桃", "梅花", "红桃", "方片", "EMA", "Z.")

force_map = {
    "AM": "野心家",
    "HAN": "汉势力",
    "WEI": "魏势力",
    "SHU": "蜀势力",
    "WU": "吴势力",
    "QUN": "群势力",
    "JIN": "晋势力"
}

TARGET_SHEETS = [
    "官方范围",
    "兵情篇",
    "豪门贵胄",
    "异军突起",
    "小型扩展",
    "他山之玉"
]

SPECIAL_ORDER = {
    "君主": 0,
    "野心家": 1,
    "叛首": 2,
    "叛谍": 3
}

# Excel 列号常量（1-based）
COL_PACKAGE = 1        # 分包
COL_CODE = 2           # 编号
COL_NAME = 3           # 姓名
COL_TITLE = 4          # 称号
COL_HP = 5             # 体力值
COL_SYNERGY = 6        # 珠联璧合
COL_LEADERSHIP = 7     # 统领能力
COL_SKILL1_NAME = 8    # 技能1 名
COL_SKILL1_DESC = 9    # 技能1 描述
COL_SKILL2_NAME = 10   # 技能2 名
COL_SKILL2_DESC = 11   # 技能2 描述
COL_SKILL3_NAME = 12   # 技能3 名
COL_SKILL3_DESC = 13   # 技能3 描述

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|\r\n]+', '_', name).strip()

def detect_special_prefixes(code: str):
    """检测编号里包含的特殊身份前缀，返回 ['君主','野心家','叛首','叛谍']"""
    tags = []

    # EM (但不含 EMA)
    if "EM" in code and not code.startswith("EMA"):
        tags.append("君主")

    # AM 野心家
    if "AM" in code:
        tags.append("野心家")

    # REB 叛首
    if "REB" in code:
        tags.append("叛首")

    # ^ 叛谍
    if "^" in code:
        tags.append("叛谍")

    return list(set(tags))

def split_multi_forces(force_str: str):
    """把多势力字符串按 & 或 / 分割"""
    return re.split(r"[&/]", force_str)

def _split_and_map_forces(force_str: str):
    """映射势力前缀到中文势力名"""
    forces = []
    for part in split_multi_forces(force_str):
        for k, v in force_map.items():
            if part.startswith(k):
                forces.append(v)
                break
    return list(set(forces))

def parse_forces(code: str):
    """
    解析势力：
    - 优先括号
    - 其次 ^ 后部分
    - 否则全局解析
    """
    # 括号内容
    if "(" in code and ")" in code:
        inner = re.search(r"\((.*?)\)", code)
        if inner:
            return _split_and_map_forces(inner.group(1))

    # ^ 后
    if "^" in code:
        rest = code.split("^", 1)[1]
        return _split_and_map_forces(rest)

    # 普通
    return _split_and_map_forces(code)

def dedup_and_sort_tags(tags, sheet_name, package_name, forces, hero_name):
    """去重并固定顺序排序"""
    seen = set()
    deduped = []
    for t in tags:
        if t not in seen:
            deduped.append(t)
            seen.add(t)

    def sort_key(tag):
        if tag == "武将":
            return (0, 0)
        if tag == sheet_name:
            return (1, 0)
        if package_name and tag == package_name:
            return (2, 0)
        if tag in SPECIAL_ORDER:  # 固定身份顺序
            return (3, SPECIAL_ORDER[tag])
        if tag in forces:  # 势力们
            return (4, tag)
        if tag == hero_name:
            return (5, 0)
        return (6, tag)

    return sorted(deduped, key=sort_key)

def process_sheet(ws, sheet_tag: str):
    current_package = None

    for row_idx in range(2, ws.max_row + 1):
        if ws.row_dimensions[row_idx].hidden:
            continue

        package_val = ws.cell(row=row_idx, column=COL_PACKAGE).value
        if package_val:
            current_package = str(package_val).strip()

        code_cell = ws.cell(row=row_idx, column=COL_CODE)
        code = str(code_cell.value).strip() if code_cell.value else ""

        hero_cell = ws.cell(row=row_idx, column=COL_NAME)
        hero_name = str(hero_cell.value).strip() if hero_cell.value else ""

        if not code or not hero_name or code == "nan" or hero_name == "nan":
            continue

        if code.startswith(SKIP_PREFIXES):
            continue

        raw_title = ws.cell(row=row_idx, column=COL_TITLE).value
        title = convert(str(raw_title), 'zh-cn') if raw_title else ""

        raw_hp = ws.cell(row=row_idx, column=COL_HP).value
        raw_hp = str(raw_hp).strip() if raw_hp else ""
        hp_value = HP_MAP.get(raw_hp, raw_hp)

        synergy_val = ws.cell(row=row_idx, column=COL_SYNERGY).value
        synergy = str(synergy_val).strip() if synergy_val else ""

        leadership_val = ws.cell(row=row_idx, column=COL_LEADERSHIP).value
        leadership = str(leadership_val).strip() if leadership_val else ""

        skill1_name_val = ws.cell(row=row_idx, column=COL_SKILL1_NAME).value
        skill1_name = str(skill1_name_val).strip() if skill1_name_val else ""
        skill1_desc_val = ws.cell(row=row_idx, column=COL_SKILL1_DESC).value
        skill1_desc = str(skill1_desc_val).strip() if skill1_desc_val else ""

        skill2_name_val = ws.cell(row=row_idx, column=COL_SKILL2_NAME).value
        skill2_name = str(skill2_name_val).strip() if skill2_name_val else ""
        skill2_desc_val = ws.cell(row=row_idx, column=COL_SKILL2_DESC).value
        skill2_desc = str(skill2_desc_val).strip() if skill2_desc_val else ""

        skill3_name_val = ws.cell(row=row_idx, column=COL_SKILL3_NAME).value
        skill3_name = str(skill3_name_val).strip() if skill3_name_val else ""
        skill3_desc_val = ws.cell(row=row_idx, column=COL_SKILL3_DESC).value
        skill3_desc = str(skill3_desc_val).strip() if skill3_desc_val else ""

        base_tags = ["武将", hero_name]
        if current_package:
            base_tags.append(current_package)
        base_tags.append(sheet_tag)

        # 检测编号中的特殊身份tag
        special_tags = detect_special_prefixes(code)

        # 解析势力
        force_tags = parse_forces(code)

        # 合并tags
        raw_tags = base_tags + special_tags + force_tags
        all_tags = dedup_and_sort_tags(
            raw_tags,
            sheet_name=sheet_tag,
            package_name=current_package or "",
            forces=force_tags,
            hero_name=hero_name
        )

        # YAML frontmatter
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

        tags_block = "\n  - ".join(all_tags)
        yaml_lines.append("tags:\n  - " + tags_block)

        aliases_list = [hero_name]
        if title:
            aliases_list.append(title)
        aliases_block = "\n  - ".join(aliases_list)
        yaml_lines.append("aliases:\n  - " + aliases_block)

        yaml_lines.append("---\n")

        # body
        body_lines = [f"# {title + '-' if title else ''}{hero_name}\n"]
        if title:
            body_lines.append(f"**编号**: {code}  ")
        if hp_value:
            body_lines.append(f"**体力值**: {hp_value}  ")
        if synergy:
            body_lines.append(f"**珠联璧合**: {synergy}  ")
        if leadership:
            body_lines.append(f"**统领能力**: {leadership}  ")

        body_lines.append("\n---\n")

        if skill1_name:
            body_lines.append(f"## {skill1_name}")
            if skill1_desc:
                body_lines.append(skill1_desc)
            body_lines.append("\n---\n")
        if skill2_name:
            body_lines.append(f"## {skill2_name}")
            if skill2_desc:
                body_lines.append(skill2_desc)
            body_lines.append("\n---\n")
        if skill3_name:
            body_lines.append(f"## {skill3_name}")
            if skill3_desc:
                body_lines.append(skill3_desc)
            body_lines.append("\n---\n")

        md_content = "\n".join(yaml_lines + body_lines).strip() + "\n"

        safe_filename = sanitize_filename(f"{code} {hero_name}.md")
        filepath = os.path.join(OUTPUT_DIR, safe_filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"✅ 生成/覆盖: {safe_filename}")

def main():
    print(f"📖 加载 Excel: {EXCEL_PATH}")
    wb = load_workbook(EXCEL_PATH)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for sheet_name in TARGET_SHEETS:
        print(f"\n🔄 解析 Sheet: {sheet_name}")
        ws = wb[sheet_name]
        process_sheet(ws, sheet_name)

    print("\n🎉 所有武将笔记已生成完毕！")

if __name__ == "__main__":
    main()
