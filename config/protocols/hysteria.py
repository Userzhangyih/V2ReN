# config/protocols/hysteria.py
"""
Hysteria协议解析器（第一代）
"""
import urllib.parse
from .base import NodeParser
from config.logger import log_error


class HysteriaParser(NodeParser):
    """Hysteria协议解析器（第一代）"""
    
    def parse(self, node_url):
        """解析Hysteria协议节点（第一代）"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息（fragment）
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # 提取查询参数
            auth = query_params.get('auth', [''])[0]
            if not auth and parsed.username:
                auth = parsed.username  # 有些节点将auth放在username部分
            
            alpn = query_params.get('alpn', [''])[0]
            obfs = query_params.get('obfs', [''])[0]
            insecure = query_params.get('insecure', ['0'])[0]
            upmbps = query_params.get('upmbps', [''])[0]
            downmbps = query_params.get('downmbps', [''])[0]
            peer = query_params.get('peer', [''])[0]
            host = query_params.get('host', [''])[0]
            sni = query_params.get('sni', [''])[0]
            
            # 处理端口
            port = parsed.port
            server = parsed.hostname
            
            # 如果没有端口但有peer参数，尝试从peer中提取端口
            if not port and peer:
                if ':' in peer:
                    peer_parts = peer.split(':')
                    if len(peer_parts) == 2 and peer_parts[1].isdigit():
                        port = int(peer_parts[1])
                        server = peer_parts[0]
            
            return self.create_output(
                protocol='Hysteria',
                server=server,
                port=port,
                auth=auth,
                alpn=alpn,
                obfs=obfs,
                insecure=insecure,
                upmbps=upmbps,
                downmbps=downmbps,
                peer=peer,
                host=host,
                sni=sni,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"Hysteria解析错误: {e}")
            return None