"""
ClashMeta协议解析器
"""
import base64
import json
from .Base import NodeParser
from Config.Logger import log_error


class ClashMetaParser(NodeParser):
    """ClashMeta协议解析器"""
    protocol_name = "clashmeta"
    
    def parse(self, node_url):
        """解析ClashMeta协议节点"""
        try:
            # 移除clashmeta://前缀
            encoded_content = node_url[12:]
            
            # 添加padding并解码
            padding = 4 - len(encoded_content) % 4
            if padding != 4:
                encoded_content += '=' * padding
            
            decoded_bytes = base64.b64decode(encoded_content)
            config = json.loads(decoded_bytes)
            
            # ClashMeta配置格式
            return self.create_output(
                protocol='ClashMeta',
                server=config.get('server', ''),
                port=config.get('port', ''),
                type=config.get('type', ''),
                password=config.get('password', ''),
                method=config.get('cipher', ''),
                uuid=config.get('uuid', ''),
                alterId=config.get('alterId', ''),
                network=config.get('network', ''),
                tls=config.get('tls', False),
                sni=config.get('sni', ''),
                remark=config.get('name', ''),
                original_url=node_url
            )
        except Exception as e:
            log_error(f"ClashMeta解析错误: {e}")
            return None