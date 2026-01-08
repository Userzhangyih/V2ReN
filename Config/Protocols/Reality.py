"""
Reality协议解析器
"""
import urllib.parse
from .Base import NodeParser
from Config.Logger import log_error


class RealityParser(NodeParser):
    """Reality协议解析器"""
    protocol_name = "reality"
    
    def parse(self, node_url):
        """解析Reality协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # Reality协议参数
            uuid = parsed.username or ''
            
            # 提取查询参数
            sni = query_params.get('sni', [''])[0]
            fp = query_params.get('fp', ['chrome'])[0]
            pbk = query_params.get('pbk', [''])[0]
            sid = query_params.get('sid', [''])[0]
            spx = query_params.get('spx', [''])[0]
            flow = query_params.get('flow', [''])[0]
            type = query_params.get('type', ['tcp'])[0]
            host = query_params.get('host', [''])[0]
            path = query_params.get('path', [''])[0]
            
            return self.create_output(
                protocol='Reality',
                server=parsed.hostname,
                port=parsed.port,
                uuid=uuid,
                sni=sni,
                fp=fp,
                pbk=pbk,
                sid=sid,
                spx=spx,
                flow=flow,
                type=type,
                host=host,
                path=path,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"Reality解析错误: {e}")
            return None