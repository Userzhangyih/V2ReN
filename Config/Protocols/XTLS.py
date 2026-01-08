"""
XTLS协议解析器
"""
import urllib.parse
from .Base import NodeParser
from Config.Logger import log_error


class XTLSParser(NodeParser):
    """XTLS协议解析器"""
    protocol_name = "xtls"
    
    def parse(self, node_url):
        """解析XTLS协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # XTLS协议参数
            uuid = parsed.username or ''
            
            # 提取查询参数
            flow = query_params.get('flow', ['xtls-rprx-direct'])[0]
            encryption = query_params.get('encryption', ['none'])[0]
            type = query_params.get('type', ['tcp'])[0]
            security = query_params.get('security', ['tls'])[0]
            sni = query_params.get('sni', [''])[0]
            host = query_params.get('host', [''])[0]
            path = query_params.get('path', [''])[0]
            
            return self.create_output(
                protocol='XTLS',
                server=parsed.hostname,
                port=parsed.port,
                uuid=uuid,
                flow=flow,
                encryption=encryption,
                type=type,
                security=security,
                sni=sni,
                host=host,
                path=path,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"XTLS解析错误: {e}")
            return None