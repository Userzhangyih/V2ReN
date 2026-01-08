"""
Hysteria2协议解析器
"""
import urllib.parse
from .Base import NodeParser
from Config.Logger import log_error


class Hysteria2Parser(NodeParser):
    """Hysteria2协议解析器"""
    protocol_name = "hysteria2"
    
    def parse(self, node_url):
        """解析Hysteria2协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # 提取查询参数
            sni = query_params.get('sni', [''])[0]
            obfs = query_params.get('obfs', [''])[0]
            obfs_password = query_params.get('obfs-password', [''])[0]
            insecure = query_params.get('insecure', [''])[0]
            alpn = query_params.get('alpn', [''])[0]
            
            # Hysteria2使用username作为密码
            password = parsed.username or ''
            
            return self.create_output(
                protocol='Hysteria2',
                server=parsed.hostname or '',
                port=parsed.port or 443,
                password=password,
                sni=sni,
                obfs=obfs,
                obfs_password=obfs_password,
                insecure=insecure,
                alpn=alpn,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"Hysteria2解析错误: {e}")
            return None