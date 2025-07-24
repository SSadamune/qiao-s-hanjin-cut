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

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|\r\n]+', '_', name).strip()

def parse_true_forces(code: str):
    """只解析 ^ 后的真势力（支持 & 多势力）"""
    if "^" in code:
        rest = code.split("^", 1)[1]  # 取 ^ 之后
    else:
        rest = code

    forces = []
    # 多势力用 & 连接
    for part in rest.split("&"):
        for k, v in force_map.items():
            if part.startswith(k):
                forces.append(v)
                break
    return list(set(forces))

def process_sheet(ws, sheet_tag: str):
    current_package = None

    for row_idx in range(2, ws.max_row + 1):
        if ws.row_dimensions[row_idx].hidden:
            continue

        分包_val = ws.cell(row=row_idx, column=1).value
        if 分包_val:
            current_package = str(分包_val).strip()

        编号_cell = ws.cell(row=row_idx, column=2)
        编号 = str(编号_cell.value).strip() if 编号_cell.value else ""
        姓名 = str(ws.cell(row=row_idx, column=3).value).strip() if ws.cell(row=row_idx, column=3).value else ""

        if not 编号 or not 姓名 or 编号 == "nan" or 姓名 == "nan":
            continue

        if 编号.startswith(SKIP_PREFIXES):
            continue

        raw_title = ws.cell(row=row_idx, column=4).value
        称号 = convert(str(raw_title), 'zh-cn') if raw_title else ""

        raw_hp = ws.cell(row=row_idx, column=5).value
        raw_hp = str(raw_hp).strip() if raw_hp else ""
        体力值 = HP_MAP.get(raw_hp, raw_hp)

        珠联璧合 = str(ws.cell(row=row_idx, column=6).value).strip() if ws.cell(row=row_idx, column=6).value else ""
        统领能力 = str(ws.cell(row=row_idx, column=7).value).strip() if ws.cell(row=row_idx, column=7).value else ""

        技能1名 = str(ws.cell(row=row_idx, column=8).value).strip() if ws.cell(row=row_idx, column=8).value else ""
        技能1描述 = str(ws.cell(row=row_idx, column=9).value).strip() if ws.cell(row=row_idx, column=9).value else ""
        技能2名 = str(ws.cell(row=row_idx, column=10).value).strip() if ws.cell(row=row_idx, column=10).value else ""
        技能2描述 = str(ws.cell(row=row_idx, column=11).value).strip() if ws.cell(row=row_idx, column=11).value else ""
        技能3名 = str(ws.cell(row=row_idx, column=12).value).strip() if ws.cell(row=row_idx, column=12).value else ""
        技能3描述 = str(ws.cell(row=row_idx, column=13).value).strip() if ws.cell(row=row_idx, column=13).value else ""

        base_tags = ["武将", 姓名]
        if current_package:
            base_tags.append(current_package)
        base_tags.append(sheet_tag)

        final_code = 编号
        extra_tags = []

        # 通过 ^ 判断叛谍
        if "^" in 编号:
            extra_tags.append("叛谍")

        # EM 君主 & REB 叛首
        if 编号.startswith("EM") and not 编号.startswith("EMA"):
            extra_tags.append("君主")
        if 编号.startswith("REB"):
            extra_tags.append("叛首")

        # 解析真势力标签（只取 ^ 之后部分）
        势力tags = parse_true_forces(编号)

        all_tags = base_tags + 势力tags + extra_tags

        yaml_lines = ["---"]
        yaml_lines.append(f"编号: {final_code}")
        yaml_lines.append(f"姓名: {姓名}")
        if 称号:
            yaml_lines.append(f"称号: {称号}")
        if 体力值:
            yaml_lines.append(f"体力值: {体力值}")
        if 珠联璧合:
            yaml_lines.append(f"珠联璧合: {珠联璧合}")
        if 统领能力:
            yaml_lines.append(f"统领能力: {统领能力}")

        tags_block = "\n  - ".join(all_tags)
        yaml_lines.append("tags:\n  - " + tags_block)

        aliases_list = [姓名]
        if 称号:
            aliases_list.append(称号)
        aliases_block = "\n  - ".join(aliases_list)
        yaml_lines.append("aliases:\n  - " + aliases_block)

        yaml_lines.append("---\n")

        body_lines = [f"# {姓名} ({final_code})\n"]
        if 称号:
            body_lines.append(f"**称号**: {称号}  ")
        if 体力值:
            body_lines.append(f"**体力值**: {体力值}  ")
        if 珠联璧合:
            body_lines.append(f"**珠联璧合**: {珠联璧合}  ")
        if 统领能力:
            body_lines.append(f"**统领能力**: {统领能力}  ")

        body_lines.append("\n---\n")

        if 技能1名:
            body_lines.append(f"## {技能1名}")
            if 技能1描述:
                body_lines.append(技能1描述)
            body_lines.append("\n---\n")
        if 技能2名:
            body_lines.append(f"## {技能2名}")
            if 技能2描述:
                body_lines.append(技能2描述)
            body_lines.append("\n---\n")
        if 技能3名:
            body_lines.append(f"## {技能3名}")
            if 技能3描述:
                body_lines.append(技能3描述)
            body_lines.append("\n---\n")

        md_content = "\n".join(yaml_lines + body_lines).strip() + "\n"

        safe_filename = sanitize_filename(f"{final_code} {姓名}.md")
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
