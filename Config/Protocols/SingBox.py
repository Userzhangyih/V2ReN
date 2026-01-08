"""
SingBox协议解析器
"""
import base64
import json
from .Base import NodeParser
from Config.Logger import log_error


class SingBoxParser(NodeParser):
    """SingBox协议解析器"""
    protocol_name = "singbox"
    
    def parse(self, node_url):
        """解析SingBox协议节点"""
        try:
            # 移除singbox://前缀
            encoded_content = node_url[10:]
            
            # SingBox配置通常是base64编码的JSON
            padding = 4 - len(encoded_content) % 4
            if padding != 4:
                encoded_content += '=' * padding
            
            decoded_bytes = base64.b64decode(encoded_content)
            config = json.loads(decoded_bytes)
            
            # SingBox配置格式
            return self.create_output(
                protocol='SingBox',
                server=config.get('server', ''),
                port=config.get('port', ''),
                type=config.get('type', ''),
                uuid=config.get('uuid', ''),
                password=config.get('password', ''),
                method=config.get('method', ''),
                tls=config.get('tls', False),
                sni=config.get('sni', ''),
                remark=config.get('name', ''),
                original_url=node_url
            )
        except Exception as e:
            log_error(f"SingBox解析错误: {e}")
            return None