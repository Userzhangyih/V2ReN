# config/protocols/socks.py
"""
SOCKS协议解析器
"""
import urllib.parse
from .base import NodeParser
from config.logger import log_error


class SocksParser(NodeParser):
    """SOCKS协议解析器"""
    
    def parse(self, node_url):
        """解析SOCKS协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            
            # 提取备注信息（fragment）
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # 获取协议类型：socks、socks5、socks4
            protocol_type = parsed.scheme.lower()
            if protocol_type == 'socks':
                # 默认为SOCKS5
                protocol_type = 'socks5'
            
            # 解析用户认证信息
            username = parsed.username if parsed.username else ""
            password = parsed.password if parsed.password else ""
            
            # 解析服务器和端口
            server = parsed.hostname
            port = parsed.port
            
            if not server:
                log_error("SOCKS解析错误: 缺少服务器地址")
                return None
            
            # 如果没有指定端口，使用默认端口
            if not port:
                port = 1080  # SOCKS默认端口
            
            return self.create_output(
                protocol='Socks',
                server=server,
                port=port,
                username=username,
                password=password,
                socks_version=protocol_type.replace('socks', ''),  # 提取版本号：5, 4 或空字符串
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"SOCKS解析错误: {e}")
            return None