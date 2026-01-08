"""
Trojan协议解析器
"""
import urllib.parse
from .Base import NodeParser
from Config.Logger import log_error


class TrojanParser(NodeParser):
    """Trojan协议解析器"""
    protocol_name = "trojan"
    
    def parse(self, node_url):
        """解析Trojan协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # Trojan格式: trojan://password@host:port
            password = parsed.password or ''
            
            # 提取查询参数
            sni = query_params.get('sni', [''])[0]
            allow_insecure = query_params.get('allowInsecure', ['0'])[0]
            peer = query_params.get('peer', [''])[0]
            flow = query_params.get('flow', [''])[0]
            
            return self.create_output(
                protocol='Trojan',
                server=parsed.hostname,
                port=parsed.port,
                password=password,
                sni=sni if sni else peer,
                allow_insecure=allow_insecure,
                flow=flow,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"Trojan解析错误: {e}")
            return None