"""
卡牌处理器，负责加载Excel文件中的卡牌数据并生成Markdown笔记。
"""

import os
import pandas as pd
from openpyxl import load_workbook
from domain.heroes.constants import OUTPUT_DIR

# 卡牌输出目录
CARD_OUTPUT_DIR = os.path.join(os.path.dirname(OUTPUT_DIR), "游戏牌")


def sanitize_filename(name: str) -> str:
    """将文件名中的非法字符替换为下划线，并去除首尾空格"""
    import re

    return re.sub(r'[\\/:*?"<>|\r\n]+', "_", name).strip()


def process_card_sheet(df):
    """处理卡牌数据，生成Markdown文件"""
    count = 0

    for index, row in df.iterrows():
        # 获取卡牌信息
        card_name = str(row["牌名"]).strip() if pd.notna(row["牌名"]) else ""
        card_type = str(row["类别"]).strip() if pd.notna(row["类别"]) else ""
        sub_type = str(row["副类别"]).strip() if pd.notna(row["副类别"]) else ""
        timing = str(row["使用时机"]).strip() if pd.notna(row["使用时机"]) else ""
        target = str(row["使用目标"]).strip() if pd.notna(row["使用目标"]) else ""
        special_desc = str(row["特殊描述"]).strip() if pd.notna(row["特殊描述"]) else ""
        effect = str(row["作用效果"]).strip() if pd.notna(row["作用效果"]) else ""
        follow_up = str(row["后续动作"]).strip() if pd.notna(row["后续动作"]) else ""

        # 方法2的信息
        timing2 = (
            str(row["使用时机（方法2）"]).strip()
            if pd.notna(row["使用时机（方法2）"])
            else ""
        )
        target2 = (
            str(row["使用目标（方法2）"]).strip()
            if pd.notna(row["使用目标（方法2）"])
            else ""
        )
        effect2 = (
            str(row["作用效果（方法2）"]).strip()
            if pd.notna(row["作用效果（方法2）"])
            else ""
        )
        follow_up2 = (
            str(row["后续动作（方法2）"]).strip()
            if pd.notna(row["后续动作（方法2）"])
            else ""
        )

        if not card_name or card_name == "牌名":
            continue

        # 生成YAML头部
        yaml_lines = ["---"]
        yaml_lines.append(f"牌名: {card_name}")
        if card_type:
            yaml_lines.append(f"类别: {card_type}")
        if sub_type:
            yaml_lines.append(f"副类别: {sub_type}")

        # 生成tags
        tags = ["游戏牌"]
        if card_type:
            tags.append(card_type)
        if sub_type:
            tags.append(sub_type)
        tags.append(card_name)

        yaml_lines.append("tags:")
        for tag in tags:
            yaml_lines.append(f"  - {tag}")

        yaml_lines.append("aliases:")
        yaml_lines.append(f"  - {card_name}")
        yaml_lines.append("---\n")

        # 生成正文
        body_lines = [f"# {card_name}\n"]

        if card_type:
            body_lines.append(f"**类别**: {card_type}  ")
        if sub_type:
            body_lines.append(f"**副类别**: {sub_type}  ")
        if special_desc:
            body_lines.append(f"**特殊描述**: {special_desc}  ")

        # 判断是否有两种使用方法
        has_method2 = timing2 or target2 or effect2 or follow_up2

        if has_method2:
            # 有两种使用方法
            body_lines.append("\n---\n")
            body_lines.append("## 使用方法　①\n")

            if timing:
                body_lines.append(f"**使用时机**: {timing}  ")
            if target:
                body_lines.append(f"**使用目标**: {target}  ")
            if effect:
                body_lines.append(f"**作用效果**: {effect}  ")
            if follow_up:
                body_lines.append(f"**后续动作**: {follow_up}  ")

            body_lines.append("\n---\n")
            body_lines.append("## 使用方法　②\n")

            if timing2:
                body_lines.append(f"**使用时机**: {timing2}  ")
            if target2:
                body_lines.append(f"**使用目标**: {target2}  ")
            if effect2:
                body_lines.append(f"**作用效果**: {effect2}  ")
            if follow_up2:
                body_lines.append(f"**后续动作**: {follow_up2}  ")
        else:
            # 只有一种使用方法
            if timing:
                body_lines.append(f"**使用时机**: {timing}  ")
            if target:
                body_lines.append(f"**使用目标**: {target}  ")
            if effect:
                body_lines.append(f"**作用效果**: {effect}  ")
            if follow_up:
                body_lines.append(f"**后续动作**: {follow_up}  ")

        # 生成完整内容
        md_content = "\n".join(yaml_lines + body_lines).strip() + "\n"

        # 根据类别确定子目录
        sub_dir = ""
        if card_type == "基本牌":
            sub_dir = "基本牌"
        elif card_type == "锦囊牌":
            sub_dir = "锦囊牌"
        elif card_type == "装备牌":
            sub_dir = "装备牌"

        # 创建子目录路径
        if sub_dir:
            card_dir = os.path.join(CARD_OUTPUT_DIR, sub_dir)
        else:
            card_dir = CARD_OUTPUT_DIR

        # 确保输出目录存在
        os.makedirs(card_dir, exist_ok=True)

        # 保存文件
        safe_filename = sanitize_filename(f"{card_name}.md")
        filepath = os.path.join(card_dir, safe_filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"✅ 生成/覆盖: {safe_filename}")
        count += 1

    return count


def main():
    """主函数，负责加载Excel文件并处理卡牌数据"""
    excel_path = os.path.join(
        os.path.dirname(__file__), "..", "resources", "乔剪国战全牌表.xlsx"
    )
    print(f"📖 加载 Excel: {excel_path}")

    # 读取卡面描述sheet
    df = pd.read_excel(excel_path, sheet_name="卡面描述")
    print(f"📌 读取卡牌数: {len(df)} 张")

    # 处理卡牌数据
    total_count = process_card_sheet(df)

    print(f"\n🎉 所有卡牌笔记已生成完毕，共 {total_count} 张！")


if __name__ == "__main__":
    main()
