"""
Juicity协议解析器
"""
import urllib.parse
from .Base import NodeParser
from Config.Logger import log_error


class JuicityParser(NodeParser):
    """Juicity协议解析器"""
    protocol_name = "juicity"
    
    def parse(self, node_url):
        """解析Juicity协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # 提取查询参数
            sni = query_params.get('sni', [''])[0]
            allow_insecure = query_params.get('allowInsecure', ['0'])[0]
            congestion_control = query_params.get('congestion_control', ['bbr'])[0]
            alpn = query_params.get('alpn', [''])[0]
            
            # Juicity使用username作为UUID
            uuid = parsed.username or ''
            
            return self.create_output(
                protocol='Juicity',
                server=parsed.hostname,
                port=parsed.port,
                uuid=uuid,
                sni=sni,
                allow_insecure=allow_insecure,
                congestion_control=congestion_control,
                alpn=alpn,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"Juicity解析错误: {e}")
            return None