import os
import re
import pandas as pd

# === 配置部分 ===

# Vault 根目录
VAULT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Excel 文件路径
EXCEL_PATH = os.path.join(VAULT_PATH, "resources", "乔剪国战表格.xlsx")

# 输出 Markdown 的目录
OUTPUT_DIR = os.path.join(VAULT_PATH, "notes", "武将")

# 体力值映射规则
HP_MAP = {
    "696": 1.5,
    "6969": 2.0,
    "69696": 2.5,
}

# 跳过的前缀
SKIP_PREFIXES = ("黑桃", "梅花", "红桃", "方片", "EMA")

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

# 需要解析的目标 sheet
TARGET_SHEETS = [
    "官方范围",
    # "兵情篇",
    # "豪门贵胄",
    # "异军突起",
    # "小型扩展",
    # "他山之玉"
]


def parse_forces(code: str):
    """根据编号解析势力"""
    code = code.strip()
    forces = []

    # AM开头 → 直接野心家，不附加其他势力
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
        return list(set(forces))  # 去重

    # 单势力前缀
    for k, v in force_map.items():
        if code.startswith(k):
            forces.append(v)
            break

    return forces


def process_dataframe(df: pd.DataFrame, sheet_tag: str):
    """处理一个 sheet 的 DataFrame"""
    global OUTPUT_DIR
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    current_package = None

    for _, row in df.iterrows():
        # A列 = 分包
        分包 = str(row.get("分包/势力", "")).strip()
        if 分包 and 分包 != "nan":
            current_package = 分包

        # B列 = 编号
        编号 = str(row.get("编号", "")).strip()
        姓名 = str(row.get("姓名", "")).strip()

        # 跳过空编号/姓名
        if not 编号 or not 姓名 or 编号 == "nan" or 姓名 == "nan":
            continue

        # 跳过卡牌/标记物
        if 编号.startswith(SKIP_PREFIXES):
            continue

        # 解析势力
        forces = parse_forces(编号)

        # 称号
        称号 = str(row.get("称号", "")).strip()
        # 体力值
        raw_hp = str(row.get("体力值", "")).strip()
        体力值 = HP_MAP.get(raw_hp, raw_hp if raw_hp != "nan" else "")
        # 珠联璧合
        珠联璧合 = str(row.get("珠联璧合", "")).strip()
        # 统领能力
        统领能力 = str(row.get("统领能力", "")).strip()

        # 技能1~3
        技能1名 = str(row.get("技能1", "")).strip()
        技能1描述 = str(row.iloc[8]).strip() if len(row) > 8 else ""
        技能2名 = str(row.get("技能2", "")).strip()
        技能2描述 = str(row.iloc[10]).strip() if len(row) > 10 else ""
        技能3名 = str(row.get("技能3", "")).strip()
        技能3描述 = str(row.iloc[12]).strip() if len(row) > 12 else ""

        # === YAML 头部 ===
        yaml_lines = ["---"]
        yaml_lines.append(f"编号: {编号}")
        yaml_lines.append(f"姓名: {姓名}")
        if 称号 and 称号 != "nan":
            yaml_lines.append(f"称号: {称号}")
        if 体力值 and 体力值 != "nan":
            yaml_lines.append(f"体力值: {体力值}")
        if 珠联璧合 and 珠联璧合 != "nan":
            yaml_lines.append(f"珠联璧合: {珠联璧合}")
        if 统领能力 and 统领能力 != "nan":
            yaml_lines.append(f"统领能力: {统领能力}")

        # tags = 武将 + 姓名 + 分包(如果有) + 势力 + sheet名
        all_tags = ["武将", 姓名]
        if current_package:
            all_tags.append(current_package)
        all_tags.extend(forces)
        # 无论是否有分包，都额外加上 sheet 名作为 tag
        all_tags.append(sheet_tag)

        tags_block = "\n  - ".join(all_tags)
        yaml_lines.append("tags:\n  - " + tags_block)

        # aliases = 姓名 + 称号
        aliases_list = [姓名]
        if 称号 and 称号 != "nan":
            aliases_list.append(称号)
        aliases_block = "\n  - ".join(aliases_list)
        yaml_lines.append("aliases:\n  - " + aliases_block)

        yaml_lines.append("---\n")

        # === 正文 ===
        body_lines = [f"# {姓名} ({编号})\n"]
        if 称号 and 称号 != "nan":
            body_lines.append(f"**称号**: {称号}  ")
        if 体力值 and 体力值 != "nan":
            body_lines.append(f"**体力值**: {体力值}  ")
        if 珠联璧合 and 珠联璧合 != "nan":
            body_lines.append(f"**珠联璧合**: {珠联璧合}  ")
        if 统领能力 and 统领能力 != "nan":
            body_lines.append(f"**统领能力**: {统领能力}  ")

        body_lines.append("\n---\n")

        # 技能1~3
        if 技能1名 and 技能1名 != "nan":
            body_lines.append(f"## {技能1名}")
            if 技能1描述 and 技能1描述 != "nan":
                body_lines.append(技能1描述)
            body_lines.append("\n---\n")

        if 技能2名 and 技能2名 != "nan":
            body_lines.append(f"## {技能2名}")
            if 技能2描述 and 技能2描述 != "nan":
                body_lines.append(技能2描述)
            body_lines.append("\n---\n")

        if 技能3名 and 技能3名 != "nan":
            body_lines.append(f"## {技能3名}")
            if 技能3描述 and 技能3描述 != "nan":
                body_lines.append(技能3描述)
            body_lines.append("\n---\n")

        # === 合并内容 ===
        md_content = "\n".join(yaml_lines + body_lines).strip() + "\n"

        # 输出文件路径（覆盖模式）
        safe_filename = sanitize_filename(f"{编号} {姓名}.md")
        filepath = os.path.join(OUTPUT_DIR, safe_filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"✅ 生成/覆盖: {safe_filename}")
        
        
def sanitize_filename(name: str) -> str:
    # 替换所有 Windows/macOS 不允许的字符
    safe = re.sub(r'[\\/:*?"<>|\r\n]+', '_', name)
    # 去掉首尾空格
    return safe.strip()


# === 主流程 ===
print(f"📖 读取 Excel: {EXCEL_PATH}")

for sheet_name in TARGET_SHEETS:
    print(f"\n🔄 解析 Sheet: {sheet_name}")
    df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)
    process_dataframe(df, sheet_name)

print("\n🎉 所有武将笔记已生成并覆盖完成！")
