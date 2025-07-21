import os
import re
from openpyxl import load_workbook
from zhconv import convert

# === 配置 ===

VAULT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXCEL_PATH = os.path.join(VAULT_PATH, "resources", "乔剪国战表格.xlsx")
OUTPUT_DIR = os.path.join(VAULT_PATH, "notes", "武将")

# 体力值映射
HP_MAP = {"696": 1.5, "6969": 2.0, "69696": 2.5}

# 跳过的编号前缀
SKIP_PREFIXES = ("黑桃", "梅花", "红桃", "方片", "EMA", "Z.") 

# 势力映射
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
    """安全文件名"""
    return re.sub(r'[\\/:*?"<>|\r\n]+', '_', name).strip()

def parse_forces(code: str):
    """正常编号解析势力（不处理删除线）"""
    code = code.strip()
    forces = []

    # AM开头 → 野心家
    if code.startswith("AM"):
        return ["野心家"]

    # EM(SHU001) 特殊处理
    if code.startswith("EM(") and not code.startswith("EMA"):
        inner = re.search(r"\((.*?)\)", code)
        if inner:
            inner_code = inner.group(1)
            return parse_forces(inner_code)

    # 多势力: HAN&WEI&SHU001
    if "&" in code:
        parts = code.split("&")
        for part in parts:
            for k, v in force_map.items():
                if part.startswith(k):
                    forces.append(v)
                    break
        return list(set(forces))

    # 单势力前缀
    for k, v in force_map.items():
        if code.startswith(k):
            forces.append(v)
            break

    return forces

def handle_strike_code(code: str):
    """
    解析叛谍编号:
    - 第一个前缀是假势力，后续部分为真势力序列+后缀
    - 返回转换后的编号 + 真势力代码列表
    """
    fake = None
    rest = code
    for k in force_map.keys():   # 找第一个假势力
        if code.startswith(k):
            fake = k
            rest = code[len(k):]  # 剩余部分 = 真势力序列 + 后缀
            break
    if not fake:
        # 没识别假势力 → 原样加 !
        return f"!{code}", []

    # 真势力列表
    true_forces = []
    pos = 0
    while pos < len(rest):
        matched = False
        for k in force_map.keys():
            if rest[pos:].startswith(k):
                true_forces.append(k)
                pos += len(k)
                matched = True
                break
        if not matched:
            break  # 到后缀了

    suffix = rest[pos:]  # 真势力后缀编号
    # 最终编号 = !(假势力) + 真势力序列 + 后缀
    new_code = f"!({fake}){''.join(true_forces)}{suffix}"
    return new_code, true_forces

def process_sheet(ws, sheet_tag: str):
    current_package = None

    for row_idx in range(2, ws.max_row + 1):  # 从第2行开始
        # 跳过隐藏行
        if ws.row_dimensions[row_idx].hidden:
            continue

        # === 读取列 ===
        分包_val = ws.cell(row=row_idx, column=1).value  # A列 分包
        if 分包_val:
            current_package = str(分包_val).strip()

        编号_cell = ws.cell(row=row_idx, column=2)  # B列
        编号 = str(编号_cell.value).strip() if 编号_cell.value else ""
        姓名 = str(ws.cell(row=row_idx, column=3).value).strip() if ws.cell(row=row_idx, column=3).value else ""

        # 跳过空编号/姓名
        if not 编号 or not 姓名 or 编号 == "nan" or 姓名 == "nan":
            continue

        # 跳过卡牌/标记物
        if 编号.startswith(SKIP_PREFIXES):
            continue

        # 检查删除线
        has_strike = bool(编号_cell.font.strike)

        # 称号（D列）繁体转简体
        raw_title = ws.cell(row=row_idx, column=4).value
        称号 = convert(str(raw_title), 'zh-cn') if raw_title else ""

        # 体力值 E列
        raw_hp = ws.cell(row=row_idx, column=5).value
        raw_hp = str(raw_hp).strip() if raw_hp else ""
        体力值 = HP_MAP.get(raw_hp, raw_hp)

        # 珠联璧合 F列
        珠联璧合 = str(ws.cell(row=row_idx, column=6).value).strip() if ws.cell(row=row_idx, column=6).value else ""

        # 统领能力 G列
        统领能力 = str(ws.cell(row=row_idx, column=7).value).strip() if ws.cell(row=row_idx, column=7).value else ""

        # 技能1 H列 & I列
        技能1名 = str(ws.cell(row=row_idx, column=8).value).strip() if ws.cell(row=row_idx, column=8).value else ""
        技能1描述 = str(ws.cell(row=row_idx, column=9).value).strip() if ws.cell(row=row_idx, column=9).value else ""
        # 技能2 J列 & K列
        技能2名 = str(ws.cell(row=row_idx, column=10).value).strip() if ws.cell(row=row_idx, column=10).value else ""
        技能2描述 = str(ws.cell(row=row_idx, column=11).value).strip() if ws.cell(row=row_idx, column=11).value else ""
        # 技能3 L列 & M列
        技能3名 = str(ws.cell(row=row_idx, column=12).value).strip() if ws.cell(row=row_idx, column=12).value else ""
        技能3描述 = str(ws.cell(row=row_idx, column=13).value).strip() if ws.cell(row=row_idx, column=13).value else ""

        # === 初始tags ===
        base_tags = ["武将", 姓名]
        if current_package:
            base_tags.append(current_package)
        base_tags.append(sheet_tag)  # sheet名也加入tag

        # === 编号处理 ===
        final_code = 编号
        extra_tags = []
        势力tags = []

        if has_strike:
            # 删除线编号 → 假势力/真势力解析
            final_code, true_forces = handle_strike_code(编号)
            势力tags = [force_map[k] for k in true_forces]
            extra_tags.append("叛谍")
        else:
            # 正常编号解析势力
            parsed_forces = parse_forces(编号)
            势力tags = parsed_forces

        # 额外tag逻辑
        if 编号.startswith("EM") and not 编号.startswith("EMA"):
            extra_tags.append("君主")
        if 编号.startswith("REB"):
            extra_tags.append("叛首")

        # 合并tags
        all_tags = base_tags + 势力tags + extra_tags

        # === YAML 头部 ===
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

        # tags block
        tags_block = "\n  - ".join(all_tags)
        yaml_lines.append("tags:\n  - " + tags_block)

        # aliases block
        aliases_list = [姓名]
        if 称号:
            aliases_list.append(称号)
        aliases_block = "\n  - ".join(aliases_list)
        yaml_lines.append("aliases:\n  - " + aliases_block)

        yaml_lines.append("---\n")

        # === 正文 ===
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

        # 合并内容
        md_content = "\n".join(yaml_lines + body_lines).strip() + "\n"

        # 输出文件
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
