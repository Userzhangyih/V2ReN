"""
HTTP协议解析器
"""
import urllib.parse
from .Base import NodeParser
from Config.Logger import log_error


class HTTPParser(NodeParser):
    """HTTP协议解析器"""
    protocol_name = "http"
    
    def parse(self, node_url):
        """解析HTTP协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # 解析用户名和密码
            username = parsed.username or ''
            password = parsed.password or ''
            
            # 判断是否HTTPS
            is_https = parsed.scheme.lower() == 'https'
            
            # 提取查询参数
            allow_insecure = query_params.get('allowInsecure', ['0'])[0]
            sni = query_params.get('sni', [''])[0]
            
            return self.create_output(
                protocol='HTTP' + ('S' if is_https else ''),
                server=parsed.hostname,
                port=parsed.port,
                username=username,
                password=password,
                tls=is_https,
                allow_insecure=allow_insecure,
                sni=sni,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"HTTP解析错误: {e}")
            return None