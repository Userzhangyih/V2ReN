"""
协议管理器 - 动态加载和管理所有协议解析器
"""
import os
import importlib
import inspect
from pathlib import Path
from Config.Logger import log_info, log_error, log_debug
from .ProtocolAliases import get_protocol_by_alias, is_valid_alias


class ProtocolManager:
    """协议管理器，负责动态加载协议解析器"""
    
    def __init__(self):
        self.parsers = {}  # 协议名 -> 解析器实例
        self.load_all_parsers()
    
    def load_all_parsers(self):
        """动态加载所有协议解析器"""
        protocols_dir = Path(__file__).parent  # protocols目录
        
        # 排除的文件
        exclude_files = {
            'Base.py', '__init__.py', 'ProtocolManager.py', 
            'NodeTester.py', 'NodeRewriter.py', 'ProtocolAliases.py'
        }
        
        # 扫描所有.py文件
        for file_path in protocols_dir.glob("*.py"):
            if file_path.name in exclude_files:
                continue
            
            try:
                # 动态导入模块
                module_name = file_path.stem
                module_path = f"Config.Protocols.{module_name}"
                
                # 导入模块
                module = importlib.import_module(module_path)
                
                # 查找所有继承自NodeParser的类
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, self._get_base_parser_class()) and 
                        obj is not self._get_base_parser_class() and
                        hasattr(obj, 'protocol_name')):
                        
                        # 创建解析器实例
                        parser_instance = obj()
                        protocol_name = parser_instance.protocol_name
                        
                        if protocol_name:
                            self.parsers[protocol_name] = parser_instance
                            log_info(f"加载协议解析器: {protocol_name} ({obj.__name__})")
                        else:
                            log_error(f"解析器 {obj.__name__} 没有定义 protocol_name")
                
            except ImportError as e:
                log_error(f"导入模块失败 {file_path.name}: {e}")
            except Exception as e:
                log_error(f"加载解析器失败 {file_path.name}: {e}")
        
        log_info(f"共加载 {len(self.parsers)} 个协议解析器")
    
    def _get_base_parser_class(self):
        """获取基类NodeParser"""
        from .Base import NodeParser
        return NodeParser
    
    def get_parser(self, protocol_name):
        """获取指定协议的解析器"""
        # 尝试直接获取
        parser = self.parsers.get(protocol_name.lower())
        
        # 如果直接获取失败，尝试通过别名获取
        if not parser:
            normalized_protocol = get_protocol_by_alias(protocol_name)
            parser = self.parsers.get(normalized_protocol.lower())
        
        return parser
    
    def get_parser_for_url(self, node_url):
        """根据URL获取对应的解析器"""
        if not node_url or '://' not in node_url:
            return None
        
        # 提取协议部分
        protocol = node_url.split('://')[0].lower()
        
        # 尝试直接获取
        parser = self.parsers.get(protocol)
        if parser:
            return parser
        
        # 尝试通过别名获取
        normalized_protocol = get_protocol_by_alias(protocol)
        return self.parsers.get(normalized_protocol)
    
    def parse_node(self, node_url):
        """解析节点URL"""
        parser = self.get_parser_for_url(node_url)
        if parser:
            result = parser.parse(node_url)
            if result:
                log_debug(f"成功解析 {parser.protocol_name} 节点")
            else:
                log_error(f"解析 {parser.protocol_name} 节点失败")
            return result
        else:
            protocol = node_url.split('://')[0] if '://' in node_url else '未知'
            log_error(f"不支持此协议: {protocol}")
            return None
    
    def get_supported_protocols(self):
        """获取支持的协议列表（包括别名）"""
        supported = list(self.parsers.keys())
        
        # 添加协议友好名称
        from . import get_protocol_friendly_name
        friendly_list = []
        for protocol in supported:
            friendly_name = get_protocol_friendly_name(protocol)
            if friendly_name != protocol:
                friendly_list.append(f"{protocol} ({friendly_name})")
            else:
                friendly_list.append(protocol)
        
        return friendly_list
    
    def get_all_parsers(self):
        """获取所有解析器"""
        return self.parsers
    
    def add_parser(self, parser_instance):
        """手动添加解析器（用于动态扩展）"""
        if hasattr(parser_instance, 'protocol_name') and parser_instance.protocol_name:
            self.parsers[parser_instance.protocol_name] = parser_instance
            log_info(f"手动添加协议解析器: {parser_instance.protocol_name}")
        else:
            log_error("解析器必须定义 protocol_name 属性")
    
    def remove_parser(self, protocol_name):
        """移除协议解析器"""
        if protocol_name in self.parsers:
            del self.parsers[protocol_name]
            log_info(f"移除协议解析器: {protocol_name}")
            return True
        return False
    
    def has_parser(self, protocol_name):
        """检查是否有指定协议的解析器"""
        return protocol_name in self.parsers or get_protocol_by_alias(protocol_name) in self.parsers