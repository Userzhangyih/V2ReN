# config/protocols/manager.py
"""
协议管理器
"""
import json
import re
import base64
import socket
import urllib.parse
from config.logger import log_info, log_warning, log_error, log_debug
from config.Base64 import process_base64_content
from config.IP_test import get_ip_location_with_cache

# 导入所有协议解析器
from .vmess import VMessParser
from .shadowsocks import ShadowSocksParser
from .trojan import TrojanParser
from .vless import VLessParser
from .hysteria import HysteriaParser
from .hysteria2 import Hysteria2Parser
from .socks import SocksParser


class ProtocolManager:
    """协议管理器"""
    
    def __init__(self):
        self.parsers = {
            'vmess': VMessParser(),
            'ss': ShadowSocksParser(),
            'trojan': TrojanParser(),
            'vless': VLessParser(),
            'hysteria': HysteriaParser(),
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
        elif node_url.startswith('hysteria://'):
            return self.parsers['hysteria'].parse(node_url)
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
        elif protocol == 'Hysteria':
            return self.rewrite_hysteria_node(original_node, new_name)
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
    
    def rewrite_hysteria_node(self, original_node, new_name):
        """重写Hysteria节点的备注"""
        try:
            parsed = urllib.parse.urlparse(original_node)
            new_parsed = parsed._replace(fragment=urllib.parse.quote(new_name))
            return urllib.parse.urlunparse(new_parsed)
        except Exception as e:
            log_error(f"重写Hysteria节点错误: {e}")
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

# 导出的函数接口
parse_nodes_from_content = protocol_manager.parse_nodes_from_content
parse_node = protocol_manager.parse_node
test_node = protocol_manager.test_node
rewrite_node_with_new_name = protocol_manager.rewrite_node_with_new_name

# 导出工具函数
get_ip_from_hostname = protocol_manager.get_ip_from_hostname
get_location_from_ip = protocol_manager.get_location_from_ip
is_likely_base64 = protocol_manager.is_likely_base64

# 保持原有函数名兼容性
parse_vmess = protocol_manager.parsers['vmess'].parse
parse_shadowsocks = protocol_manager.parsers['ss'].parse
parse_trojan = protocol_manager.parsers['trojan'].parse
parse_vless = protocol_manager.parsers['vless'].parse
parse_hysteria = protocol_manager.parsers['hysteria'].parse
parse_hysteria2 = protocol_manager.parsers['hysteria2'].parse
parse_socks = protocol_manager.parsers['socks'].parse