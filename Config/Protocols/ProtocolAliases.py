# Config/Protocols/ProtocolAliases.py
"""协议别名映射"""

PROTOCOL_ALIASES = {
    # 主协议 -> 别名列表
    'ss': ['ss', 'shadowsocks'],
    'vmess': ['vmess'],
    'vless': ['vless'],
    'trojan': ['trojan'],
    'trojan-go': ['trojan-go', 'trojango'],
    'hysteria': ['hysteria', 'hy'],
    'hysteria2': ['hysteria2', 'hy2'],
    'hysteria3': ['hysteria3', 'hy3'],
    'socks': ['socks'],
    'socks4': ['socks4'],
    'socks5': ['socks5'],
    'http': ['http'],
    'https': ['https'],
    'tuic': ['tuic'],
    'wireguard': ['wireguard', 'wg'],
    'reality': ['reality'],
    'juicity': ['juicity'],
    'xtls': ['xtls'],
    'ssh': ['ssh', 'sftp'],
    'ssh+ws': ['ssh+ws', 'ssh+websocket'],
    'ssh+wss': ['ssh+wss', 'ssh+websockets'],
}

# 协议友好名称映射
PROTOCOL_FRIENDLY_NAMES = {
    'ss': 'Shadowsocks',
    'vmess': 'VMess',
    'vless': 'VLESS',
    'trojan': 'Trojan',
    'trojan-go': 'Trojan-Go',
    'hysteria': 'Hysteria',
    'hysteria2': 'Hysteria2',
    'hysteria3': 'Hysteria3',
    'socks': 'SOCKS',
    'socks4': 'SOCKS4',
    'socks5': 'SOCKS5',
    'http': 'HTTP',
    'https': 'HTTPS',
    'tuic': 'TUIC',
    'wireguard': 'WireGuard',
    'reality': 'Reality',
    'juicity': 'Juicity',
    'xtls': 'XTLS',
    'ssh': 'SSH',
    'ssh+ws': 'SSH+WebSocket',
    'ssh+wss': 'SSH+WebSocket Secure',
}

# 反向映射：别名 -> 主协议
ALIAS_TO_PROTOCOL = {}
for protocol, aliases in PROTOCOL_ALIASES.items():
    for alias in aliases:
        ALIAS_TO_PROTOCOL[alias] = protocol

def get_protocol_by_alias(alias):
    """通过别名获取主协议名"""
    return ALIAS_TO_PROTOCOL.get(alias.lower(), alias)

def get_friendly_name(protocol):
    """获取协议的友好名称"""
    return PROTOCOL_FRIENDLY_NAMES.get(protocol, protocol)

def is_valid_alias(alias):
    """检查是否为有效的协议别名"""
    return alias.lower() in ALIAS_TO_PROTOCOL

def get_all_aliases():
    """获取所有别名"""
    all_aliases = []
    for aliases in PROTOCOL_ALIASES.values():
        all_aliases.extend(aliases)
    return all_aliases