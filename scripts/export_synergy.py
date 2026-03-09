"""
导出珠联璧合关系到 CSV 文件。
从已生成的 Markdown 文件中读取珠联璧合关系。
每行记录一个武将及其所有与之珠联璧合的武将，避免重复记录关系。
"""

import os
import re
import csv
from domain.heroes.parsers import parse_factions_from_code


def parse_yaml_simple(yaml_content):
    """
    简单解析 YAML front matter，提取键值对。
    """
    data = {}
    for line in yaml_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key == 'tags' or key == 'aliases':
                # 列表类型，跳过（我们不需要）
                continue
            data[key] = value
    return data


def parse_markdown_file(file_path):
    """
    解析 Markdown 文件，提取武将信息和珠联璧合关系。
    返回字典：{
        'code': 编号,
        'name': 姓名,
        'title': 称号（可选）,
        'synergy_links': [链接列表，格式为 '编号 姓名']
    }
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分离 YAML front matter 和 body
    parts = content.split('---', 2)
    if len(parts) < 3:
        return None
    
    yaml_content = parts[1].strip()
    body_content = parts[2]
    
    # 解析 YAML
    data = parse_yaml_simple(yaml_content)
    
    if not data or '编号' not in data or '姓名' not in data:
        return None
    
    code = data['编号']
    name = data['姓名']
    title = data.get('称号', '')
    
    # 跳过君主武将
    parsed = parse_factions_from_code(code)
    if "君主" in parsed["types"]:
        return None
    
    # 从 body 中提取珠联璧合链接
    synergy_links = []
    synergy_pattern = r'\*\*珠联璧合\*\*:\s*(.+?)\s*\n'
    match = re.search(synergy_pattern, body_content)
    
    if match:
        synergy_text = match.group(1)
        # 提取所有 [[编号 姓名]] 格式的链接
        link_pattern = r'\[\[([^\]]+)\]\]'
        links = re.findall(link_pattern, synergy_text)
        synergy_links = [link.strip() for link in links if link.strip()]
    
    return {
        'code': code,
        'name': name,
        'title': title,
        'synergy_links': synergy_links
    }


def scan_markdown_files(notes_dir):
    """
    扫描 notes/武将/ 目录下的所有 Markdown 文件。
    返回武将信息列表。
    """
    heroes = []
    
    if not os.path.exists(notes_dir):
        print(f"错误: 目录不存在: {notes_dir}")
        return heroes
    
    for filename in os.listdir(notes_dir):
        if not filename.endswith('.md'):
            continue
        
        file_path = os.path.join(notes_dir, filename)
        hero_info = parse_markdown_file(file_path)
        
        if hero_info:
            heroes.append(hero_info)
    
    return heroes


def get_display_name(code, name):
    """
    根据编号和姓名生成显示名称。
    规则：
    - AM 开头的：野{姓名}
    - SHU004 诸葛亮：丞相诸葛亮
    - SHU011 诸葛亮：卧龙诸葛亮
    - JIN009 司马懿：晋司马懿
    - WEI002 司马懿：魏司马懿
    - 袁谭_袁尚_袁熙：三次袁
    - 姜叙_赵衢_尹奉_梁宽：天水四侠
    - 其他：直接使用姓名
    """
    # 处理特殊组合武将
    if name == '袁谭_袁尚_袁熙':
        return '三次袁'
    if name == '姜叙_赵衢_尹奉_梁宽':
        return '天水四侠'
    
    # 处理野心家版本
    if code.startswith('AM('):
        return f"野{name}"
    
    # 处理两个版本的诸葛亮
    if code == 'SHU004' and name == '诸葛亮':
        return '丞相诸葛亮'
    if code == 'SHU011' and name == '诸葛亮':
        return '卧龙诸葛亮'
    
    # 处理两个版本的司马懿
    if code == 'JIN009' and name == '司马懿':
        return '晋司马懿'
    if code == 'WEI002' and name == '司马懿':
        return '魏司马懿'
    
    # 其他情况直接使用姓名
    return name


def build_synergy_relationships(heroes):
    """
    构建珠联璧合关系图。
    返回两个字典：
    1. synergy_map: {武将标识: set(与之珠联璧合的武将标识列表)}
    2. display_name_map: {武将标识: 显示名称}
    武将标识格式：编号 姓名（用于区分不同的诸葛亮）
    """
    synergy_map = {}
    display_name_map = {}
    
    # 建立武将索引：编号 姓名 -> 武将信息
    hero_index = {}
    for hero in heroes:
        hero_key = f"{hero['code']} {hero['name']}"
        hero_index[hero_key] = hero
        if hero_key not in synergy_map:
            synergy_map[hero_key] = set()
        # 建立显示名称映射
        display_name_map[hero_key] = get_display_name(hero['code'], hero['name'])
    
    # 构建关系图
    for hero in heroes:
        hero_key = f"{hero['code']} {hero['name']}"
        
        # 处理该武将的珠联璧合链接
        for link in hero['synergy_links']:
            # link 格式是 "编号 姓名"
            if link in hero_index:
                target_hero = hero_index[link]
                target_key = f"{target_hero['code']} {target_hero['name']}"
                
                # 跳过自己
                if target_key != hero_key:
                    synergy_map[hero_key].add(target_key)
    
    return synergy_map, display_name_map


def export_synergy_to_csv(synergy_map, display_name_map, output_path):
    """
    导出珠联璧合关系到 CSV 文件。
    每行记录一个武将及其所有与之珠联璧合的武将（使用显示名称）。
    如果 A-B 已经在之前的行中记录过，后续行就不再记录 B-A。
    """
    # 记录已经处理过的关系对（避免重复）
    processed_pairs = set()
    
    # 按武将标识排序，确保输出顺序一致
    sorted_heroes = sorted(synergy_map.keys())
    
    # 先收集所有数据，确定最大列数
    rows_data = []
    max_cols = 1  # 至少需要1列（武将名）
    
    for hero_key in sorted_heroes:
        synergy_set = synergy_map[hero_key]
        
        # 过滤掉已经在之前行中记录过的关系
        # 例如：如果 A-B 已经在第一行记录过，那么 B 这一行就不需要再记录 A
        filtered_synergy = []
        for syn_key in sorted(synergy_set):
            # 检查这个关系是否已经在之前的行中记录过
            pair_key = tuple(sorted([hero_key, syn_key]))
            if pair_key not in processed_pairs:
                filtered_synergy.append(syn_key)
                processed_pairs.add(pair_key)
        
        # 如果该武将有珠联璧合关系，才记录
        if filtered_synergy:
            # 转换为显示名称
            hero_display_name = display_name_map[hero_key]
            synergy_display_names = [display_name_map[syn_key] for syn_key in filtered_synergy]
            rows_data.append([hero_display_name] + synergy_display_names)
            max_cols = max(max_cols, len(filtered_synergy) + 1)
    
    # 如果文件已存在，先删除
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except PermissionError:
            print(f"警告: 无法删除旧文件，可能正在被其他程序打开。请关闭文件后重试。")
            return
    
    # 写入 CSV 文件
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        
        # 直接写入数据（不写入表头）
        for row_data in rows_data:
            # 确保每行的列数一致，不足的用空字符串填充
            row = row_data + [''] * (max_cols - len(row_data))
            writer.writerow(row)
    
    print(f"珠联璧合关系已导出到: {output_path}")
    print(f"共记录了 {len(rows_data)} 个武将的珠联璧合关系")


def main():
    """主函数"""
    # 确定路径
    vault_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    notes_dir = os.path.join(vault_path, "notes", "武将")
    output_dir = os.path.join(vault_path, "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "珠联璧合关系.csv")
    
    # 扫描 Markdown 文件
    print(f"扫描 Markdown 文件目录: {notes_dir}")
    heroes = scan_markdown_files(notes_dir)
    print(f"共扫描到 {len(heroes)} 个武将")
    
    # 构建珠联璧合关系图
    print("构建珠联璧合关系图...")
    synergy_map, display_name_map = build_synergy_relationships(heroes)
    
    # 统计关系数量
    total_relationships = sum(len(synergy_set) for synergy_set in synergy_map.values())
    print(f"共发现 {total_relationships} 条珠联璧合关系")
    
    # 导出到 CSV
    print("导出到 CSV...")
    export_synergy_to_csv(synergy_map, display_name_map, output_path)
    
    print("\n导出完成！")


if __name__ == "__main__":
    main()
