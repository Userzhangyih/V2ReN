# Config/Local.py
import geoip2.database
import os
import re
import time
from Config.Logger import log_info, log_warning, log_error, log_debug

class LocalGeoIPQuery:
    """本地GeoLite2数据库查询器 - 提供IP地理位置查询"""
    
    def __init__(self, db_paths=None):
        """
        初始化本地数据库查询器
        
        Args:
            db_paths: 数据库路径列表，按优先级排序
        """
        if db_paths is None:
            # 默认数据库路径，支持多种可能的位置
            default_paths = [
                # 尝试不同位置的数据库文件
                os.path.join("Data", "Database", "GeoLite2-City.mmdb"),
                os.path.join("Data", "GeoLite2-City.mmdb"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Data", "Database", "GeoLite2-City.mmdb"),
                os.path.join("GeoLite2-City.mmdb"),
                # 尝试绝对路径
                r"D:\Program\V2ReN\Data\Database\GeoLite2-City.mmdb",
            ]
            db_paths = default_paths
        
        self.db_paths = db_paths
        self.reader = None
        self.db_loaded = False
        self.used_db_path = None
        self.stats = {
            'total_queries': 0,
            'success_queries': 0,
            'city_found_queries': 0,
            'address_not_found': 0,
            'errors': 0
        }
        
        self._load_database()
    
    def _load_database(self):
        """尝试加载数据库文件"""
        for db_path in self.db_paths:
            try:
                # 处理路径中的转义字符
                db_path = os.path.normpath(db_path)
                if os.path.exists(db_path):
                    self.reader = geoip2.database.Reader(db_path)
                    self.db_loaded = True
                    self.used_db_path = db_path
                    file_size = os.path.getsize(db_path)
                    log_info(f"本地GeoLite2数据库加载成功: {db_path} ({file_size/1024/1024:.2f} MB)")
                    
                    # 输出数据库信息
                    self._log_database_info()
                    return
                else:
                    log_debug(f"数据库文件不存在: {db_path}")
            except Exception as e:
                log_error(f"加载数据库失败 {db_path}: {e}")
                continue
        
        if not self.db_loaded:
            log_warning("未找到可用的本地GeoLite2数据库，将使用在线API查询")
    
    def _log_database_info(self):
        """记录数据库信息"""
        try:
            metadata = self.reader.metadata()
            log_info(f"数据库版本: {metadata.database_type} v{metadata.binary_format_major_version}.{metadata.binary_format_minor_version}")
            log_info(f"构建时间: {metadata.build_epoch} ({time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(metadata.build_epoch))})")
            log_info(f"描述: {metadata.description.get('en', 'Unknown')}")
            log_info(f"IP版本: IPv{metadata.ip_version}")
            log_info(f"节点数: {metadata.node_count}")
        except Exception as e:
            log_debug(f"无法获取数据库信息: {e}")
    
    def query_ip(self, ip, check_city_only=False):
        """
        查询IP地址的地理位置信息
        
        Args:
            ip: IP地址字符串
            check_city_only: 如果为True，只检查是否有城市名，不返回完整结果
            
        Returns:
            dict: 地理位置信息字典，包含标准化的字段
                  如果check_city_only为True，返回{'has_city': True/False}
        """
        self.stats['total_queries'] += 1
        
        if not self.db_loaded or not self.reader:
            log_debug(f"本地数据库不可用，无法查询: {ip}")
            if check_city_only:
                return {'has_city': False, 'available': False}
            return None
        
        try:
            # 验证IP地址格式
            if not self._is_valid_ip(ip):
                log_debug(f"无效的IP地址格式: {ip}")
                self.stats['errors'] += 1
                if check_city_only:
                    return {'has_city': False, 'invalid_ip': True}
                return None
            
            # 查询城市信息
            response = self.reader.city(ip)
            
            # 检查是否有城市信息
            has_city = bool(response.city.name and response.city.name.strip())
            city_name = response.city.name if response.city.name else ''
            
            # 如果只需要检查城市信息，返回简化结果
            if check_city_only:
                self.stats['success_queries'] += 1
                if has_city:
                    self.stats['city_found_queries'] += 1
                
                return {
                    'has_city': has_city,
                    'available': True,
                    'city': city_name,
                    'country_code': response.country.iso_code if response.country.iso_code else '',
                    'country': response.country.name if response.country.name else ''
                }
            
            # 构建完整结果字典
            result = {
                'ip': ip,
                'country': response.country.name if response.country.name else '',
                'country_code': response.country.iso_code if response.country.iso_code else '',
                'city': city_name,
                'city_en': city_name,  # 英文城市名
                'region': response.subdivisions.most_specific.name if response.subdivisions.most_specific.name else '',
                'region_code': response.subdivisions.most_specific.iso_code if response.subdivisions.most_specific.iso_code else '',
                'lat': float(response.location.latitude) if response.location.latitude else 0.0,
                'lon': float(response.location.longitude) if response.location.longitude else 0.0,
                'timezone': response.location.time_zone if response.location.time_zone else '',
                'isp': '',  # 本地数据库不包含ISP信息
                'source': 'local-geolite2',
                'local_query': True,
                'has_city': has_city,  # 是否有城市信息
                'accuracy': 'high' if has_city else 'low',
                'postal_code': response.postal.code if response.postal.code else '',
                'metro_code': response.location.metro_code if response.location.metro_code else '',
                'continent': response.continent.name if response.continent.name else '',
                'continent_code': response.continent.code if response.continent.code else '',
                'is_in_european_union': response.country.is_in_european_union if hasattr(response.country, 'is_in_european_union') else False
            }
            
            # 更新统计信息
            self.stats['success_queries'] += 1
            if has_city:
                self.stats['city_found_queries'] += 1
                log_debug(f"本地查询成功 [{ip}]: {result['city']}, {result['country_code']}")
            else:
                log_debug(f"本地查询成功但城市信息缺失 [{ip}]: {result['country_code']}")
            
            return result
            
        except geoip2.errors.AddressNotFoundError:
            self.stats['address_not_found'] += 1
            log_debug(f"IP地址在本地数据库中未找到: {ip}")
            if check_city_only:
                return {'has_city': False, 'address_not_found': True}
            return None
        except Exception as e:
            self.stats['errors'] += 1
            log_error(f"本地数据库查询异常 [{ip}]: {e}")
            if check_city_only:
                return {'has_city': False, 'error': str(e)}
            return None
    
    def check_city_available(self, ip):
        """
        快速检查IP地址是否有城市信息
        
        Args:
            ip: IP地址
            
        Returns:
            bool: 如果有城市信息返回True，否则返回False
        """
        result = self.query_ip(ip, check_city_only=True)
        return result.get('has_city', False) if result else False
    
    def check_multiple_city_available(self, ip_list):
        """
        批量检查多个IP地址是否有城市信息
        
        Args:
            ip_list: IP地址列表
            
        Returns:
            dict: 统计结果，包括总数、有城市信息的数量、覆盖率等
        """
        total = len(ip_list)
        has_city = 0
        results = {}
        
        log_info(f"开始批量检查 {total} 个IP的城市信息")
        
        for ip in ip_list:
            try:
                if self.check_city_available(ip):
                    has_city += 1
                    results[ip] = True
                else:
                    results[ip] = False
            except Exception as e:
                log_debug(f"检查IP城市信息失败 {ip}: {e}")
                results[ip] = False
        
        coverage_rate = (has_city / total * 100) if total > 0 else 0
        
        stats = {
            'total_ips': total,
            'has_city': has_city,
            'no_city': total - has_city,
            'coverage_rate': round(coverage_rate, 2),
            'coverage_percentage': f"{coverage_rate:.1f}%",
            'results': results
        }
        
        log_info(f"批量检查完成: {stats['coverage_percentage']} 覆盖率 ({has_city}/{total})")
        return stats
    
    def _is_valid_ip(self, ip):
        """验证IP地址格式"""
        # 移除可能的空格
        ip = ip.strip()
        
        # IPv4模式
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        # IPv6简化模式
        ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){1,7}[0-9a-fA-F]{1,4}$'
        ipv6_compressed_pattern = r'^([0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4})*)?::([0-9a-fA-F]{1,4}(:[0-9a-fA-F]{1,4})*)?$'
        
        if re.match(ipv4_pattern, ip):
            # 验证IPv4各部分在0-255之间
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                try:
                    num = int(part)
                    if not 0 <= num <= 255:
                        return False
                except ValueError:
                    return False
            return True
        elif re.match(ipv6_pattern, ip) or re.match(ipv6_compressed_pattern, ip):
            return True
        return False
    
    def get_database_info(self):
        """获取数据库信息"""
        if self.db_loaded and self.reader:
            try:
                metadata = self.reader.metadata()
                return {
                    'path': self.used_db_path,
                    'database_type': metadata.database_type,
                    'binary_format_major_version': metadata.binary_format_major_version,
                    'binary_format_minor_version': metadata.binary_format_minor_version,
                    'build_epoch': metadata.build_epoch,
                    'build_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(metadata.build_epoch)),
                    'description': metadata.description.get('en', ''),
                    'node_count': metadata.node_count,
                    'record_size': metadata.record_size,
                    'ip_version': metadata.ip_version,
                    'loaded': True
                }
            except Exception as e:
                log_error(f"获取数据库信息失败: {e}")
                return {'loaded': True, 'path': self.used_db_path}
        return {'loaded': False}
    
    def get_stats(self):
        """获取查询统计信息"""
        total = self.stats['total_queries']
        success = self.stats['success_queries']
        city_found = self.stats['city_found_queries']
        
        success_rate = (success / total * 100) if total > 0 else 0
        city_found_rate = (city_found / success * 100) if success > 0 else 0
        
        return {
            **self.stats,
            'success_rate': round(success_rate, 2),
            'city_found_rate': round(city_found_rate, 2),
            'available': self.db_loaded
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_queries': 0,
            'success_queries': 0,
            'city_found_queries': 0,
            'address_not_found': 0,
            'errors': 0
        }
        log_debug("本地查询统计已重置")
    
    def close(self):
        """关闭数据库读取器"""
        if self.reader:
            try:
                self.reader.close()
                self.reader = None
                self.db_loaded = False
                log_debug("本地GeoLite2数据库已关闭")
            except Exception as e:
                log_error(f"关闭数据库失败: {e}")

# 创建全局实例
_local_geoip = None

def get_local_geoip():
    """获取本地GeoLite2查询器实例"""
    global _local_geoip
    if _local_geoip is None:
        _local_geoip = LocalGeoIPQuery()
    return _local_geoip

def query_ip_local(ip, check_city_only=False):
    """
    查询IP地址的地理位置（本地优先）
    
    Args:
        ip: IP地址
        check_city_only: 如果为True，只检查是否有城市名
        
    Returns:
        dict: 地理位置信息，如果本地查询失败返回None
    """
    query = get_local_geoip()
    return query.query_ip(ip, check_city_only)

def check_city_available(ip):
    """
    快速检查IP地址是否有城市信息
    
    Args:
        ip: IP地址
        
    Returns:
        bool: 如果有城市信息返回True，否则返回False
    """
    query = get_local_geoip()
    return query.check_city_available(ip)

def check_multiple_city_available(ip_list):
    """
    批量检查多个IP地址是否有城市信息
    
    Args:
        ip_list: IP地址列表
        
    Returns:
        dict: 统计结果
    """
    query = get_local_geoip()
    return query.check_multiple_city_available(ip_list)

def is_local_db_available():
    """检查本地数据库是否可用"""
    query = get_local_geoip()
    return query.db_loaded

def get_local_db_info():
    """获取本地数据库信息"""
    query = get_local_geoip()
    return query.get_database_info()

def get_local_stats():
    """获取本地查询统计信息"""
    query = get_local_geoip()
    return query.get_stats()

def reset_local_stats():
    """重置本地查询统计"""
    query = get_local_geoip()
    query.reset_stats()

# 程序退出时自动关闭读取器
import atexit

def cleanup():
    """清理资源"""
    global _local_geoip
    if _local_geoip:
        _local_geoip.close()
        _local_geoip = None

atexit.register(cleanup)