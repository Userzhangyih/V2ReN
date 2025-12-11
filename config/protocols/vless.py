# config/protocols/vless.py
"""
VLESS协议解析器
"""
import urllib.parse
from .base import NodeParser
from config.logger import log_error


class VLessParser(NodeParser):
    """VLESS协议解析器"""
    
    def parse(self, node_url):
        """解析VLESS协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息（fragment）
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # 处理路径解码
            path = query_params.get('path', [''])[0]
            if path:
                path = urllib.parse.unquote(path)
            
            # 处理host参数
            host = query_params.get('host', [''])[0]
            sni = query_params.get('sni', [''])[0]
            
            return self.create_output(
                protocol='VLESS',
                server=parsed.hostname,
                port=parsed.port,
                id=parsed.username,
                encryption=query_params.get('encryption', [''])[0],
                type=query_params.get('type', [''])[0],
                security=query_params.get('security', [''])[0],
                sni=sni,
                host=host,
                path=path,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"VLESS解析错误: {e}")
            return None