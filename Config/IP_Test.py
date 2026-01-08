# Config/IP_Test.py
import random
import time
import threading
from Config.Logger import log_info, log_warning, log_error, log_debug
from Config.Local import (
    query_ip_local, check_city_available, check_multiple_city_available,
    is_local_db_available, get_local_db_info, get_local_stats
)
from Config.IP_API import (
    _ipinfo_io, _ipapi_com, _ipapi_co, _ipwhois, _ipapi_com_line,
    _ipapi_is, _ipbase, _ipregistry, _ipgeolocation_new,
    _ipstack_new, _db_ip_free, _abstractapi, _ipify, _ip2location
)

class GeoLocationQuery:
    """地理位置查询器 - 优先使用本地数据库，智能降级到在线API"""
    
    def __init__(self):
        self.local_available = is_local_db_available()
        self.last_fallback_time = 0
        self.fallback_cooldown = 0.5  # 降级查询冷却时间改为0.5秒，避免阻塞
        self.query_count = 0
        self.local_success_with_city = 0
        self.local_success_without_city = 0
        self.online_success_count = 0
        self.online_failed_count = 0
        self.cache = {}  # 简单缓存，避免重复查询
        self.cache_lock = threading.Lock()
        self.cache_ttl = 3600  # 缓存有效期1小时
        self.online_services_enabled = True  # 是否启用在线服务
        self.stats_lock = threading.Lock()
        self.fallback_cache = {}  # 降级查询缓存，记录哪些IP已经降级过
        
        # 在线服务配置（按优先级）
        self.primary_services = [
            (_ipapi_com, "ip-api.com"),      # 免费，可靠，支持中文
            (_ipinfo_io, "ipinfo.io"),       # 免费，可靠
            (_ipapi_co, "ipapi.co"),         # 免费但有速率限制
        ]
        
        self.secondary_services = [
            (_ipwhois, "ipwhois.io"),        # 免费，可靠
            (_ipapi_com_line, "ip-api.com-line"),  # 轻量快速
            (_ipapi_is, "ipapi.is"),         # 快速可靠
        ]
        
        self.tertiary_services = [
            (_ipbase, "ipbase.com"),
            (_ipregistry, "ipregistry.co"),
            (_ipgeolocation_new, "ipgeolocation.io"),
            (_ipstack_new, "ipstack.com"),
            (_db_ip_free, "db-ip.com"),
            (_abstractapi, "abstractapi.com"),
            (_ipify, "ipify.org"),
            (_ip2location, "ip2location.io"),
        ]
        
        log_info(f"地理位置查询器初始化完成 - 本地数据库: {'可用' if self.local_available else '不可用'}")
        if self.local_available:
            db_info = get_local_db_info()
            if db_info.get('loaded'):
                log_info(f"数据库版本: {db_info.get('database_type', 'Unknown')}")
    
    def query(self, ip, force_online=False, enable_fallback=True):
        """
        查询IP地理位置，优先使用本地数据库
        如果本地数据库没有城市名，则自动降级到在线查询
        
        Args:
            ip: IP地址
            force_online: 强制使用在线查询（跳过本地和缓存）
            enable_fallback: 是否启用降级机制
            
        Returns:
            dict: 地理位置信息，包含source字段标识来源
        """
        with self.stats_lock:
            self.query_count += 1
        
        # 1. 检查缓存
        cache_key = f"geo_{ip}"
        cached_result = self._get_from_cache(cache_key)
        
        if cached_result and not force_online:
            log_debug(f"[{ip}] 使用缓存结果")
            return cached_result
        
        # 2. 首先尝试本地查询（如果可用且未强制在线）
        local_result = None
        local_has_city = False
        
        if self.local_available and not force_online:
            # 执行完整的本地查询
            local_result = query_ip_local(ip)
            
            if local_result:
                # 检查本地查询是否有城市信息
                local_has_city = local_result.get('has_city', False)
                
                if local_has_city:
                    # 本地查询有城市信息
                    with self.stats_lock:
                        self.local_success_with_city += 1
                    
                    log_debug(f"[{ip}] 本地查询成功（有城市信息）: {local_result.get('city')}, {local_result.get('country_code')}")
                    
                    # 缓存结果
                    self._add_to_cache(cache_key, local_result)
                    return local_result
                else:
                    # 本地查询没有城市信息
                    with self.stats_lock:
                        self.local_success_without_city += 1
                    
                    log_info(f"[{ip}] 本地查询完成（无城市信息）: {local_result.get('country_code')}")
                    
                    # 标记本地查询无城市信息
                    local_result['has_city'] = False
                    local_result['accuracy'] = 'low'
            else:
                # 本地查询失败
                log_debug(f"[{ip}] 本地查询失败")
        
        # 3. 检查是否需要降级到在线查询
        need_online_query = False
        
        if force_online:
            need_online_query = True
            log_info(f"[{ip}] 强制在线查询")
        elif enable_fallback and not local_has_city and self.online_services_enabled:
            # 本地查询无城市信息，且启用了降级机制，需要降级到在线查询
            
            # 检查冷却时间
            current_time = time.time()
            if current_time - self.last_fallback_time >= self.fallback_cooldown:
                need_online_query = True
                log_info(f"[{ip}] 本地查询无城市信息，自动降级到在线查询")
            else:
                log_debug(f"[{ip}] 在线查询冷却中，跳过降级")
        
        # 4. 如果需要，执行在线查询
        if need_online_query:
            self.last_fallback_time = time.time()
            
            online_result = self._query_online(ip)
            
            if online_result:
                with self.stats_lock:
                    self.online_success_count += 1
                
                # 合并本地结果（如果有）
                if local_result and not force_online:
                    online_result = self._merge_local_online_results(local_result, online_result)
                
                # 检查在线查询是否有城市信息
                online_has_city = online_result.get('has_city', False)
                
                if online_has_city:
                    log_info(f"[{ip}] 在线查询成功（有城市信息）: {online_result.get('city', 'Unknown')}, {online_result.get('country_code', 'Unknown')}")
                else:
                    log_info(f"[{ip}] 在线查询成功（无城市信息）: {online_result.get('country_code', 'Unknown')}")
                
                # 缓存结果
                self._add_to_cache(cache_key, online_result)
                
                # 记录降级查询
                self.fallback_cache[ip] = True
                
                return online_result
            else:
                with self.stats_lock:
                    self.online_failed_count += 1
                log_warning(f"[{ip}] 在线查询失败")
        
        # 5. 返回本地结果（如果有）或None
        if local_result:
            if local_has_city:
                log_debug(f"[{ip}] 返回本地查询结果（有城市信息）")
            else:
                log_debug(f"[{ip}] 返回本地查询结果（无城市信息）")
            
            # 如果本地没有城市信息且在线查询也失败或被跳过，记录降级状态
            if not local_has_city:
                local_result['online_fallback_attempted'] = need_online_query
                local_result['online_fallback_available'] = self.online_services_enabled
            
            return local_result
        
        log_error(f"[{ip}] 所有地理位置查询都失败")
        return None
    
    def query_with_fallback(self, ip):
        """
        查询IP地理位置，强制启用降级机制
        
        Args:
            ip: IP地址
            
        Returns:
            dict: 地理位置信息
        """
        return self.query(ip, force_online=False, enable_fallback=True)
    
    def query_force_online(self, ip):
        """
        强制使用在线查询
        
        Args:
            ip: IP地址
            
        Returns:
            dict: 地理位置信息
        """
        return self.query(ip, force_online=True, enable_fallback=True)
    
    def _merge_local_online_results(self, local_result, online_result):
        """合并本地和在线查询结果"""
        merged = online_result.copy()
        
        # 优先使用在线查询的城市信息
        if not merged.get('city') and local_result.get('city'):
            merged['city'] = local_result.get('city')
            merged['city_en'] = local_result.get('city_en', local_result.get('city'))
        
        # 如果在线查询没有国家信息，使用本地的
        if not merged.get('country') and local_result.get('country'):
            merged['country'] = local_result.get('country')
        
        if not merged.get('country_code') and local_result.get('country_code'):
            merged['country_code'] = local_result.get('country_code')
        
        # 标记结果来源
        merged['local_combined'] = True
        merged['local_original_has_city'] = local_result.get('has_city', False)
        
        return merged
    
    def _query_online(self, ip):
        """在线API查询（多个服务，按优先级）"""
        
        # 尝试主要服务（随机顺序避免对单一服务的压力）
        services = self.primary_services.copy()
        random.shuffle(services)
        
        for service_func, service_name in services:
            try:
                result = service_func(ip)
                if result and result.get('country_code'):
                    normalized = self._normalize_online_result(result, service_name)
                    if normalized:
                        return normalized
            except Exception as e:
                log_debug(f"在线服务 {service_name} 查询异常: {e}")
                continue
        
        # 尝试次要服务
        services = self.secondary_services.copy()
        random.shuffle(services)
        
        for service_func, service_name in services:
            try:
                result = service_func(ip)
                if result and result.get('country_code'):
                    normalized = self._normalize_online_result(result, service_name)
                    if normalized:
                        return normalized
            except Exception as e:
                log_debug(f"在线服务 {service_name} 查询异常: {e}")
                continue
        
        # 尝试三级服务（允许没有城市信息）
        services = self.tertiary_services.copy()
        random.shuffle(services)
        
        for service_func, service_name in services:
            try:
                result = service_func(ip)
                if result:
                    normalized = self._normalize_online_result(result, service_name)
                    if normalized:
                        return normalized
            except Exception as e:
                log_debug(f"在线服务 {service_name} 查询异常: {e}")
                continue
        
        return None
    
    def _normalize_online_result(self, result, source_name):
        """标准化在线API返回的结果格式"""
        if not result:
            return None
        
        # 提取经纬度并转换为浮点数
        lat = 0.0
        lon = 0.0
        try:
            lat_str = result.get('lat', '0')
            lon_str = result.get('lon', '0')
            lat = float(lat_str) if lat_str else 0.0
            lon = float(lon_str) if lon_str else 0.0
        except (ValueError, TypeError):
            pass
        
        # 获取城市信息
        city = result.get('city', '')
        has_city = bool(city and city.strip())
        
        # 获取ISP信息
        isp = result.get('isp', '')
        if not isp:
            isp = result.get('org', '')
        if not isp:
            isp = result.get('connection', {}).get('isp', '')
        if not isp:
            isp = result.get('connection', {}).get('organization', '')
        
        # 构建标准化结果
        normalized = {
            'ip': result.get('ip', ''),
            'country': result.get('country_name', result.get('country', '')),
            'country_code': result.get('country_code', ''),
            'city': city,
            'city_en': city,  # 在线API通常返回英文
            'region': result.get('region', result.get('region_name', '')),
            'lat': lat,
            'lon': lon,
            'isp': isp,
            'source': result.get('source', source_name),
            'local_query': False,
            'has_city': has_city,
            'accuracy': 'high' if has_city else 'medium'
        }
        
        return normalized
    
    def _get_from_cache(self, key):
        """从缓存获取数据"""
        with self.cache_lock:
            if key in self.cache:
                data, timestamp = self.cache[key]
                if time.time() - timestamp < self.cache_ttl:
                    return data
                else:
                    # 缓存过期
                    del self.cache[key]
        return None
    
    def _add_to_cache(self, key, data):
        """添加数据到缓存"""
        with self.cache_lock:
            self.cache[key] = (data, time.time())
    
    def clear_cache(self):
        """清空缓存"""
        with self.cache_lock:
            self.cache.clear()
        log_debug("地理位置查询缓存已清空")
    
    def enable_online_services(self, enabled=True):
        """启用或禁用在线服务"""
        self.online_services_enabled = enabled
        status = "启用" if enabled else "禁用"
        log_info(f"在线地理位置服务已{status}")
    
    def set_fallback_cooldown(self, seconds):
        """设置降级查询冷却时间"""
        self.fallback_cooldown = seconds
        log_info(f"降级查询冷却时间设置为 {seconds} 秒")
    
    def get_stats(self):
        """获取查询统计信息"""
        with self.stats_lock:
            total = self.query_count
            local_with_city = self.local_success_with_city
            local_without_city = self.local_success_without_city
            online_success = self.online_success_count
            online_failed = self.online_failed_count
            
            local_total = local_with_city + local_without_city
            local_rate = (local_total / total * 100) if total > 0 else 0
            local_city_rate = (local_with_city / local_total * 100) if local_total > 0 else 0
            online_rate = (online_success / total * 100) if total > 0 else 0
            online_success_rate = (online_success / (online_success + online_failed) * 100) if (online_success + online_failed) > 0 else 0
            cache_size = len(self.cache)
            fallback_cache_size = len(self.fallback_cache)
            
            return {
                'total_queries': total,
                'local_with_city': local_with_city,
                'local_without_city': local_without_city,
                'online_success': online_success,
                'online_failed': online_failed,
                'local_success_rate': round(local_rate, 2),
                'local_city_available_rate': round(local_city_rate, 2),
                'online_fallback_rate': round(online_rate, 2),
                'online_success_rate': round(online_success_rate, 2),
                'cache_size': cache_size,
                'fallback_cache_size': fallback_cache_size,
                'local_available': self.local_available,
                'online_enabled': self.online_services_enabled,
                'fallback_cooldown': self.fallback_cooldown
            }
    
    def reset_stats(self):
        """重置统计信息"""
        with self.stats_lock:
            self.query_count = 0
            self.local_success_with_city = 0
            self.local_success_without_city = 0
            self.online_success_count = 0
            self.online_failed_count = 0
        self.fallback_cache.clear()
        log_debug("地理位置查询统计已重置")

# 创建全局查询器实例
_geo_query = None

def get_geo_query():
    """获取地理位置查询器实例"""
    global _geo_query
    if _geo_query is None:
        _geo_query = GeoLocationQuery()
    return _geo_query

def get_ip_location(ip, force_online=False, enable_fallback=True):
    """
    主函数：查询IP地理位置（兼容原有接口）
    智能策略：优先使用本地数据库，如果没有城市信息则自动降级到在线查询
    
    Args:
        ip: IP地址
        force_online: 强制使用在线查询
        enable_fallback: 是否启用降级机制
        
    Returns:
        dict: 地理位置信息
    """
    query = get_geo_query()
    return query.query(ip, force_online, enable_fallback)

def get_ip_location_with_fallback(ip):
    """
    查询IP地理位置，强制启用降级机制
    
    Args:
        ip: IP地址
        
    Returns:
        dict: 地理位置信息
    """
    query = get_geo_query()
    return query.query_with_fallback(ip)

def get_ip_location_force_online(ip):
    """
    强制使用在线查询IP地理位置
    
    Args:
        ip: IP地址
        
    Returns:
        dict: 地理位置信息
    """
    query = get_geo_query()
    return query.query_force_online(ip)

def get_query_stats():
    """获取查询统计信息"""
    if _geo_query:
        return _geo_query.get_stats()
    return None

def clear_geo_cache():
    """清空地理位置查询缓存"""
    if _geo_query:
        _geo_query.clear_cache()

def enable_online_geo_services(enabled=True):
    """启用或禁用在线地理位置服务"""
    query = get_geo_query()
    query.enable_online_services(enabled)

def reset_geo_stats():
    """重置地理位置查询统计"""
    if _geo_query:
        _geo_query.reset_stats()

def check_ip_has_city_local(ip):
    """
    快速检查本地数据库是否有IP的城市信息
    
    Args:
        ip: IP地址
        
    Returns:
        bool: 如果有城市信息返回True，否则返回False
    """
    return check_city_available(ip)

def check_local_city_coverage(ip_list):
    """
    检查本地数据库对IP列表的城市信息覆盖率
    
    Args:
        ip_list: IP地址列表
        
    Returns:
        dict: 覆盖率统计信息
    """
    return check_multiple_city_available(ip_list)

def get_combined_stats():
    """
    获取本地和在线查询的完整统计信息
    
    Returns:
        dict: 完整统计信息
    """
    geo_stats = get_query_stats()
    local_stats = get_local_stats()
    
    combined = {
        'geo_query': geo_stats,
        'local_query': local_stats,
        'summary': {
            'local_available': local_stats.get('available', False),
            'total_queries': geo_stats.get('total_queries', 0) if geo_stats else 0,
            'local_success_rate': geo_stats.get('local_success_rate', 0) if geo_stats else 0,
            'online_fallback_rate': geo_stats.get('online_fallback_rate', 0) if geo_stats else 0,
            'cache_size': geo_stats.get('cache_size', 0) if geo_stats else 0
        }
    }
    
    return combined

def test_fallback_logic(ip):
    """
    测试降级逻辑
    
    Args:
        ip: IP地址
        
    Returns:
        dict: 测试结果
    """
    query = get_geo_query()
    
    # 检查本地是否有城市信息
    local_has_city = check_ip_has_city_local(ip)
    
    # 正常查询
    result = get_ip_location(ip, enable_fallback=True)
    
    test_result = {
        'ip': ip,
        'local_has_city': local_has_city,
        'result_has_city': result.get('has_city', False) if result else False,
        'source': result.get('source', '') if result else '',
        'local_query': result.get('local_query', False) if result else False,
        'city': result.get('city', '') if result else '',
        'country': result.get('country', '') if result else '',
        'online_services_enabled': query.online_services_enabled,
        'fallback_cooldown': query.fallback_cooldown
    }
    
    return test_result