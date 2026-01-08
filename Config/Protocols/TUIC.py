"""
TUIC协议解析器
"""
import urllib.parse
from .Base import NodeParser
from Config.Logger import log_error


class TUICParser(NodeParser):
    """TUIC协议解析器"""
    protocol_name = "tuic"
    
    def parse(self, node_url):
        """解析TUIC协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # TUIC格式: tuic://uuid:password@host:port
            auth_part = parsed.username or ''
            uuid = ''
            password = ''
            
            if ':' in auth_part:
                uuid, password = auth_part.split(':', 1)
            else:
                uuid = auth_part
                password = ''
            
            # 提取查询参数
            sni = query_params.get('sni', [''])[0]
            allow_insecure = query_params.get('allow_insecure', ['0'])[0]
            congestion_control = query_params.get('congestion_control', ['cubic'])[0]
            udp_relay_mode = query_params.get('udp_relay_mode', ['native'])[0]
            alpn = query_params.get('alpn', [''])[0]
            
            return self.create_output(
                protocol='TUIC',
                server=parsed.hostname,
                port=parsed.port,
                uuid=uuid,
                password=password,
                sni=sni,
                allow_insecure=allow_insecure,
                congestion_control=congestion_control,
                udp_relay_mode=udp_relay_mode,
                alpn=alpn,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"TUIC解析错误: {e}")
            return None