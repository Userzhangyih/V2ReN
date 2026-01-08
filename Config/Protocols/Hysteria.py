# Config/Protocols/Hysteria.py
"""
Hysteria协议解析器
"""
import urllib.parse
from .Base import NodeParser
from Config.Logger import log_error


class HysteriaParser(NodeParser):
    """Hysteria协议解析器"""
    protocol_name = "hysteria"
    
    def parse(self, node_url):
        """解析Hysteria协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # 提取查询参数
            auth = query_params.get('auth', [''])[0]
            transport_protocol = query_params.get('protocol', ['udp'])[0]  # 重命名变量
            upmbps = query_params.get('upmbps', [''])[0]
            downmbps = query_params.get('downmbps', [''])[0]
            alpn = query_params.get('alpn', [''])[0]
            obfs = query_params.get('obfs', [''])[0]
            obfs_param = query_params.get('obfsParam', [''])[0]
            insecure = query_params.get('insecure', ['0'])[0]
            sni = query_params.get('sni', [''])[0]
            
            return self.create_output(
                server=parsed.hostname,
                port=parsed.port,
                auth=auth,
                transport_protocol=transport_protocol,  # 修改参数名
                upmbps=upmbps,
                downmbps=downmbps,
                alpn=alpn,
                obfs=obfs,
                obfs_param=obfs_param,
                insecure=insecure,
                sni=sni,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"Hysteria解析错误: {e}")
            return None