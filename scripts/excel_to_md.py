import os
from openpyxl import load_workbook
from constants import EXCEL_PATH, OUTPUT_DIR, TARGET_SHEETS
from monarch_cache import scan_all_monarch_names
from sheet_processor import process_sheet

def main():
    print(f"📖 加载 Excel: {EXCEL_PATH}")
    wb = load_workbook(EXCEL_PATH)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 缓存君主武将名
    monarch_names = scan_all_monarch_names(wb, TARGET_SHEETS)
    print(f"📌 缓存君主武将名: {len(monarch_names)} 个")

    total_count = 0
    for sheet_name in TARGET_SHEETS:
        print(f"\n🔄 解析 Sheet: {sheet_name}")
        ws = wb[sheet_name]
        total_count += process_sheet(ws, sheet_name, monarch_names)

    print(f"\n🎉 所有武将笔记已生成完毕，共 {total_count} 条！")

if __name__ == "__main__":
    main()
