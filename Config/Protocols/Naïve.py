"""
Naïve协议解析器
"""
import urllib.parse
from .Base import NodeParser
from Config.Logger import log_error


class NaïveParser(NodeParser):
    """Naïve协议解析器"""
    protocol_name = "naive"
    
    def parse(self, node_url):
        """解析Naïve协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # Naïve格式: naive://username:password@host:port
            username = parsed.username or ''
            password = parsed.password or ''
            
            # 提取查询参数
            padding = query_params.get('padding', ['true'])[0].lower() == 'true'
            sni = query_params.get('sni', [''])[0]
            allow_insecure = query_params.get('allowInsecure', ['0'])[0]
            
            return self.create_output(
                protocol='Naïve',
                server=parsed.hostname,
                port=parsed.port,
                username=username,
                password=password,
                padding=padding,
                sni=sni,
                allow_insecure=allow_insecure,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"Naïve解析错误: {e}")
            return None