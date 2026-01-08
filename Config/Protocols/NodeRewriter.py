"""
节点重写器 - 重写节点配置
"""
import base64
import json
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode, quote
from Config.Logger import log_debug, log_error


def rewrite_node_with_new_name(node, new_name, node_info):
    """根据节点信息重写节点配置"""
    try:
        protocol = node_info.get('protocol', '').lower()
        
        # 根据协议类型选择不同的重写方法
        if protocol == 'vmess':
            return rewrite_vmess(node, new_name)
        elif protocol == 'vless':
            return rewrite_vless(node, new_name)
        elif protocol == 'hysteria' or protocol == 'hysteria2' or protocol == 'hysteria3':
            return rewrite_hysteria(node, new_name, protocol)
        elif protocol == 'trojan' or protocol == 'trojan-go':
            return rewrite_trojan(node, new_name)
        elif protocol == 'ss' or 'shadowsocks' in protocol:
            return rewrite_ss(node, new_name)
        elif 'socks' in protocol:
            return rewrite_socks(node, new_name)
        elif 'http' in protocol:
            return rewrite_http(node, new_name)
        elif protocol == 'tuic':
            return rewrite_tuic(node, new_name)
        elif protocol == 'wireguard':
            return rewrite_wireguard(node, new_name)
        elif protocol == 'reality':
            return rewrite_reality(node, new_name)
        elif protocol == 'juicity':
            return rewrite_juicity(node, new_name)
        elif protocol == 'xtls':
            return rewrite_xtls(node, new_name)
        elif protocol == 'ssh' or 'ssh+ws' in protocol:
            return rewrite_ssh(node, new_name)
        else:
            # 通用方法：添加到fragment中
            return rewrite_general(node, new_name)
            
    except Exception as e:
        log_error(f"重写节点失败: {e}")
        return node


def rewrite_vmess(node, new_name):
    """重写VMess节点"""
    try:
        # 提取base64编码部分
        encoded = node[8:]  # 移除"vmess://"
        
        # 解码
        padding = 4 - len(encoded) % 4
        if padding != 4:
            encoded += '=' * padding
        
        decoded = base64.b64decode(encoded).decode('utf-8')
        config = json.loads(decoded)
        
        # 更新备注
        config['ps'] = new_name
        
        # 重新编码
        new_encoded = base64.b64encode(json.dumps(config).encode('utf-8')).decode('utf-8')
        return f"vmess://{new_encoded}"
    except Exception as e:
        log_error(f"重写VMess失败: {e}")
        return node


def rewrite_vless(node, new_name):
    """重写VLESS节点"""
    try:
        parsed = urlparse(node)
        
        # 构建新的URL，将新名称添加到fragment
        new_url = parsed._replace(fragment=quote(new_name, safe=''))
        return urlunparse(new_url)
    except Exception as e:
        log_error(f"重写VLESS失败: {e}")
        return node


def rewrite_hysteria(node, new_name, protocol):
    """重写Hysteria节点"""
    try:
        parsed = urlparse(node)
        
        # 构建新的URL，将新名称添加到fragment
        new_url = parsed._replace(fragment=quote(new_name, safe=''))
        return urlunparse(new_url)
    except Exception as e:
        log_error(f"重写{protocol}失败: {e}")
        return node


def rewrite_trojan(node, new_name):
    """重写Trojan节点"""
    try:
        parsed = urlparse(node)
        new_url = parsed._replace(fragment=quote(new_name, safe=''))
        return urlunparse(new_url)
    except Exception as e:
        log_error(f"重写Trojan失败: {e}")
        return node


def rewrite_ss(node, new_name):
    """重写Shadowsocks节点"""
    try:
        parsed = urlparse(node)
        new_url = parsed._replace(fragment=quote(new_name, safe=''))
        return urlunparse(new_url)
    except Exception as e:
        log_error(f"重写Shadowsocks失败: {e}")
        return node


def rewrite_socks(node, new_name):
    """重写SOCKS节点"""
    try:
        parsed = urlparse(node)
        new_url = parsed._replace(fragment=quote(new_name, safe=''))
        return urlunparse(new_url)
    except Exception as e:
        log_error(f"重写SOCKS失败: {e}")
        return node


def rewrite_http(node, new_name):
    """重写HTTP节点"""
    try:
        parsed = urlparse(node)
        new_url = parsed._replace(fragment=quote(new_name, safe=''))
        return urlunparse(new_url)
    except Exception as e:
        log_error(f"重写HTTP失败: {e}")
        return node


def rewrite_tuic(node, new_name):
    """重写TUIC节点"""
    try:
        parsed = urlparse(node)
        new_url = parsed._replace(fragment=quote(new_name, safe=''))
        return urlunparse(new_url)
    except Exception as e:
        log_error(f"重写TUIC失败: {e}")
        return node


def rewrite_wireguard(node, new_name):
    """重写WireGuard节点"""
    try:
        # WireGuard格式特殊，通常不修改fragment
        # 但我们可以在查询参数中添加备注
        parsed = urlparse(node)
        query_params = parse_qs(parsed.query)
        
        # 添加或更新remark参数
        query_params['remark'] = [new_name]
        
        # 重新构建查询字符串
        new_query = urlencode(query_params, doseq=True)
        new_url = parsed._replace(query=new_query)
        
        return urlunparse(new_url)
    except Exception as e:
        log_error(f"重写WireGuard失败: {e}")
        return node


def rewrite_reality(node, new_name):
    """重写Reality节点"""
    try:
        parsed = urlparse(node)
        new_url = parsed._replace(fragment=quote(new_name, safe=''))
        return urlunparse(new_url)
    except Exception as e:
        log_error(f"重写Reality失败: {e}")
        return node


def rewrite_juicity(node, new_name):
    """重写Juicity节点"""
    try:
        parsed = urlparse(node)
        new_url = parsed._replace(fragment=quote(new_name, safe=''))
        return urlunparse(new_url)
    except Exception as e:
        log_error(f"重写Juicity失败: {e}")
        return node


def rewrite_xtls(node, new_name):
    """重写XTLS节点"""
    try:
        parsed = urlparse(node)
        new_url = parsed._replace(fragment=quote(new_name, safe=''))
        return urlunparse(new_url)
    except Exception as e:
        log_error(f"重写XTLS失败: {e}")
        return node


def rewrite_ssh(node, new_name):
    """重写SSH节点"""
    try:
        parsed = urlparse(node)
        new_url = parsed._replace(fragment=quote(new_name, safe=''))
        return urlunparse(new_url)
    except Exception as e:
        log_error(f"重写SSH失败: {e}")
        return node


def rewrite_general(node, new_name):
    """通用重写方法"""
    try:
        if '#' in node:
            # 替换现有的fragment
            parts = node.split('#', 1)
            return f"{parts[0]}#{quote(new_name, safe='')}"
        else:
            # 添加新的fragment
            return f"{node}#{quote(new_name, safe='')}"
    except Exception:
        return node


def encode_special_protocols(node_info, new_name):
    """处理特殊协议的编码需求"""
    protocol = node_info.get('protocol', '').lower()
    
    if protocol == 'wireguard':
        # WireGuard需要特殊的配置处理
        return encode_wireguard_config(node_info, new_name)
    elif protocol == 'ssh':
        # SSH可能需要密钥处理
        return encode_ssh_config(node_info, new_name)
    
    return None


def encode_wireguard_config(node_info, new_name):
    """编码WireGuard配置"""
    try:
        config = f"""[Interface]
PrivateKey = {node_info.get('private_key', '')}
Address = {node_info.get('address', '10.0.0.2/32')}
DNS = {node_info.get('dns', '8.8.8.8')}
MTU = {node_info.get('mtu', '1420')}

[Peer]
PublicKey = {node_info.get('public_key', '')}
Endpoint = {node_info.get('server', '')}:{node_info.get('port', '51820')}
AllowedIPs = {node_info.get('allowed_ips', '0.0.0.0/0')}
PersistentKeepalive = {node_info.get('persistent_keepalive', '25')}

# {new_name}
"""
        return config
    except Exception as e:
        log_error(f"编码WireGuard配置失败: {e}")
        return None


def encode_ssh_config(node_info, new_name):
    """编码SSH配置"""
    try:
        config = f"""Host {new_name}
    HostName {node_info.get('server', '')}
    Port {node_info.get('port', '22')}
    User {node_info.get('username', 'root')}
"""
        if node_info.get('password'):
            config += f"    Password {node_info.get('password')}\n"
        if node_info.get('private_key'):
            config += f"    IdentityFile {node_info.get('private_key')}\n"
        
        return config
    except Exception as e:
        log_error(f"编码SSH配置失败: {e}")
        return None