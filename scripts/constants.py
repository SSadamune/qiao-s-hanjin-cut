# constants.py

import os

# Vault 路径
VAULT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXCEL_PATH = os.path.join(VAULT_PATH, "resources", "乔剪国战表格.xlsx")
OUTPUT_DIR = os.path.join(VAULT_PATH, "notes", "武将")

# Sheet 名称
TARGET_SHEETS = [
    "官方范围",
    "兵情篇",
    "豪门贵胄",
    "异军突起",
    "小型扩展",
    "他山之玉"
]

# 体力值映射
HP_MAP = {"696": 1.5, "6969": 2.0, "69696": 2.5}

# 跳过编号前缀
SKIP_PREFIXES = ("黑桃", "梅花", "红桃", "方片", "EMA", "Z.")

# 势力前缀映射
FORCE_MAP = {
    "HAN": "汉",
    "WEI": "魏",
    "SHU": "蜀",
    "WU": "吴",
    "QUN": "群",
    "JIN": "晋"
}

# 武将类型顺序
TYPE_ORDER = ["君主", "野心家", "叛首", "叛谍", "客将", "隐士", "可君主升变"]

# Excel 列常量
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

# 前6列（用于颜色分析）
FIRST_6_COLS = [COL_PACKAGE, COL_CODE, COL_NAME, COL_TITLE, COL_HP, COL_SYNERGY]

# 颜色映射
COLOR_MEANINGS = {
    "FFFFEEAD": "汉",
    "FFC5CAD3": "群",
    "FFC7DCFF": "魏",
    "FFF2C7FF": "晋",
    "FFFFC9C7": "蜀",
    "FFC3EAD5": "吴",
    "FFFFE270": "君主",
    "FF5E2281": "野心家",
    "FFF3F5F7": "隐士"
}

# 允许正常识别的颜色集合
KNOWN_COLORS = set(COLOR_MEANINGS.keys())

# 在解析时忽略的分包名
IGNORED_PACKAGES = {"隐世", "妙仙"}