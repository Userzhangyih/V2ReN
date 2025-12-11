# config/protocols/trojan.py
"""
Trojan协议解析器
"""
import urllib.parse
from .base import NodeParser
from config.logger import log_error


class TrojanParser(NodeParser):
    """Trojan协议解析器"""
    
    def parse(self, node_url):
        """解析Trojan协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息（fragment）
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # 提取SNI参数，如果没有则使用hostname
            sni = query_params.get('sni', [parsed.hostname])[0]
            type_param = query_params.get('type', ['tcp'])[0]
            
            return self.create_output(
                protocol='Trojan',
                server=parsed.hostname,
                port=parsed.port,
                password=parsed.username,
                sni=sni,
                type=type_param,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"Trojan解析错误: {e}")
            return None