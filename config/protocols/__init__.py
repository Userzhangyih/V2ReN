# config/protocols/__init__.py
"""
协议模块入口文件
"""
from .base import NodeParser
from .manager import ProtocolManager
from .factory import ProtocolFactory

# 创建全局管理器实例
protocol_manager = ProtocolManager()
protocol_factory = ProtocolFactory()

# 导出的函数接口
parse_nodes_from_content = protocol_manager.parse_nodes_from_content
parse_node = protocol_manager.parse_node
test_node = protocol_manager.test_node
rewrite_node_with_new_name = protocol_manager.rewrite_node_with_new_name

# 导出工具函数
from .manager import (
    get_ip_from_hostname,
    get_location_from_ip,
    is_likely_base64
)

# 导出所有支持的协议
__all__ = [
    'NodeParser',
    'ProtocolManager',
    'ProtocolFactory',
    'protocol_manager',
    'protocol_factory',
    'parse_nodes_from_content',
    'parse_node',
    'test_node',
    'rewrite_node_with_new_name',
    'get_ip_from_hostname',
    'get_location_from_ip',
    'is_likely_base64'
]