"""
ShadowTLS协议解析器
"""
import urllib.parse
from .Base import NodeParser
from Config.Logger import log_error


class ShadowTLSParser(NodeParser):
    """ShadowTLS协议解析器"""
    protocol_name = "shadowtls"
    
    def parse(self, node_url):
        """解析ShadowTLS协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # ShadowTLS参数
            password = parsed.password or ''
            
            # 提取查询参数
            sni = query_params.get('sni', [''])[0]
            mode = query_params.get('mode', [''])[0]
            fingerprint = query_params.get('fp', [''])[0]
            password = query_params.get('password', [password])[0]
            
            return self.create_output(
                protocol='ShadowTLS',
                server=parsed.hostname,
                port=parsed.port,
                password=password,
                sni=sni,
                mode=mode,
                fingerprint=fingerprint,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"ShadowTLS解析错误: {e}")
            return None