# config/protocols/shadowsocks.py
"""
Shadowsocks协议解析器
"""
import re
import base64
import urllib.parse
from .base import NodeParser
from config.logger import log_error, log_warning


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