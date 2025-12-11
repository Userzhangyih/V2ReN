# config/protocols.py
import re
import base64
import json
import socket
import urllib.parse

# 导入日志模块和IP测试模块
from config.logger import log_info, log_warning, log_error, log_debug
from config.IP_test import get_ip_location_with_cache
from config.Base64 import process_base64_content


class NodeParser:
    """节点解析器基类"""
    
    def __init__(self):
        self.common_fields = {
            'protocol': '',
            'server': '',
            'port': '',
            'remark': '',
            'original_url': ''
        }
    
    def parse(self, node_url):
        """解析节点URL的通用方法"""
        raise NotImplementedError("子类必须实现此方法")
    
    def create_output(self, **kwargs):
        """创建标准化的输出字典"""
        output = self.common_fields.copy()
        output.update(kwargs)
        return output


class VMessParser(NodeParser):
    """VMess协议解析器"""
    
    def parse(self, node_url):
        """解析VMess协议节点"""
        try:
            # 移除vmess://前缀
            encoded_content = node_url[8:]
            
            # 添加padding并解码
            padding = 4 - len(encoded_content) % 4
            if padding != 4:
                encoded_content += '=' * padding
            
            decoded_bytes = base64.b64decode(encoded_content)
            config = json.loads(decoded_bytes)
            
            return self.create_output(
                protocol='VMess',
                server=config.get('add', ''),
                port=config.get('port', ''),
                id=config.get('id', ''),
                alterId=config.get('aid', ''),
                network=config.get('net', ''),
                type=config.get('type', ''),
                host=config.get('host', ''),
                path=config.get('path', ''),
                tls=config.get('tls', ''),
                original_url=node_url
            )
        except Exception as e:
            log_error(f"VMess解析错误: {e}")
            return None


class ShadowSocksParser(NodeParser):
    """Shadowsocks协议解析器"""
    
    def parse(self, node_url):
        """解析Shadowsocks协议节点"""
        try:
            # 移除协议头
            if not node_url.startswith('ss://'):
                return None
            
            content = node_url[5:]
            
            # 分离备注和配置内容
            if '#' in content:
                config_part, remark = content.split('#', 1)
                remark = urllib.parse.unquote(remark)
            else:
                config_part = content
                remark = ""
            
            # 处理URL编码
            config_part = urllib.parse.unquote(config_part)
            
            # 检查是否包含插件参数
            if any(param in config_part for param in ['?', ';', '&', 'plugin=']):
                return self.parse_with_plugin(node_url, config_part, remark)
            else:
                return self.parse_standard(node_url, config_part, remark)
                
        except Exception as e:
            log_error(f"Shadowsocks解析错误: {e}")
            return None
    
    def parse_standard(self, node_url, config_part, remark):
        """解析标准Shadowsocks格式"""
        try:
            if '@' in config_part:
                # SIP002格式: base64(method:password)@host:port
                return self.parse_sip002(node_url, config_part, remark)
            else:
                # 旧格式: base64(server:port:method:password)
                return self.parse_legacy(node_url, config_part, remark)
        except Exception as e:
            log_error(f"标准格式解析失败: {e}")
            return None
    
    def parse_sip002(self, node_url, config_part, remark):
        """解析SIP002格式"""
        auth_part, server_part = config_part.split('@', 1)
        
        # 解码认证部分
        auth_part_padded = self.add_base64_padding(auth_part)
        auth_decoded = base64.b64decode(auth_part_padded).decode('utf-8')
        
        # 解析method和password
        if ':' in auth_decoded:
            method, password = auth_decoded.split(':', 1)
        else:
            method, password = auth_decoded, ""
        
        # 解析服务器部分
        server_part_clean = server_part.split('?')[0].split(';')[0].split('&')[0]
        server, port = self.parse_server_part(server_part_clean)
        
        if not server:
            return None
        
        return self.create_output(
            protocol='Shadowsocks',
            server=server,
            port=port,
            method=method,
            password=password,
            remark=remark,
            original_url=node_url
        )
    
    def parse_legacy(self, node_url, config_part, remark):
        """解析旧格式"""
        config_part_padded = self.add_base64_padding(config_part)
        decoded_bytes = base64.b64decode(config_part_padded)
        
        try:
            decoded_str = decoded_bytes.decode('utf-8')
        except UnicodeDecodeError:
            decoded_str = decoded_bytes.decode('latin-1')
        
        parts = decoded_str.split(':')
        
        if len(parts) >= 4:
            server, port_str, method, password = parts[0], parts[1], parts[2], ':'.join(parts[3:])
        elif len(parts) == 3:
            server, port_str, method, password = parts[0], parts[1], parts[2], ""
        else:
            return None
        
        port = self.clean_port(port_str)
        if not port:
            return None
        
        return self.create_output(
            protocol='Shadowsocks',
            server=server,
            port=port,
            method=method,
            password=password,
            remark=remark,
            original_url=node_url
        )
    
    def parse_with_plugin(self, node_url, config_part, remark):
        """解析带插件的Shadowsocks"""
        try:
            base_part = config_part.split('?')[0].split(';')[0].split('&')[0]
            
            if '@' in base_part:
                auth_part, server_part = base_part.split('@', 1)
                
                # 解码认证部分
                auth_part_padded = self.add_base64_padding(auth_part)
                auth_decoded = base64.b64decode(auth_part_padded).decode('utf-8')
                
                # 解析method和password
                if ':' in auth_decoded:
                    method, password = auth_decoded.split(':', 1)
                else:
                    method, password = auth_decoded, ""
                
                # 解析服务器部分
                server_part_clean = server_part.split('/')[0]
                server, port = self.parse_server_part(server_part_clean)
                
                if not server:
                    return None
                
                # 提取插件信息
                plugin_info = self.extract_plugin_info(node_url)
                
                return self.create_output(
                    protocol='Shadowsocks',
                    server=server,
                    port=port,
                    method=method,
                    password=password,
                    remark=remark,
                    plugin=plugin_info,
                    original_url=node_url
                )
            
            return None
        except Exception as e:
            log_error(f"带插件 Shadowsocks 解析错误: {e}")
            return None
    
    def parse_server_part(self, server_part):
        """解析服务器部分"""
        if ':' in server_part:
            if server_part.startswith('['):
                # IPv6地址
                ipv6_end = server_part.index(']')
                server = server_part[1:ipv6_end]
                port_part = server_part[ipv6_end+1:]
                if port_part.startswith(':'):
                    port_str = port_part[1:]
                else:
                    port_str = ""
            else:
                # IPv4地址或域名
                server, port_str = server_part.split(':', 1)
            
            port = self.clean_port(port_str)
            return server, port
        else:
            return server_part, 8388  # 默认端口
    
    def extract_plugin_info(self, ss_url):
        """提取插件参数信息"""
        plugin_info = {}
        
        try:
            # 查找插件参数
            if 'plugin=' in ss_url:
                plugin_match = re.search(r'plugin=([^;|&]+)', ss_url)
                if plugin_match:
                    plugin_info['plugin'] = plugin_match.group(1)
            
            # 提取其他参数
            params = ['mode', 'host', 'path', 'tls', 'mux']
            for param in params:
                pattern = rf'{param}=([^;|&]+)'
                match = re.search(pattern, ss_url)
                if match:
                    plugin_info[param] = match.group(1)
            
            return plugin_info if plugin_info else None
        except Exception as e:
            log_error(f"提取插件信息错误: {e}")
            return None
    
    def add_base64_padding(self, s):
        """为base64字符串添加padding"""
        padding = 4 - len(s) % 4
        if padding != 4:
            return s + '=' * padding
        return s
    
    def clean_port(self, port_str):
        """清理端口号"""
        if not port_str:
            return 8388
        
        port_clean = ''.join(filter(str.isdigit, port_str))
        if port_clean and port_clean.isdigit():
            return int(port_clean)
        
        log_warning(f"无效的端口: {port_str}")
        return None


class TrojanParser(NodeParser):
    """Trojan协议解析器"""
    
    def parse(self, node_url):
        """解析Trojan协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息（fragment）
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # 提取SNI参数，如果没有则使用hostname
            sni = query_params.get('sni', [parsed.hostname])[0]
            type_param = query_params.get('type', ['tcp'])[0]
            
            return self.create_output(
                protocol='Trojan',
                server=parsed.hostname,
                port=parsed.port,
                password=parsed.username,
                sni=sni,
                type=type_param,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"Trojan解析错误: {e}")
            return None


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


class Hysteria2Parser(NodeParser):
    """Hysteria2协议解析器"""
    
    def parse(self, node_url):
        """解析Hysteria2协议节点"""
        try:
            parsed = urllib.parse.urlparse(node_url)
            query_params = urllib.parse.parse_qs(parsed.query)
            
            # 提取备注信息（fragment）
            remark = ""
            if parsed.fragment:
                remark = urllib.parse.unquote(parsed.fragment)
            
            # 提取查询参数
            sni = query_params.get('sni', [''])[0]
            obfs = query_params.get('obfs', [''])[0]
            obfs_password = query_params.get('obfs-password', [''])[0]
            insecure = query_params.get('insecure', [''])[0]
            
            return self.create_output(
                protocol='Hysteria2',
                server=parsed.hostname,
                port=parsed.port,
                password=parsed.username,  # Hysteria2使用username作为密码
                sni=sni,
                obfs=obfs,
                obfs_password=obfs_password,
                insecure=insecure,
                remark=remark,
                original_url=node_url
            )
        except Exception as e:
            log_error(f"Hysteria2解析错误: {e}")
            return None


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


class ProtocolManager:
    """协议管理器"""
    
    def __init__(self):
        self.parsers = {
            'vmess': VMessParser(),
            'ss': ShadowSocksParser(),
            'trojan': TrojanParser(),
            'vless': VLessParser(),
            'hysteria2': Hysteria2Parser(),
            'socks': SocksParser(),
            'socks5': SocksParser(),
            'socks4': SocksParser()
        }
    
    def parse_nodes_from_content(self, content):
        """
        从内容中解析节点，支持base64编码和明文
        
        Args:
            content: 包含节点信息的内容
            
        Returns:
            list: 解析后的节点列表
        """
        nodes = process_base64_content(content)
        
        parsed_nodes = []
        for node_url in nodes:
            parsed_node = self.parse_node(node_url)
            if parsed_node:
                parsed_nodes.append({
                    'original_url': node_url,
                    'parsed_info': parsed_node
                })
        
        return parsed_nodes
    
    def parse_node(self, node_url):
        """
        解析节点URL
        
        Args:
            node_url: 节点URL字符串
            
        Returns:
            dict: 解析后的节点信息
        """
        node_url = node_url.strip()
        
        # 检查是否是 base64 编码的完整节点
        if self.is_likely_base64(node_url) and len(node_url) > 50:
            try:
                decoded = base64.b64decode(node_url).decode('utf-8', errors='ignore')
                log_debug(f"Base64 解码成功: {decoded[:80]}...")
                # 递归解析解码后的内容
                return self.parse_node(decoded)
            except Exception as e:
                log_debug(f"Base64 解码失败: {e}")
                pass
        
        # 根据协议类型选择解析器
        if node_url.startswith('vmess://'):
            return self.parsers['vmess'].parse(node_url)
        elif node_url.startswith('ss://'):
            return self.parsers['ss'].parse(node_url)
        elif node_url.startswith('trojan://'):
            return self.parsers['trojan'].parse(node_url)
        elif node_url.startswith('vless://'):
            return self.parsers['vless'].parse(node_url)
        elif node_url.startswith('hysteria2://'):
            return self.parsers['hysteria2'].parse(node_url)
        elif node_url.startswith('socks://') or node_url.startswith('socks5://') or node_url.startswith('socks4://'):
            # 所有SOCKS协议使用同一个解析器
            return self.parsers['socks'].parse(node_url)
        else:
            log_warning(f"不支持的协议: {node_url[:50]}...")
            return None
    
    def is_likely_base64(self, s):
        """判断是否可能是 base64"""
        if len(s) < 20:
            return False
        pattern = re.compile(r'^[A-Za-z0-9+/]*={0,2}$')
        return pattern.match(s) is not None
    
    def get_ip_from_hostname(self, hostname):
        """从主机名获取IP地址 - 支持IPv4和IPv6"""
        try:
            # 尝试获取所有地址信息
            addr_info = socket.getaddrinfo(hostname, None)
            
            # 优先返回IPv4地址
            for addr in addr_info:
                if addr[0] == socket.AF_INET:  # IPv4
                    ip = addr[4][0]
                    log_debug(f"DNS解析成功 (IPv4): {hostname} -> {ip}")
                    return ip
            
            # 如果没有IPv4，返回IPv6地址
            for addr in addr_info:
                if addr[0] == socket.AF_INET6:  # IPv6
                    ip = addr[4][0]
                    log_debug(f"DNS解析成功 (IPv6): {hostname} -> {ip}")
                    return ip
            
            log_warning(f"DNS解析失败: 无法获取 {hostname} 的IP地址")
            return None
            
        except Exception as e:
            log_error(f"DNS解析错误: {e}")
            return None
    
    def is_valid_ip(self, ip):
        """检查IP地址是否有效（支持IPv4和IPv6）"""
        if not ip:
            return False
        
        # 检查IPv4格式
        try:
            socket.inet_pton(socket.AF_INET, ip)
            return True
        except socket.error:
            pass
        
        # 检查IPv6格式
        try:
            socket.inet_pton(socket.AF_INET6, ip)
            return True
        except socket.error:
            pass
        
        return False
    
    def is_private_ip(self, ip):
        """检查是否为私有IP地址（支持IPv4和IPv6）"""
        if not ip:
            return True
        
        # IPv4私有地址范围
        ipv4_private_ranges = [
            '10.', '192.168.', '172.16.', '172.17.', '172.18.', '172.19.',
            '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.',
            '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.',
            '127.', '169.254.'
        ]
        
        # IPv6私有地址范围
        ipv6_private_ranges = [
            'fc00:', 'fd00:', 'fe80:', '::1'
        ]
        
        # 检查IPv4私有地址
        for prefix in ipv4_private_ranges:
            if ip.startswith(prefix):
                return True
        
        # 检查IPv6私有地址
        for prefix in ipv6_private_ranges:
            if ip.startswith(prefix):
                return True
        
        return False
    
    def get_location_from_ip(self, ip):
        """从IP地址获取地理位置信息 - 使用独立的IP查询模块"""
        return get_ip_location_with_cache(ip)
    
    def test_node(self, node_info, city_mappings=None):
        """
        测试节点获取IP和位置信息
        
        Args:
            node_info: 节点信息字典
            city_mappings: 城市名称映射字典
            
        Returns:
            dict: 测试结果信息
        """
        try:
            # 获取服务器地址
            server = (node_info.get('server') or 
                     node_info.get('address') or 
                     node_info.get('host'))
            
            if not server:
                log_warning("测试节点失败: 无法获取服务器地址")
                return None
            
            # 检查是否为本地或无效主机名
            if server in ['127.0.0.1', '127.0.0.2', '127.0.0.53', 'localhost', '0.0.0.0']:
                log_warning(f"测试节点失败: 无效的服务器地址 {server}")
                return None
            
            # 获取IP地址
            ip = self.get_ip_from_hostname(server)
            if not ip:
                log_warning(f"测试节点失败: 无法解析 {server} 的IP地址")
                return None
            
            # 检查IP地址有效性
            if not self.is_valid_ip(ip):
                log_warning(f"测试节点失败: 无效的IP地址格式 {ip}")
                return None
            
            # 检查是否为私有IP
            if self.is_private_ip(ip):
                log_warning(f"测试节点失败: 私有IP地址 {ip}")
                return None
            
            # 获取位置信息
            location = self.get_location_from_ip(ip)
            if location:
                # 转换城市名为中文
                city_en = location.get('city', '')
                city_zh = city_en
                if city_mappings and city_en:
                    city_zh = city_mappings.get(city_en, city_en)
                
                result = {
                    'ip': location['ip'],
                    'country_code': location['country_code'],
                    'city': city_zh,
                    'city_en': city_en  # 保留英文城市名用于调试
                }
                
                # 添加额外信息（如果存在）
                if location.get('country_name'):
                    result['country_name'] = location['country_name']
                if location.get('region'):
                    result['region'] = location['region']
                if location.get('isp'):
                    result['isp'] = location['isp']
                
                log_info(f"节点测试成功: {server} -> {ip} ({result.get('country_name', '未知')})")
                return result
            else:
                log_warning(f"测试节点失败: 无法获取 {ip} 的地理位置信息")
                return None
        
        except Exception as e:
            log_error(f"测试节点错误: {e}")
        
        return None
    
    def rewrite_node_with_new_name(self, original_node, new_name, node_info):
        """
        将新名称写入节点配置中
        
        Args:
            original_node: 原始节点URL
            new_name: 新名称
            node_info: 节点信息
            
        Returns:
            str: 重写后的节点URL
        """
        protocol = node_info.get('protocol', '')
        
        if protocol == 'VMess':
            return self.rewrite_vmess_node(original_node, new_name)
        elif protocol == 'Shadowsocks':
            return self.rewrite_shadowsocks_node(original_node, new_name)
        elif protocol == 'Trojan':
            return self.rewrite_trojan_node(original_node, new_name)
        elif protocol == 'VLESS':
            return self.rewrite_vless_node(original_node, new_name)
        elif protocol == 'Hysteria2':
            return self.rewrite_hysteria2_node(original_node, new_name)
        elif protocol == 'Socks':
            return self.rewrite_socks_node(original_node, new_name)
        else:
            log_warning(f"不支持重写的协议: {protocol}")
            return original_node
    
    def rewrite_vmess_node(self, original_node, new_name):
        """重写VMess节点的备注"""
        try:
            # 移除vmess://前缀
            encoded_content = original_node[8:]
            
            # 添加padding并解码
            padding = 4 - len(encoded_content) % 4
            if padding != 4:
                encoded_content += '=' * padding
            
            decoded_bytes = base64.b64decode(encoded_content)
            config = json.loads(decoded_bytes)
            
            # 更新备注
            config['ps'] = new_name
            
            # 重新编码
            new_config_json = json.dumps(config, separators=(',', ':'))
            new_encoded = base64.b64encode(new_config_json.encode()).decode().rstrip('=')
            
            return f"vmess://{new_encoded}"
        except Exception as e:
            log_error(f"重写VMess节点错误: {e}")
            return original_node
    
    def rewrite_shadowsocks_node(self, original_node, new_name):
        """重写Shadowsocks节点的备注"""
        try:
            parsed = urllib.parse.urlparse(original_node)
            new_parsed = parsed._replace(fragment=urllib.parse.quote(new_name))
            return urllib.parse.urlunparse(new_parsed)
        except Exception as e:
            log_error(f"重写Shadowsocks节点错误: {e}")
            return original_node
    
    def rewrite_trojan_node(self, original_node, new_name):
        """重写Trojan节点的备注"""
        try:
            parsed = urllib.parse.urlparse(original_node)
            new_parsed = parsed._replace(fragment=urllib.parse.quote(new_name))
            return urllib.parse.urlunparse(new_parsed)
        except Exception as e:
            log_error(f"重写Trojan节点错误: {e}")
            return original_node
    
    def rewrite_vless_node(self, original_node, new_name):
        """重写VLESS节点的备注"""
        try:
            parsed = urllib.parse.urlparse(original_node)
            new_parsed = parsed._replace(fragment=urllib.parse.quote(new_name))
            return urllib.parse.urlunparse(new_parsed)
        except Exception as e:
            log_error(f"重写VLESS节点错误: {e}")
            return original_node
    
    def rewrite_hysteria2_node(self, original_node, new_name):
        """重写Hysteria2节点的备注"""
        try:
            parsed = urllib.parse.urlparse(original_node)
            new_parsed = parsed._replace(fragment=urllib.parse.quote(new_name))
            return urllib.parse.urlunparse(new_parsed)
        except Exception as e:
            log_error(f"重写Hysteria2节点错误: {e}")
            return original_node
    
    def rewrite_socks_node(self, original_node, new_name):
        """重写SOCKS节点的备注"""
        try:
            parsed = urllib.parse.urlparse(original_node)
            new_parsed = parsed._replace(fragment=urllib.parse.quote(new_name))
            return urllib.parse.urlunparse(new_parsed)
        except Exception as e:
            log_error(f"重写SOCKS节点错误: {e}")
            return original_node


# 创建全局管理器实例
protocol_manager = ProtocolManager()

# 兼容旧版本的函数接口
def parse_nodes_from_content(content):
    """从内容中解析节点"""
    return protocol_manager.parse_nodes_from_content(content)

def parse_node(node_url):
    """解析节点URL"""
    return protocol_manager.parse_node(node_url)

def test_node(node_info, city_mappings=None):
    """测试节点获取IP和位置信息"""
    return protocol_manager.test_node(node_info, city_mappings)

def rewrite_node_with_new_name(original_node, new_name, node_info):
    """将新名称写入节点配置中"""
    return protocol_manager.rewrite_node_with_new_name(original_node, new_name, node_info)

# 保持原有函数名兼容性
parse_vmess = protocol_manager.parsers['vmess'].parse
parse_shadowsocks = protocol_manager.parsers['ss'].parse
parse_trojan = protocol_manager.parsers['trojan'].parse
parse_vless = protocol_manager.parsers['vless'].parse
parse_hysteria2 = protocol_manager.parsers['hysteria2'].parse
parse_socks = protocol_manager.parsers['socks'].parse
get_ip_from_hostname = protocol_manager.get_ip_from_hostname
get_location_from_ip = protocol_manager.get_location_from_ip
is_likely_base64 = protocol_manager.is_likely_base64