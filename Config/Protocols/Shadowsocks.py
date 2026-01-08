# Config/Protocols/Shadowsocks.py
"""
Shadowsocks协议解析器 - 修复版
支持标准SIP002格式: ss://base64(method:password)@server:port#remark
"""
import base64
import urllib.parse
import re
from .Base import NodeParser
from Config.Logger import log_error, log_debug, log_info


class ShadowsocksParser(NodeParser):
    """Shadowsocks协议解析器 - 修复版"""
    protocol_name = "ss"
    
    def parse(self, node_url):
        """解析Shadowsocks协议节点 - 修复SIP002格式解析"""
        try:
            log_debug(f"解析Shadowsocks节点: {node_url[:80]}...")
            
            # 确保有ss://前缀
            if not node_url.startswith('ss://'):
                log_error(f"无效的Shadowsocks链接: {node_url[:50]}")
                return None
            
            # 移除ss://前缀
            url_without_prefix = node_url[5:]
            
            # 先处理片段（备注）
            remark = ""
            if '#' in url_without_prefix:
                # 分离URL和备注
                parts = url_without_prefix.split('#', 1)
                base_url = parts[0]
                remark = urllib.parse.unquote(parts[1]) if len(parts) > 1 else ""
            else:
                base_url = url_without_prefix
            
            # 解码片段中的特殊字符（如emoji和国家代码）
            if remark:
                try:
                    # 尝试解码可能存在的URL编码
                    remark = urllib.parse.unquote(remark)
                except:
                    pass
            
            # 检查是否有@符号（SIP002格式）
            if '@' not in base_url:
                log_debug(f"不是标准SIP002格式，缺少@符号: {base_url[:50]}")
                return self.parse_legacy_format(node_url, base_url, remark)
            
            # 分离base64部分和服务器部分
            encoded_part, server_part = base_url.split('@', 1)
            
            # 清理encoded_part（移除可能的查询参数）
            if '?' in encoded_part:
                encoded_part = encoded_part.split('?')[0]
            
            # 解码base64部分
            try:
                # 清理base64字符串
                encoded_part = encoded_part.strip()
                encoded_part = re.sub(r'\s', '', encoded_part)
                
                # 确保长度是4的倍数
                padding_needed = 4 - len(encoded_part) % 4
                if padding_needed != 4:
                    encoded_part += '=' * padding_needed
                
                # 解码
                decoded_bytes = base64.b64decode(encoded_part)
                
                # 查找方法名和密码的分隔符
                if b':' not in decoded_bytes:
                    log_error(f"解码后没有找到冒号分隔符: {decoded_bytes[:50]}")
                    return None
                
                # 提取方法名和密码
                colon_pos = decoded_bytes.find(b':')
                method_bytes = decoded_bytes[:colon_pos]
                password_bytes = decoded_bytes[colon_pos + 1:]
                
                # 解码方法名（应该是可读的字符串）
                try:
                    method = method_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    method = method_bytes.decode('latin-1')
                
                # 解码密码（尝试UTF-8，失败则用latin-1）
                try:
                    password = password_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    # 对于UUID格式的密码，直接使用latin-1解码
                    password = password_bytes.decode('latin-1', errors='ignore')
                    # 如果不是可打印字符，使用原始字节的hex表示
                    if not self.is_printable(password):
                        password = password_bytes.hex()
                
            except Exception as e:
                log_error(f"解码Base64失败: {e}")
                return None
            
            # 解析服务器部分
            # 可能包含端口和查询参数
            server = ""
            port = 443
            
            # 分离查询参数（如果有）
            if '?' in server_part:
                server_part = server_part.split('?')[0]
            
            if ':' in server_part:
                # 处理IPv6地址（如[2001:db8::1]:8080）
                if server_part.startswith('['):
                    # IPv6地址
                    end_bracket = server_part.find(']')
                    if end_bracket != -1:
                        server = server_part[1:end_bracket]
                        port_part = server_part[end_bracket + 1:]
                        if port_part.startswith(':'):
                            port_str = port_part[1:].split('/')[0]
                            port = int(port_str) if port_str.isdigit() else 443
                else:
                    # IPv4地址或域名
                    parts = server_part.split(':', 1)
                    server = parts[0]
                    if len(parts) > 1:
                        port_str = parts[1].split('/')[0]  # 移除路径部分
                        port = int(port_str) if port_str.isdigit() else 443
            else:
                server = server_part
            
            # 创建输出
            result = self.create_output(
                protocol=self.protocol_name,
                server=server,
                port=port,
                method=method,
                password=password,
                remark=remark,
                original_url=node_url
            )
            
            log_debug(f"成功解析Shadowsocks节点: {server}:{port}, 方法: {method}")
            return result
            
        except Exception as e:
            log_error(f"Shadowsocks解析错误: {e}")
            import traceback
            log_error(f"详细错误: {traceback.format_exc()}")
            return None
    
    def parse_legacy_format(self, node_url, encoded_content, remark):
        """解析旧格式的Shadowsocks节点"""
        try:
            log_debug(f"尝试解析旧格式: {encoded_content[:50]}...")
            
            # 清理编码内容
            encoded_content = re.sub(r'\s', '', encoded_content)
            
            # 确保长度是4的倍数
            padding_needed = 4 - len(encoded_content) % 4
            if padding_needed != 4:
                encoded_content += '=' * padding_needed
            
            # 解码
            decoded_bytes = base64.b64decode(encoded_content)
            decoded_str = decoded_bytes.decode('utf-8', errors='ignore')
            
            log_debug(f"旧格式解码结果: {decoded_str[:100]}")
            
            # 尝试不同的旧格式
            # 格式1: method:password@server:port
            if '@' in decoded_str:
                method_password, server_port = decoded_str.split('@', 1)
                if ':' in method_password:
                    method, password = method_password.split(':', 1)
                else:
                    method = method_password
                    password = ''
                
                if ':' in server_port:
                    server, port = server_port.split(':', 1)
                    port = int(port) if port.isdigit() else 443
                else:
                    server = server_port
                    port = 443
                
                return self.create_output(
                    protocol=self.protocol_name,
                    server=server,
                    port=port,
                    method=method,
                    password=password,
                    remark=remark,
                    original_url=node_url
                )
            
            # 格式2: server:port:method:password
            if decoded_str.count(':') >= 3:
                parts = decoded_str.split(':')
                server = parts[0]
                port = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 443
                method = parts[2] if len(parts) > 2 else ''
                password = parts[3] if len(parts) > 3 else ''
                
                return self.create_output(
                    protocol=self.protocol_name,
                    server=server,
                    port=port,
                    method=method,
                    password=password,
                    remark=remark,
                    original_url=node_url
                )
            
            log_error(f"无法解析旧格式: {decoded_str[:100]}")
            return None
            
        except Exception as e:
            log_error(f"旧格式解析错误: {e}")
            return None
    
    def is_printable(self, text):
        """检查文本是否可打印"""
        try:
            return all(c.isprintable() or c.isspace() for c in text)
        except:
            return False