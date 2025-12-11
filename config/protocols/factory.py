# config/protocols/factory.py
"""
协议工厂模式 - 自动注册和发现协议解析器
"""
import importlib
import os
import sys
from pathlib import Path
from config.logger import log_info, log_error, log_debug
from .base import NodeParser


class ProtocolFactory:
    """协议工厂 - 自动发现和加载协议解析器"""
    
    def __init__(self, protocols_dir=None):
        self.protocols_dir = protocols_dir or Path(__file__).parent
        self.protocols = {}
        self.load_protocols()
    
    def load_protocols(self):
        """动态加载所有协议解析器"""
        try:
            # 获取当前目录下的所有.py文件（除了特定文件）
            for file_path in self.protocols_dir.glob("*.py"):
                file_name = file_path.stem
                
                # 跳过特定的文件
                if file_name in ['__init__', 'base', 'manager', 'factory']:
                    continue
                
                # 尝试导入模块
                try:
                    module_name = f"config.protocols.{file_name}"
                    module = importlib.import_module(module_name)
                    
                    # 查找协议解析器类
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        
                        # 检查是否是协议解析器类
                        if (isinstance(attr, type) and 
                            issubclass(attr, NodeParser) and
                            attr.__name__ != 'NodeParser'):
                            
                            # 获取协议类型（从类名推断，如 VMessParser -> vmess）
                            protocol_type = attr.__name__.replace('Parser', '').lower()
                            self.protocols[protocol_type] = attr()
                            log_info(f"加载协议解析器: {protocol_type} -> {attr.__name__}")
                    
                except ImportError as e:
                    log_error(f"导入协议模块失败 {file_name}: {e}")
                except Exception as e:
                    log_error(f"加载协议解析器失败 {file_name}: {e}")
            
            log_info(f"共加载 {len(self.protocols)} 个协议解析器")
        
        except Exception as e:
            log_error(f"加载协议时发生错误: {e}")
    
    def get_parser(self, protocol_type):
        """获取协议解析器"""
        return self.protocols.get(protocol_type.lower())
    
    def register_parser(self, protocol_type, parser_class):
        """手动注册协议解析器"""
        self.protocols[protocol_type.lower()] = parser_class()
        log_info(f"手动注册协议解析器: {protocol_type}")
    
    def get_all_protocols(self):
        """获取所有支持的协议"""
        return list(self.protocols.keys())
    
    def get_parser_for_url(self, node_url):
        """根据URL获取对应的解析器"""
        for protocol_type, parser in self.protocols.items():
            if node_url.startswith(f"{protocol_type}://"):
                return parser
        return None