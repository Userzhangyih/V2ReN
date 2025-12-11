# V2ray.py
import json
import os
import base64
import subprocess

# 导入配置模块
from config.logger import init_logger, log_info, log_warning, log_error, log_debug
from config.GUI import create_gui
from config.protocols import parse_node, test_node, rewrite_node_with_new_name
from config.Base64 import process_base64_content

def load_country_mappings():
        data = {
                    "country_zh_map": "data/country_zh_map.json",
                    "city_zh_map": "data/city_zh_map.json",
                    "country_flags": "data/country_flags.json"
                }
    
        with open(data["country_zh_map"], "r", encoding="utf-8") as f:
            country_mappings = json.load(f)
        
        with open(data["country_flags"], "r", encoding="utf-8") as f:
            flag_mappings = json.load(f)

        with open(data['city_zh_map'], "r", encoding="utf-8") as f:
            city_mappings = json.load(f)
        
        # 合并所有映射
        mappings = {
            'country_zh_map': country_mappings,
            'country_flags': flag_mappings,
            'city_zh_map': city_mappings
        }
        
        print(f"[配置] 成功加载映射配置")
        print(f"[配置] 国家名称映射数量: {len(country_mappings)}")
        print(f"[配置] 国旗映射数量: {len(flag_mappings)}")
        print(f"[配置] 城市名称映射数量: {len(city_mappings)}")
        
        return mappings

def load_nodes():
    """从Input.txt加载节点"""
    try:
        with open("input/Input.txt", "r", encoding="utf-8") as f:
            content = f.read().strip()
        
        # 使用base64处理函数来处理内容
        nodes = process_base64_content(content)
        return nodes
    except FileNotFoundError:
        log_error("找不到 input/Input.txt 文件")
        return []

def rename_node(node_info, country_mappings):
    """重命名节点"""
    country_code = node_info.get('country_code', '')
    city = node_info.get('city', '')
    protocol = node_info.get('protocol', '')
    
    # 如果无法获取国家代码，使用默认旗帜
    if not country_code:
        return f"🏳️[未知][未知][{protocol}]"
    
    # 获取旗帜和国家中文名称
    flag = country_mappings['country_flags'].get(country_code, '🏳️')
    country_zh = country_mappings['country_zh_map'].get(country_code, country_code)
    
    # 构建新名称
    if city:
        new_name = f"{flag}{country_zh}[{city}][{protocol}]"
    else:
        new_name = f"{flag}{country_zh}[{protocol}]"
    
    return new_name

def main():
    """主函数"""
    log_info("正在启动节点处理工具...")
    
    # 初始化日志记录器
    logger = init_logger("output/log.txt")
    logger.clear_log()
    
    # 记录程序开始
    log_info("程序开始运行")
    
    # 步骤1: 创建GUI并获取输入
    log_info("步骤1: 打开GUI输入节点内容...")
    create_gui()
    
    # 步骤2: 加载配置和节点
    log_info("步骤2: 加载配置和节点...")
    country_mappings = load_country_mappings()
    if not country_mappings:
        log_error("无法加载国家映射配置，程序终止")
        return
    
    # 获取城市映射
    city_mappings = country_mappings.get('city_zh_map', {})
    
    nodes = load_nodes()
    if not nodes:
        log_warning("没有找到节点内容，程序终止")
        return
    
    log_info(f"找到 {len(nodes)} 个节点")
    
    # 步骤3-6: 解析、测试和重命名节点
    processed_nodes = []
    
    for i, node in enumerate(nodes, 1):
        # 记录处理开始
        log_info(f"处理节点 {i}/{len(nodes)}: {node[:50]}...")
        
        # 解析节点
        node_info = parse_node(node)
        if not node_info:
            log_warning("  解析失败，跳过")
            continue
        
        # 测试节点获取位置信息
        log_debug("  测试节点获取位置信息...")
        location_info = test_node(node_info, city_mappings)
        if location_info:
            node_info.update(location_info)
        
        # 重命名节点
        new_name = rename_node(node_info, country_mappings)
        node_info['new_name'] = new_name
        node_info['original_content'] = node
       
        # 将新名称写入节点配置
        rewritten_node = rewrite_node_with_new_name(node, new_name, node_info)
        node_info['rewritten_content'] = rewritten_node
        
        processed_nodes.append(node_info)
        
        log_info(f"  重命名为: {new_name}")
    
    # 步骤7: 保存到输出文件
    log_info("步骤7: 保存处理结果...")
    os.makedirs("output", exist_ok=True)
    
    # 保存可直接导入的订阅文件
    with open("output/Subscription.txt", "w", encoding="utf-8") as f:
        for node_info in processed_nodes:
            f.write(f"{node_info['rewritten_content']}\n")
    
    # 保存详细信息报告
    with open("output/Details.txt", "w", encoding="utf-8") as f:
        f.write("节点处理详情报告\n")
        f.write("=" * 60 + "\n\n")
        
        for i, node_info in enumerate(processed_nodes, 1):
            f.write(f"节点 #{i}\n")
            f.write(f"名称: {node_info['new_name']}\n")
            f.write(f"协议: {node_info.get('protocol', 'Unknown')}\n")
            
            if node_info.get('ip'):
                f.write(f"IP地址: {node_info['ip']}\n")
            
            if node_info.get('city_en'):
                f.write(f"位置: {node_info.get('city', '')} ({node_info.get('city_en', '')})\n")
            
            f.write(f"重写后的节点:\n{node_info['rewritten_content']}\n")
            f.write("-" * 50 + "\n\n")
    
    # 保存Base64编码的订阅文件（标准订阅格式）
    with open("output/Subscription_Base64.txt", "w", encoding="utf-8") as f:
        node_lines = []
        for node_info in processed_nodes:
            node_lines.append(node_info['rewritten_content'])
        
        # 将所有节点连接成一个字符串，然后进行Base64编码
        all_nodes = "\n".join(node_lines)
        encoded_nodes = base64.b64encode(all_nodes.encode('utf-8')).decode('utf-8')
        f.write(encoded_nodes)
    
    log_info(f"成功处理 {len(processed_nodes)} 个节点")
    
    # 输出生成的文件信息
    logger.save_summary("处理完成")
    
    log_info("\n生成的文件:")
    log_info("  - output/Subscription.txt: 可直接复制的节点列表")
    log_info("  - output/Subscription_Base64.txt: Base64编码的订阅链接内容")
    log_info("  - output/Details.txt: 详细处理报告")
    log_info("  - output/log.txt: 运行日志")
    
    # 步骤8: 用默认文本应用打开主要输出文件
    log_info("步骤8: 打开订阅文件...")
    try:
        subprocess.run(['notepad', 'output/Subscription.txt'], check=True)
    except Exception as e:
        log_warning(f"无法自动打开文件，请手动查看 output/Subscription.txt: {str(e)}")
    
    log_info("程序运行结束")

if __name__ == "__main__":
    main()