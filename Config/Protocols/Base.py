"""
基础解析器类
"""
from abc import ABC, abstractmethod
from Config.Logger import log_error, log_debug


class NodeParser(ABC):
    """节点解析器基类"""
    
    # 协议名称，子类必须覆盖
    protocol_name = None
    
    def __init__(self):
        if self.protocol_name is None:
            raise NotImplementedError("子类必须定义 protocol_name 属性")
    
    @abstractmethod
    def parse(self, node_url):
        """解析节点URL，返回解析后的字典"""
        pass
    
    def create_output(self, **kwargs):
        """创建标准输出格式"""
        output = {
            'protocol': kwargs.get('protocol', self.protocol_name),
            'server': kwargs.get('server', ''),
            'port': kwargs.get('port', 443),
            'remark': kwargs.get('remark', ''),
            'original_url': kwargs.get('original_url', ''),
            **kwargs
        }
        # 移除重复的protocol键
        if 'protocol' in kwargs:
            output['protocol'] = kwargs['protocol']
        
        log_debug(f"创建输出: protocol={output.get('protocol')}, server={output.get('server')}:{output.get('port')}")
        return output
    
    def can_parse(self, node_url):
        """检查是否能解析此URL"""
        if not node_url or '://' not in node_url:
            return False
        protocol = node_url.split('://')[0].lower()
        return protocol == self.protocol_name