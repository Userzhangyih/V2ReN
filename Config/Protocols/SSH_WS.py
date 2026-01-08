"""
SSH-WebSocket协议解析器
"""
import urllib.parse
from .Base import NodeParser
from Config.Logger import log_error


class SSH_WSParser(NodeParser):
    """SSH-WebSocket协议解析器"""
    protocol_name = "ssh+ws"
    
    def parse(self, node_url):
        """解析SSH-WebSocket协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # SSH+WS格式: ssh+ws://username:password@host:port/path?query
            username = parsed.username or ''
            password = parsed.password or ''
            
            # 提取查询参数
            path = parsed.path
            host = query_params.get('host', [''])[0]
            sni = query_params.get('sni', [''])[0]
            tls = query_params.get('tls', ['false'])[0].lower() == 'true'
            allow_insecure = query_params.get('allowInsecure', ['0'])[0]
            
            return self.create_output(
                protocol='SSH+WS',
                server=parsed.hostname,
                port=parsed.port,
                username=username,
                password=password,
                path=path,
                host=host,
                sni=sni,
                tls=tls,
                allow_insecure=allow_insecure,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"SSH+WS解析错误: {e}")
            return None