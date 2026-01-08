"""
Mieru协议解析器
"""
import urllib.parse
from .Base import NodeParser
from Config.Logger import log_error


class MieruParser(NodeParser):
    """Mieru协议解析器"""
    protocol_name = "mieru"
    
    def parse(self, node_url):
        """解析Mieru协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # 提取密码
            password = parsed.password or ''
            username = parsed.username or ''
            
            # 提取查询参数
            cipher = query_params.get('cipher', ['aes-128-gcm'])[0]
            tls = query_params.get('tls', ['false'])[0].lower() == 'true'
            sni = query_params.get('sni', [''])[0]
            alpn = query_params.get('alpn', [''])[0]
            
            return self.create_output(
                protocol='Mieru',
                server=parsed.hostname,
                port=parsed.port,
                username=username,
                password=password,
                cipher=cipher,
                tls=tls,
                sni=sni,
                alpn=alpn,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"Mieru解析错误: {e}")
            return None