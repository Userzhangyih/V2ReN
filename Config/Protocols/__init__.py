
"""
协议解析器模块 - 统一接口
"""
from .ProtocolManager import ProtocolManager
from ..Base64 import safe_base64_decode  # 添加修复后的Base64函数

# 创建全局协议管理器实例
_protocol_manager = ProtocolManager()

def parse_node(node_url):
    """解析节点URL（对外接口）"""
    return _protocol_manager.parse_node(node_url)

def get_supported_protocols():
    """获取支持的协议列表（对外接口）"""
    return _protocol_manager.get_supported_protocols()

def get_protocol_manager():
    """获取协议管理器实例（高级使用）"""
    return _protocol_manager

# 从子模块导入测试和重写功能
from .NodeTester import (
    test_node,
    test_node_with_fallback,
    batch_test_nodes,
    get_node_statistics
)

from .NodeRewriter import (
    rewrite_node_with_new_name,
    rewrite_vmess,
    rewrite_vless,
    rewrite_hysteria,
    rewrite_trojan,
    rewrite_ss,
    rewrite_socks,
    rewrite_http,
    rewrite_tuic,
    rewrite_wireguard,
    rewrite_reality,
    rewrite_juicity,
    rewrite_xtls,
    rewrite_ssh,
    rewrite_general,
    encode_special_protocols,
    encode_wireguard_config,
    encode_ssh_config
)

# 导入协议别名（可选）
from .ProtocolAliases import PROTOCOL_ALIASES, get_protocol_by_alias, is_valid_alias, get_all_aliases

# 辅助函数：获取协议友好名称
def get_protocol_friendly_name(protocol_name):
    """获取协议的友好显示名称"""
    protocol_map = {
        'vmess': 'VMess',
        'ss': 'Shadowsocks',
        'shadowsocks': 'Shadowsocks',
        'trojan': 'Trojan',
        'trojan-go': 'Trojan-Go',
        'vless': 'VLESS',
        'hysteria': 'Hysteria',
        'hysteria2': 'Hysteria2',
        'hysteria3': 'Hysteria3',
        'socks': 'SOCKS',
        'socks4': 'SOCKS4',
        'socks5': 'SOCKS5',
        'http': 'HTTP',
        'https': 'HTTPS',
        'tuic': 'TUIC',
        'mieru': 'Mieru',
        'naive': 'Naïve',
        'shadowtls': 'ShadowTLS',
        'anytls': 'AnyTLS',
        'ssh': 'SSH',
        'sftp': 'SFTP',
        'wireguard': 'WireGuard',
        'reality': 'Reality',
        'juicity': 'Juicity',
        'singbox': 'SingBox',
        'gost': 'GOST',
        'clashmeta': 'ClashMeta',
        'xtls': 'XTLS',
        'ssh+ws': 'SSH+WebSocket',
        'ssh+wss': 'SSH+WebSocket',
        'loader': 'Loader',
        'manager': 'Manager'
    }
    return protocol_map.get(protocol_name.lower(), protocol_name)

# 辅助函数：检查是否为加密协议
def is_encrypted_protocol(protocol_name):
    """检查是否为加密协议"""
    encrypted_protocols = {
        'vmess', 'vless', 'trojan', 'trojan-go', 'hysteria',
        'hysteria2', 'hysteria3', 'reality', 'xtls', 'shadowtls',
        'anytls', 'juicity', 'tuic', 'ss', 'shadowsocks'
    }
    return protocol_name.lower() in encrypted_protocols

# 辅助函数：检查是否为代理协议
def is_proxy_protocol(protocol_name):
    """检查是否为代理协议"""
    proxy_protocols = {
        'http', 'https', 'socks', 'socks4', 'socks5'
    }
    return protocol_name.lower() in proxy_protocols

# 辅助函数：检查是否为VPN协议
def is_vpn_protocol(protocol_name):
    """检查是否为VPN协议"""
    vpn_protocols = {
        'wireguard', 'ssh', 'sftp'
    }
    return protocol_name.lower() in vpn_protocols

# 辅助函数：检查是否为Shadowsocks协议
def is_shadowsocks_protocol(protocol_name):
    """检查是否为Shadowsocks协议"""
    shadowsocks_protocols = {'ss', 'shadowsocks'}
    return protocol_name.lower() in shadowsocks_protocols

# 辅助函数：格式化节点信息
def format_node_info(node_info):
    """格式化节点信息为易读字符串"""
    if not node_info:
        return "无效节点"
    
    protocol = node_info.get('protocol', '未知')
    server = node_info.get('server', '未知')
    port = node_info.get('port', '未知')
    remark = node_info.get('remark', '')
    
    friendly_name = get_protocol_friendly_name(protocol)
    
    result = f"{friendly_name}: {server}:{port}"
    if remark:
        result += f" [{remark}]"
    
    return result

# 辅助函数：验证节点URL
def validate_node_url(node_url):
    """验证节点URL格式是否有效"""
    if not node_url or '://' not in node_url:
        return False, "无效的节点URL格式"
    
    protocol = node_url.split('://')[0].lower()
    
    # 检查是否为支持的协议
    manager = get_protocol_manager()
    if not manager.has_parser(protocol):
        return False, f"不支持的协议: {protocol}"
    
    return True, "URL格式有效"
    
# 辅助函数：批量解析节点
def parse_nodes_batch(node_urls, skip_failures=True):
    """批量解析节点URL列表"""
    results = []
    failures = []
    
    for i, url in enumerate(node_urls, 1):
        try:
            node_info = parse_node(url)
            if node_info:
                results.append(node_info)
            elif not skip_failures:
                failures.append((i, url, "解析失败"))
        except Exception as e:
            if not skip_failures:
                failures.append((i, url, str(e)))
    
    return {
        'success': results,
        'failures': failures,
        'total': len(node_urls),
        'success_count': len(results),
        'failure_count': len(failures)
    }

# 辅助函数：获取解析器状态
def get_parser_status():
    """获取所有解析器的状态信息"""
    manager = get_protocol_manager()
    parsers = manager.get_all_parsers()
    
    status = {
        'total_parsers': len(parsers),
        'parsers': {}
    }
    
    for protocol, parser in parsers.items():
        status['parsers'][protocol] = {
            'name': protocol,
            'friendly_name': get_protocol_friendly_name(protocol),
            'class_name': parser.__class__.__name__
        }
    
    return status

# 导出函数和变量
__all__ = [
    # 主要功能
    'parse_node',
    'test_node',
    'test_node_with_fallback',
    'rewrite_node_with_new_name',
    'get_supported_protocols',
    'get_protocol_manager',
    
    # 测试功能
    'test_node',
    'test_node_with_fallback',
    'batch_test_nodes',
    'get_node_statistics',
    
    # 重写功能
    'rewrite_node_with_new_name',
    'rewrite_vmess',
    'rewrite_vless',
    'rewrite_hysteria',
    'rewrite_trojan',
    'rewrite_ss',
    'rewrite_socks',
    'rewrite_http',
    'rewrite_tuic',
    'rewrite_wireguard',
    'rewrite_reality',
    'rewrite_juicity',
    'rewrite_xtls',
    'rewrite_ssh',
    'rewrite_general',
    'encode_special_protocols',
    'encode_wireguard_config',
    'encode_ssh_config',
    
    # Base64功能
    'safe_base64_decode',
    
    # 协议别名功能
    'PROTOCOL_ALIASES',
    'get_protocol_by_alias',
    'is_valid_alias',
    'get_all_aliases',
    
    # 辅助函数
    'get_protocol_friendly_name',
    'is_encrypted_protocol',
    'is_proxy_protocol',
    'is_vpn_protocol',
    'is_shadowsocks_protocol',
    'format_node_info',
    'validate_node_url',
    'parse_nodes_batch',
    'get_parser_status'
]
