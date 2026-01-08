"""
SSH协议解析器
"""
import urllib.parse
from .Base import NodeParser
from Config.Logger import log_error


class SSHParser(NodeParser):
    """SSH协议解析器"""
    protocol_name = "ssh"
    
    def parse(self, node_url):
        """解析SSH协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # SSH格式: ssh://username:password@host:port
            username = parsed.username or ''
            password = parsed.password or ''
            
            # 提取查询参数
            private_key = query_params.get('private-key', [''])[0]
            passphrase = query_params.get('passphrase', [''])[0]
            host_key = query_params.get('host-key', [''])[0]
            
            return self.create_output(
                protocol='SSH',
                server=parsed.hostname,
                port=parsed.port,
                username=username,
                password=password,
                private_key=private_key,
                passphrase=passphrase,
                host_key=host_key,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"SSH解析错误: {e}")
            return None