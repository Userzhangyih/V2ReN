# config/protocols/hysteria2.py
"""
Hysteria2协议解析器
"""
import urllib.parse
from .base import NodeParser
from config.logger import log_error


class Hysteria2Parser(NodeParser):
    """Hysteria2协议解析器"""
    
    def parse(self, node_url):
        """解析Hysteria2协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息（fragment）
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # 提取查询参数
            sni = query_params.get('sni', [''])[0]
            obfs = query_params.get('obfs', [''])[0]
            obfs_password = query_params.get('obfs-password', [''])[0]
            insecure = query_params.get('insecure', [''])[0]
            
            return self.create_output(
                protocol='Hysteria2',
                server=parsed.hostname,
                port=parsed.port,
                password=parsed.username,  # Hysteria2使用username作为密码
                sni=sni,
                obfs=obfs,
                obfs_password=obfs_password,
                insecure=insecure,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"Hysteria2解析错误: {e}")
            return None