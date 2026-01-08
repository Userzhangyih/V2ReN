"""
WireGuard协议解析器
"""
import urllib.parse
from .Base import NodeParser
from Config.Logger import log_error


class WireGuardParser(NodeParser):
    """WireGuard协议解析器"""
    protocol_name = "wireguard"
    
    def parse(self, node_url):
        """解析WireGuard协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # WireGuard参数
            private_key = parsed.username or ''
            
            # 提取查询参数
            public_key = query_params.get('public_key', [''])[0]
            endpoint = query_params.get('endpoint', [''])[0]
            allowed_ips = query_params.get('allowed_ips', ['0.0.0.0/0'])[0]
            persistent_keepalive = query_params.get('persistent_keepalive', ['25'])[0]
            dns = query_params.get('dns', [''])[0]
            mtu = query_params.get('mtu', [''])[0]
            
            return self.create_output(
                protocol='WireGuard',
                server=parsed.hostname,
                port=parsed.port,
                private_key=private_key,
                public_key=public_key,
                endpoint=endpoint,
                allowed_ips=allowed_ips,
                persistent_keepalive=persistent_keepalive,
                dns=dns,
                mtu=mtu,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"WireGuard解析错误: {e}")
            return None