"""
GOST协议解析器
"""
import urllib.parse
from .Base import NodeParser
from Config.Logger import log_error


class GOSTParser(NodeParser):
    """GOST协议解析器"""
    protocol_name = "gost"
    
    def parse(self, node_url):
        """解析GOST协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # GOST格式: gost://method:password@host:port
            password = parsed.password or ''
            username = parsed.username or ''
            
            # 提取查询参数
            tls = query_params.get('tls', ['false'])[0].lower() == 'true'
            insecure = query_params.get('insecure', ['false'])[0].lower() == 'true'
            sni = query_params.get('sni', [''])[0]
            mode = query_params.get('mode', [''])[0]
            
            return self.create_output(
                protocol='GOST',
                server=parsed.hostname,
                port=parsed.port,
                username=username,
                password=password,
                method=query_params.get('method', [''])[0],
                tls=tls,
                insecure=insecure,
                sni=sni,
                mode=mode,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"GOST解析错误: {e}")
            return None