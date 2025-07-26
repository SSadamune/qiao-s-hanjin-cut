# 乔剪汉晋国战资料库

本项目用于管理 **乔剪汉晋国战** 的武将、卡牌、规则等信息，
通过 Python 脚本从 Excel 批量生成 Markdown 笔记，
并在 **Obsidian** 中查看和管理。

## 📂 项目结构

```
resources/乔剪国战表格.xlsx   # 武将数据源 Excel
notes/武将/                   # 脚本自动生成的武将笔记
scripts/hero_generator.py     # Excel → Markdown 转换脚本
```

## 🏗 在 Obsidian 中使用

1. 安装 [Obsidian](https://obsidian.md/)
2. 将此项目根目录添加为 Obsidian 的 Vault
3. 在 `notes/武将/` 中浏览、搜索武将笔记

## 🐍 使用 Python 脚本

### 安装依赖

```bash
pip install openpyxl zhconv
```

> 如果 `zhconv` 安装失败，可使用 `opencc-python-reimplemented` 替代。

### 运行脚本

以导入武将为例

```bash
python scripts/hero_generator.py
```

脚本会读取《乔剪国战表格.xlsx》，生成或覆盖 `notes/武将/` 下的笔记。

如发生下列错误，只需用 Excel 打开上述文件，另存为同名文件即可。

```bash
TypeError: Fill() takes no arguments
```

## ✅ 总结

- 在 Obsidian 中打开项目即可查看所有笔记
- 运行 `excel_to_md.py` 自动同步 Excel 数据到 Markdown
- Excel 更新后可随时重新运行脚本覆盖生成
