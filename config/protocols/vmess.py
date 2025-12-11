# config/protocols/vmess.py
"""
VMess协议解析器
"""
import base64
import json
from .base import NodeParser
from config.logger import log_error


class VMessParser(NodeParser):
    """VMess协议解析器"""
    
    def parse(self, node_url):
        """解析VMess协议节点"""
        try:
            # 移除vmess://前缀
            encoded_content = node_url[8:]
            
            # 添加padding并解码
            padding = 4 - len(encoded_content) % 4
            if padding != 4:
                encoded_content += '=' * padding
            
            decoded_bytes = base64.b64decode(encoded_content)
            config = json.loads(decoded_bytes)
            
            return self.create_output(
                protocol='VMess',
                server=config.get('add', ''),
                port=config.get('port', ''),
                id=config.get('id', ''),
                alterId=config.get('aid', ''),
                network=config.get('net', ''),
                type=config.get('type', ''),
                host=config.get('host', ''),
                path=config.get('path', ''),
                tls=config.get('tls', ''),
                remark=config.get('ps', ''),
                original_url=node_url
            )
        except Exception as e:
            log_error(f"VMess解析错误: {e}")
            return None