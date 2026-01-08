# Config/Base64.py (完整修复版)
import base64
import re

# 导入日志模块
from Config.Logger import log_info, log_warning, log_error, log_debug

def safe_base64_decode(encoded_string, return_bytes=False):
    """
    安全的Base64解码函数，处理各种格式问题
    
    Args:
        encoded_string: Base64编码的字符串
        return_bytes: 是否返回字节而不是字符串
        
    Returns:
        str 或 bytes: 解码后的数据
    """
    try:
        # 清理字符串
        encoded_string = encoded_string.strip()
        encoded_string = re.sub(r'\s', '', encoded_string)
        
        # 确保长度是4的倍数
        remainder = len(encoded_string) % 4
        if remainder != 0:
            encoded_string += '=' * (4 - remainder)
        
        # 尝试解码
        decoded_bytes = base64.b64decode(encoded_string, validate=True)
        
        if return_bytes:
            return decoded_bytes
        
        # 尝试解码为UTF-8字符串
        try:
            return decoded_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # 如果不是UTF-8，尝试其他编码
            for encoding in ['latin-1', 'ascii', 'gbk', 'gb2312', 'gb18030']:
                try:
                    return decoded_bytes.decode(encoding)
                except UnicodeDecodeError:
                    continue
            
            # 如果所有编码都失败，返回字节的hex表示
            return decoded_bytes.hex()
            
    except base64.binascii.Error:
        # 尝试清理非法字符
        cleaned = re.sub(r'[^A-Za-z0-9+/=]', '', encoded_string)
        remainder = len(cleaned) % 4
        if remainder != 0:
            cleaned += '=' * (4 - remainder)
        
        try:
            decoded_bytes = base64.b64decode(cleaned)
            
            if return_bytes:
                return decoded_bytes
            
            try:
                return decoded_bytes.decode('utf-8')
            except UnicodeDecodeError:
                return decoded_bytes.hex()
        except Exception:
            return None
    except Exception:
        return None

def decode_base64_nodes(encoded_content):
    """
    解码base64编码的节点列表
    
    Args:
        encoded_content: Base64编码的节点内容
        
    Returns:
        list: 解码后的节点URL列表
    """
    try:
        # 清理输入内容
        encoded_content = encoded_content.strip()
        
        # 移除所有空白字符
        encoded_content = re.sub(r'\s', '', encoded_content)
        
        # 确保长度是4的倍数
        remainder = len(encoded_content) % 4
        if remainder != 0:
            # 添加padding
            encoded_content += '=' * (4 - remainder)
        
        # 尝试解码
        decoded_bytes = base64.b64decode(encoded_content, validate=True)
        decoded_content = decoded_bytes.decode('utf-8', errors='replace')
        
        # 按行分割并清理
        nodes = []
        for line in decoded_content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                nodes.append(line)
        
        log_debug(f"Base64解码成功，获得 {len(nodes)} 个节点")
        return nodes
    except base64.binascii.Error as e:
        log_error(f"Base64格式错误: {e}")
        # 尝试清理Base64字符串
        try:
            # 移除非法字符
            cleaned = re.sub(r'[^A-Za-z0-9+/=]', '', encoded_content)
            remainder = len(cleaned) % 4
            if remainder != 0:
                cleaned += '=' * (4 - remainder)
            
            decoded_bytes = base64.b64decode(cleaned)
            decoded_content = decoded_bytes.decode('utf-8', errors='replace')
            
            nodes = []
            for line in decoded_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('//'):
                    nodes.append(line)
            
            log_debug(f"清理后Base64解码成功，获得 {len(nodes)} 个节点")
            return nodes
        except Exception as e2:
            log_error(f"清理后Base64解码仍然失败: {e2}")
            return []
    except Exception as e:
        log_error(f"Base64解码错误: {e}")
        return []

def is_base64_encoded(content):
    """
    检查内容是否为base64编码的节点列表
    
    Args:
        content: 待检查的内容
        
    Returns:
        bool: 是否为Base64编码
    """
    content = content.strip()
    
    # 如果内容很短，直接检查是否是base64
    if len(content) < 100:
        base64_pattern = re.compile(r'^[A-Za-z0-9+/]+={0,2}$')
        is_base64 = base64_pattern.match(content) is not None
        log_debug(f"短内容Base64检测结果: {is_base64}")
        return is_base64
    
    # 对于长内容，检查是否包含常见的协议前缀
    protocols = [
        'vmess://', 'ss://', 'trojan://', 'vless://', 
        'hysteria://', 'hysteria2://', 'hysteria3://',
        'socks://', 'socks5://', 'socks4://', 'tuic://',
        'http://', 'https://', 'trojan-go://', 'mieru://',
        'naive://', 'shadowtls://', 'anytls://', 'ssh://',
        'sftp://', 'wireguard://', 'reality://', 'juicity://',
        'h3://', 'hy3://', 'singbox://', 'sb://', 'gost://',
        'clashmeta://', 'clash://', 'cm://', 'xtls://',
        'ssh+ws://', 'sftp+ws://', 'ssh+wss://', 'sftp+wss://'
    ]
    
    # 如果内容已经包含协议前缀，则不是base64编码
    for protocol in protocols:
        if protocol in content:
            log_debug("检测到协议前缀，不是Base64编码")
            return False
    
    # 尝试解码前100个字符来检查
    try:
        test_content = content[:100]
        padding = 4 - len(test_content) % 4
        if padding != 4:
            test_content += '=' * padding
        
        decoded = base64.b64decode(test_content).decode('utf-8', errors='ignore')
        
        # 检查解码后的内容是否包含协议前缀
        for protocol in protocols:
            if protocol in decoded:
                log_debug("通过部分解码检测到协议前缀，是Base64编码")
                return True
    except Exception as e:
        log_debug(f"部分解码测试失败: {e}")
    
    # 检查base64模式
    base64_pattern = re.compile(r'^[A-Za-z0-9+/=\n]+$')
    lines = content.split('\n')
    
    # 如果所有行都符合base64模式，则认为是base64编码
    for line in lines:
        line = line.strip()
        if line and not base64_pattern.match(line):
            log_debug(f"行不符合Base64模式: {line[:50]}...")
            return False
    
    result = len(lines) > 0
    log_debug(f"Base64模式检测结果: {result}")
    return result

def process_base64_content(content):
    """
    处理可能为base64编码的内容
    如果是base64编码则解码，否则返回原内容按行分割
    
    Args:
        content: 节点内容
        
    Returns:
        list: 节点URL列表
    """
    content = content.strip()
    
    if not content:
        log_debug("内容为空")
        return []
    
    if is_base64_encoded(content):
        log_debug("检测到Base64编码内容，正在解码...")
        return decode_base64_nodes(content)
    else:
        # 按行分割明文节点
        nodes = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                nodes.append(line)
        
        log_debug(f"解析明文内容，获得 {len(nodes)} 个节点")
        return nodes

def encode_nodes_to_base64(nodes):
    """
    将节点列表编码为Base64格式
    
    Args:
        nodes: 节点URL列表
        
    Returns:
        str: Base64编码的节点内容
    """
    try:
        # 将所有节点连接成一个字符串
        all_nodes = '\n'.join(nodes)
        
        # Base64编码
        encoded_nodes = base64.b64encode(all_nodes.encode('utf-8')).decode('utf-8')
        
        log_debug(f"编码 {len(nodes)} 个节点到Base64")
        return encoded_nodes
    except Exception as e:
        log_error(f"编码节点到Base64错误: {e}")
        return ""