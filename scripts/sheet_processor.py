"""
处理指定工作表中的武将数据，生成 Markdown 文件。
"""

import os
from zhconv import convert
from constants import (
    COL_PACKAGE,
    COL_CODE,
    COL_NAME,
    COL_TITLE,
    COL_HP,
    COL_SYNERGY,
    COL_LEADERSHIP,
    COL_SKILL1_NAME,
    COL_SKILL1_DESC,
    COL_SKILL2_NAME,
    COL_SKILL2_DESC,
    COL_SKILL3_NAME,
    COL_SKILL3_DESC,
    SKIP_PREFIXES,
    HP_MAP,
    OUTPUT_DIR,
    IGNORED_PACKAGES,
)
from utils import sanitize_filename, detect_guest_factions, sort_tags_final
from parsers import parse_factions_from_code


def process_sheet(ws, sheet_name, monarch_names):
    """处理指定工作表中的武将数据，生成 Markdown 文件"""
    current_package = None
    count = 0

    for row_idx in range(2, ws.max_row + 1):
        if ws.row_dimensions[row_idx].hidden:
            continue

        pkg_val = ws.cell(row=row_idx, column=COL_PACKAGE).value
        if pkg_val:
            pkg_val_str = str(pkg_val).strip()
            if pkg_val_str not in IGNORED_PACKAGES:
                current_package = pkg_val_str

        code_cell = ws.cell(row=row_idx, column=COL_CODE)
        code = str(code_cell.value).strip() if code_cell.value else ""
        hero_cell = ws.cell(row=row_idx, column=COL_NAME)
        hero_name = str(hero_cell.value).strip() if hero_cell.value else ""
        hero_name = hero_name.replace("&", "_")

        if not code or not hero_name or code.startswith(SKIP_PREFIXES):
            continue

        # 称号转简体
        raw_title = ws.cell(row=row_idx, column=COL_TITLE).value
        title = convert(str(raw_title), "zh-cn") if raw_title else ""

        raw_hp = ws.cell(row=row_idx, column=COL_HP).value
        raw_hp = str(raw_hp).strip() if raw_hp else ""
        hp_value = HP_MAP.get(raw_hp, raw_hp)

        synergy = ws.cell(row=row_idx, column=COL_SYNERGY).value
        synergy = str(synergy).strip().replace("&", "_") if synergy else ""

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

        own_forces = parsed["所属势力"]  # 叛谍只有真实势力
        disguise_forces = parsed["伪装势力"]  # 叛谍伪装势力

        guest_factions = detect_guest_factions(ws, row_idx, own_forces, disguise_forces)
        if guest_factions:
            types.append("客将")

        # 如果此武将不是君主，但名字在君主缓存里 → 可君主升变
        if "君主" not in types and hero_name in monarch_names:
            types.append("可君主升变")

        # 所属势力（用于 tags）
        forces_for_tags = parsed["所属势力"]

        # tags 生成
        all_tags = sort_tags_final(
            sheet_name,
            current_package,
            types,
            hero_name,
            forces_for_tags,
            parsed["效忠势力"],
            parsed["伪装势力"],
            guest_factions,
        )

        # aliases
        aliases = [hero_name] + ([title] if title else [])

        # -------- YAML --------
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

        # -------- Body --------
        header_title = f"{title + '-' if title else ''}{hero_name}"
        body_lines = [f"# {header_title}\n"]

        if title:
            body_lines.append(f"**编号**: {code}  ")

        if types:
            body_lines.append(f"**武将类型**: {', '.join(types)}  ")
        if parsed["所属势力"]:
            body_lines.append(
                f"**所属势力**: {', '.join(x + '势力' for x in parsed['所属势力'])}  "
            )
        if parsed["效忠势力"]:
            body_lines.append(
                f"**效忠势力**: {', '.join(x + '势力' for x in parsed['效忠势力'])}  "
            )
        if parsed["伪装势力"]:
            body_lines.append(
                f"**伪装势力**: {', '.join(x + '势力' for x in parsed['伪装势力'])}  "
            )
        if guest_factions:
            body_lines.append(
                f"**客将势力**: {', '.join(x + '势力' for x in guest_factions)}  "
            )

        if hp_value:
            body_lines.append(f"**体力值**: {hp_value}  ")
        if synergy:
            body_lines.append(f"**珠联璧合**: {synergy}  ")
        if leadership:
            body_lines.append(f"**统领能力**: {leadership}  ")

        body_lines.append("\n---\n")

        # 技能
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

        print(f"✅ 生成/覆盖: {safe_filename}")
        count += 1

    return count
