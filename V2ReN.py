# V2ReN.py - 完整修复版本
import json
import os
import base64
import subprocess

# 导入配置模块
from Config.Logger import init_logger, log_info, log_warning, log_error, log_debug
from Config.GUI import create_gui
from Config.Base64 import process_base64_content

# 从Protocols导入插件化接口
from Config.Protocols import parse_node, test_node, rewrite_node_with_new_name, get_supported_protocols, get_protocol_friendly_name

def load_country_mappings():
    """加载国家、城市和旗帜映射 - 修复版，支持国家单独文件"""
    data = {
        "country_map": "Data/Country_Map.json",
        "country_flags": "Data/Country_Flag.json",
        "city_map_dir": "Data/City_Map"
    }
    
    # 检查文件是否存在
    for key, path in data.items():
        if key != "city_map_dir" and not os.path.exists(path):
            log_error(f"映射文件不存在: {path}")
            return None
    
    try:
        # 加载国家名称映射
        with open(data["country_map"], "r", encoding="utf-8") as f:
            country_mappings = json.load(f)
        
        # 加载旗帜映射
        with open(data["country_flags"], "r", encoding="utf-8") as f:
            flag_mappings = json.load(f)
        
        # 加载城市映射 - 根据您的文件结构：每个国家一个JSON文件
        city_mappings = {}
        city_map_dir = data["city_map_dir"]
        
        if os.path.isdir(city_map_dir):
            # 统计加载的文件数
            loaded_files = 0
            total_files = 0
            
            # 递归查找所有JSON文件
            for root, dirs, files in os.walk(city_map_dir):
                for file in files:
                    if file.endswith('.json'):
                        total_files += 1
                        file_path = os.path.join(root, file)
                        
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                city_data = json.load(f)
                                
                                if isinstance(city_data, dict):
                                    # 合并城市映射
                                    city_mappings.update(city_data)
                                    loaded_files += 1
                                else:
                                    log_warning(f"城市映射文件格式不正确: {file_path}")
                                    
                        except json.JSONDecodeError as e:
                            log_warning(f"JSON解析错误 {file_path}: {e}")
                        except Exception as e:
                            log_warning(f"加载城市映射文件 {file_path} 失败: {str(e)}")
            
            log_debug(f"从 {loaded_files}/{total_files} 个文件中成功加载城市映射")
        else:
            log_warning(f"城市映射目录不存在: {city_map_dir}")
        
        # 创建映射对象
        mappings = {
            'country_map': country_mappings,        # 国家代码 -> 中文名称
            'country_flags': flag_mappings,         # 国家代码 -> 旗帜
            'city_map': city_mappings               # 城市英文名 -> 城市中文名
        }
        
        # 打印统计信息
        log_info(f"[配置] 成功加载映射配置")
        log_info(f"  国家映射: {len(country_mappings)} 条")
        log_info(f"  旗帜映射: {len(flag_mappings)} 条")
        log_info(f"  城市映射: {len(city_mappings)} 条")
        
        # 显示一些示例数据
        if city_mappings:
            sample_cities = list(city_mappings.items())[:3]
            log_debug(f"城市映射示例: {sample_cities}")
        else:
            log_warning("城市映射数据为空")
            
        if country_mappings:
            sample_countries = list(country_mappings.items())[:3]
            log_debug(f"国家映射示例: {sample_countries}")
        
        return mappings
        
    except Exception as e:
        log_error(f"加载映射配置失败: {str(e)}")
        import traceback
        log_error(f"详细错误: {traceback.format_exc()}")
        return None

def load_nodes():
    """从Input.txt加载节点"""
    try:
        with open("Input/Input.txt", "r", encoding="utf-8") as f:
            content = f.read().strip()
        
        # 使用base64处理函数来处理内容
        nodes = process_base64_content(content)
        return nodes
    except FileNotFoundError:
        log_error("找不到 Input/Input.txt 文件")
        return []



# 修改rename_node函数
def rename_node(node_info, country_mappings):
    """重命名节点"""
    country_code = node_info.get('country_code', '')
    city = node_info.get('city', '')
    protocol = node_info.get('protocol', '')
    
    # 获取协议友好名称
    friendly_protocol = get_protocol_friendly_name(protocol)
    
    # 如果无法获取国家代码，使用默认旗帜
    if not country_code:
        return f"🏳️[未知][未知][{friendly_protocol}]"
    
    # 获取旗帜和国家中文名称
    flag = country_mappings['country_flags'].get(country_code, '🏳️')
    country_zh = country_mappings['country_map'].get(country_code, country_code)
    
    # 如果城市为空，尝试从节点信息中获取
    if not city:
        city = node_info.get('city_en', '')
    
    # 构建新名称
    if city:
        # 尝试从城市映射中获取中文城市名
        city_zh = country_mappings['city_map'].get(city, city)
        new_name = f"{flag}{country_zh}[{city_zh}][{friendly_protocol}]"
    else:
        new_name = f"{flag}{country_zh}[{friendly_protocol}]"
    
    return new_name

def check_directories():
    """检查必要的目录是否存在"""
    required_dirs = [
        "Input",
        "Output",
        "Data",
        "Data/City_Map",
        "Data/Database"
    ]
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            log_warning(f"目录不存在: {dir_path}")
            try:
                os.makedirs(dir_path, exist_ok=True)
                log_info(f"已创建目录: {dir_path}")
            except Exception as e:
                log_error(f"无法创建目录 {dir_path}: {str(e)}")

def main():
    """主函数"""
    log_info("正在启动节点处理工具...")
    
    # 检查目录
    check_directories()
    
    # 初始化日志记录器
    logger = init_logger("Output/log.txt", console_output=True, log_level="INFO")
    logger.clear_log()
    
    # 记录程序开始
    log_info("程序开始运行")
    
    # # 显示支持的协议
    # supported_protocols = get_supported_protocols()
    # log_info(f"支持的协议: {', '.join(supported_protocols)}")
    
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
    city_mappings = country_mappings.get('city_map', {})
    
    nodes = load_nodes()
    if not nodes:
        log_warning("没有找到节点内容，程序终止")
        return
    
    log_info(f"找到 {len(nodes)} 个节点")
    
    # 步骤3-6: 解析、测试和重命名节点
    processed_nodes = []
    
    for index, node in enumerate(nodes, 1):
        node_preview = node[:50] + "..." if len(node) > 50 else node
        log_info(' ')
        log_info(f"处理节点 {index}/{len(nodes)}: {node_preview}")
        
        # 解析节点 - 使用插件化接口
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
        
        log_info(f"重命名为: {new_name} ")
    
    # 步骤7: 保存到输出文件
    log_info(" ")
    log_info("步骤7: 保存处理结果...")
    os.makedirs("output", exist_ok=True)
    
    # 保存可直接导入的订阅文件
    with open("Output/Subscription.txt", "w", encoding="utf-8") as f:
        for node_info in processed_nodes:
            f.write(f"{node_info['rewritten_content']}\n")

    with open("Output/NewName.txt", "w", encoding="utf-8") as f:
        for node_info in processed_nodes:
            f.write(f"{node_info['new_name']}\n")
    
    # 保存详细信息报告
    with open("Output/Details.txt", "w", encoding="utf-8") as f:
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
    with open("Output/Subscription_Base64.txt", "w", encoding="utf-8") as f:
        node_lines = []
        for node_info in processed_nodes:
            node_lines.append(node_info['rewritten_content'])
        
        # 将所有节点连接成一个字符串，然后进行Base64编码
        all_nodes = "\n".join(node_lines)
        encoded_nodes = base64.b64encode(all_nodes.encode('utf-8')).decode('utf-8')
        f.write(encoded_nodes)
    
    log_info("=" * 60)
    log_info(f"成功处理: {len(processed_nodes)} 个节点")
    log_info("生成的文件:")
    log_info("Output/Subscription.txt: 可直接复制的节点列表")
    log_info("Output/Subscription_Base64.txt: Base64编码的订阅链接内容")
    log_info("Output/Details.txt: 详细处理报告")
    log_info("Output/log.txt: 运行日志")
    log_info("=" * 60)

    log_info("步骤8: 打开订阅文件...")
  
    subprocess.run(['notepad', 'Output/Subscription.txt'], check=True)

    # 直接添加处理完成的日志
    log_info("程序运行结束")


if __name__ == "__main__":
    main()