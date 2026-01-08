"""
SOCKS协议解析器 - 支持SOCKS4和SOCKS5
"""
import urllib.parse
from .Base import NodeParser
from Config.Logger import log_error


class SOCKSParser(NodeParser):
    """SOCKS协议解析器"""
    protocol_name = "socks"
    
    def parse(self, node_url):
        """解析SOCKS协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            
            # 提取备注信息
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # 解析用户名和密码
            username = parsed.username or ''
            password = parsed.password or ''
            
            # 判断版本
            scheme = parsed.scheme.lower()
            if scheme == 'socks5':
                version = '5'
            elif scheme == 'socks4':
                version = '4'
            else:
                version = '5'  # 默认为SOCKS5
            
            return self.create_output(
                protocol='SOCKS' + version,
                server=parsed.hostname,
                port=parsed.port,
                username=username,
                password=password,
                version=version,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"SOCKS解析错误: {e}")
            return None