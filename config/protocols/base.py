# config/protocols/base.py
"""
协议解析器基类
"""
import re
import base64
import json
import socket
import urllib.parse

from config.logger import log_info, log_warning, log_error, log_debug


class NodeParser:
    """节点解析器基类"""
    
    def __init__(self):
        self.common_fields = {
            'protocol': '',
            'server': '',
            'port': '',
            'remark': '',
            'original_url': ''
        }
    
    def parse(self, node_url):
        """解析节点URL的通用方法"""
        raise NotImplementedError("子类必须实现此方法")
    
    def create_output(self, **kwargs):
        """创建标准化的输出字典"""
        output = self.common_fields.copy()
        output.update(kwargs)
        return output
    
    @staticmethod
    def add_base64_padding(s):
        """为base64字符串添加padding"""
        if not s:
            return s
        padding = 4 - len(s) % 4
        if padding != 4:
            return s + '=' * padding
        return s
    
    @staticmethod
    def clean_port(port_str):
        """清理端口号"""
        if not port_str:
            return None
        
        # 移除非数字字符
        port_clean = ''.join(filter(str.isdigit, port_str))
        if port_clean and port_clean.isdigit():
            return int(port_clean)
        
        log_warning(f"无效的端口: {port_str}")
        return None