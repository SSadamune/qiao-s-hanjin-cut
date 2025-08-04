"""
主程序，负责加载 Excel 文件、缓存君主武将名、处理每个工作表并生成笔记。
"""

import os
from openpyxl import load_workbook
from domain.heroes.constants import EXCEL_PATH, OUTPUT_DIR, TARGET_SHEETS
from domain.heroes.heroes_cache import scan_all_heroes
from domain.heroes.sheet_processor import process_sheet


def main():
    """主函数，负责加载 Excel 文件、缓存君主武将名、处理每个工作表并生成笔记"""
    print(f"📖 加载 Excel: {EXCEL_PATH}")
    wb = load_workbook(EXCEL_PATH)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 缓存所有武将信息
    all_heroes = scan_all_heroes(wb, TARGET_SHEETS)
    print(f"📌 缓存武将数: {len(all_heroes)} 个")

    total_count = 0
    for sheet_name in TARGET_SHEETS:
        print(f"\n🔄 解析 Sheet: {sheet_name}")
        ws = wb[sheet_name]
        total_count += process_sheet(ws, sheet_name, all_heroes)

    print(f"\n🎉 所有武将笔记已生成完毕，共 {total_count} 条！")


if __name__ == "__main__":
    main()
