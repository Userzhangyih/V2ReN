# config/IP_test.py
import requests
import random
import time

# 导入日志模块
from config.logger import log_info, log_warning, log_error, log_debug


def _ipinfo_io(ip):
    """使用 ipinfo.io 查询IP地理位置"""
    try:
        response = requests.get(f'https://ipinfo.io/{ip}/json', timeout=10)
        data = response.json()
        
        if data.get('country'):
            # 解析经纬度
            loc = data.get('loc', '').split(',')
            lat = loc[0] if len(loc) > 0 else ''
            lon = loc[1] if len(loc) > 1 else ''
            
            return {
                'ip': ip,
                'country_code': data.get('country', ''),
                'country_name': data.get('country', ''),
                'city': data.get('city', ''),
                'region': data.get('region', ''),
                'isp': data.get('org', ''),
                'lat': lat,
                'lon': lon
            }
        else:
            log_warning("ipinfo.io查询失败")
            
    except Exception as e:
        log_error(f"ipinfo.io地理位置查询错误: {e}")
    return None


def _ipapi_co(ip):
    """使用 ipapi.co 查询IP地理位置"""
    try:
        # 尝试使用 ipapi.co 作为主要服务
        response = requests.get(f'http://ipapi.co/{ip}/json/', timeout=10)
        data = response.json()

        if data.get('error') is None:
            return {
                'ip': ip,
                'country_code': data.get('country_code', ''),
                'country_name': data.get('country_name', ''),
                'city': data.get('city', ''),
                'region': data.get('region', ''),
                'isp': data.get('org', ''),
                'lat': data.get('latitude', ''),
                'lon': data.get('longitude', '')
            }
        else:
            log_warning(f"ipapi.co查询失败: {data.get('reason', '未知错误')}")

    except Exception as e:
        log_error(f"ipapi.co地理位置查询错误: {e}")
    return None


def _ipapi_com(ip):
    """使用 ip-api.com 查询IP地理位置"""
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=10)
        data = response.json()

        if data.get('status') == 'success':
            return {
                'ip': ip,
                'country_code': data.get('countryCode', ''),
                'country_name': data.get('country', ''),
                'city': data.get('city', ''),
                'region': data.get('regionName', ''),
                'isp': data.get('isp', ''),
                'lat': data.get('lat', ''),
                'lon': data.get('lon', '')
            }
        else:
            log_warning(f"ip-api.com查询失败: {data.get('message', '未知错误')}")

    except Exception as e:
        log_error(f"ip-api.com地理位置查询错误: {e}")
    return None


def _ip_sb(ip):
    """使用 ip.sb 查询IP地理位置"""
    try:
        response = requests.get(f'https://api.ip.sb/geoip/{ip}', timeout=10)
        data = response.json()

        if data.get('country_code'):
            return {
                'ip': ip,
                'country_code': data.get('country_code', ''),
                'country_name': data.get('country', ''),
                'city': data.get('city', ''),
                'region': data.get('region', ''),
                'isp': data.get('isp', ''),
                'lat': data.get('latitude', ''),
                'lon': data.get('longitude', '')
            }
        else:
            log_warning("ip.sb查询失败")

    except Exception as e:
        log_error(f"ip.sb地理位置查询错误: {e}")
    return None


def _ipwhois(ip):
    """使用 ipwhois 查询IP地理位置"""
    try:
        response = requests.get(f'http://ipwhois.app/json/{ip}', timeout=10)
        data = response.json()

        if data.get('success') is True:
            return {
                'ip': ip,
                'country_code': data.get('country_code', ''),
                'country_name': data.get('country', ''),
                'city': data.get('city', ''),
                'region': data.get('region', ''),
                'isp': data.get('isp', ''),
                'lat': data.get('latitude', ''),
                'lon': data.get('longitude', '')
            }
        else:
            log_warning("ipwhois查询失败")

    except Exception as e:
        log_error(f"ipwhois地理位置查询错误: {e}")
    return None


def _ipgeolocation(ip):
    """使用 ipgeolocation.io 查询IP地理位置"""
    try:
        response = requests.get(f'https://api.ipgeolocation.io/ipgeo?ip={ip}', timeout=10)
        data = response.json()

        if data.get('country_code2'):
            return {
                'ip': ip,
                'country_code': data.get('country_code2', ''),
                'country_name': data.get('country_name', ''),
                'city': data.get('city', ''),
                'region': data.get('state_prov', ''),
                'isp': data.get('isp', ''),
                'lat': data.get('latitude', ''),
                'lon': data.get('longitude', '')
            }
        else:
            log_warning("ipgeolocation查询失败")

    except Exception as e:
        log_error(f"ipgeolocation地理位置查询错误: {e}")
    return None


def _freegeoip(ip):
    """使用 freegeoip.app 查询IP地理位置"""
    try:
        response = requests.get(f'https://freegeoip.app/json/{ip}', timeout=10)
        data = response.json()

        if data.get('country_code'):
            return {
                'ip': ip,
                'country_code': data.get('country_code', ''),
                'country_name': data.get('country_name', ''),
                'city': data.get('city', ''),
                'region': data.get('region_name', ''),
                'isp': data.get('', ''),  # 这个服务不提供ISP
                'lat': data.get('latitude', ''),
                'lon': data.get('longitude', '')
            }
        else:
            log_warning("freegeoip查询失败")

    except Exception as e:
        log_error(f"freegeoip地理位置查询错误: {e}")
    return None


def _extreme_ip_lookup(ip):
    """使用 extreme-ip-lookup 查询IP地理位置"""
    try:
        response = requests.get(f'https://extreme-ip-lookup.com/json/{ip}', timeout=10)
        data = response.json()

        if data.get('countryCode'):
            return {
                'ip': ip,
                'country_code': data.get('countryCode', ''),
                'country_name': data.get('country', ''),
                'city': data.get('city', ''),
                'region': data.get('region', ''),
                'isp': data.get('isp', ''),
                'lat': data.get('lat', ''),
                'lon': data.get('lon', '')
            }
        else:
            log_warning("extreme-ip-lookup查询失败")

    except Exception as e:
        log_error(f"extreme-ip-lookup地理位置查询错误: {e}")
    return None


def _ipapi_com_line(ip):
    """使用 ip-api.com line格式查询IP地理位置"""
    try:
        response = requests.get(f'http://ip-api.com/line/{ip}?fields=countryCode,country,city,regionName,isp', timeout=10)
        lines = response.text.strip().split('\n')
        
        if len(lines) >= 5 and lines[0] != 'fail':
            return {
                'ip': ip,
                'country_code': lines[0],
                'country_name': lines[1],
                'city': lines[2],
                'region': lines[3],
                'isp': lines[4] if len(lines) > 4 else ''
            }
        else:
            log_warning("ip-api.com line查询失败")

    except Exception as e:
        log_error(f"ip-api.com line地理位置查询错误: {e}")
    return None


def _db_ip(ip):
    """使用 db-ip 查询IP地理位置"""
    try:
        response = requests.get(f'https://api.db-ip.com/v2/free/{ip}', timeout=10)
        data = response.json()

        if data.get('countryCode'):
            return {
                'ip': ip,
                'country_code': data.get('countryCode', ''),
                'country_name': data.get('countryName', ''),
                'city': data.get('city', ''),
                'region': data.get('stateProv', ''),
                'isp': data.get('', ''),
                'lat': data.get('', ''),
                'lon': data.get('', '')
            }
        else:
            log_warning("db-ip查询失败")

    except Exception as e:
        log_error(f"db-ip地理位置查询错误: {e}")
    return None


def _ipstack(ip):
    """使用 ipstack 查询IP地理位置"""
    try:
        # 注意：ipstack需要API密钥，这里使用免费版（有限制）
        response = requests.get(f'http://api.ipstack.com/{ip}?access_key=demo', timeout=10)
        data = response.json()

        if data.get('country_code'):
            return {
                'ip': ip,
                'country_code': data.get('country_code', ''),
                'country_name': data.get('country_name', ''),
                'city': data.get('city', ''),
                'region': data.get('region_name', ''),
                'isp': data.get('', ''),
                'lat': data.get('latitude', ''),
                'lon': data.get('longitude', '')
            }
        else:
            log_warning("ipstack查询失败")

    except Exception as e:
        log_error(f"ipstack地理位置查询错误: {e}")
    return None


def _ipapi_com_json(ip):
    """使用 ipapi.com json格式查询IP地理位置"""
    try:
        response = requests.get(f'https://ipapi.com/ip_api.php?ip={ip}', timeout=10)
        data = response.json()

        if data.get('country_code'):
            return {
                'ip': ip,
                'country_code': data.get('country_code', ''),
                'country_name': data.get('country_name', ''),
                'city': data.get('city', ''),
                'region': data.get('region_name', ''),
                'isp': data.get('isp', ''),
                'lat': data.get('latitude', ''),
                'lon': data.get('longitude', '')
            }
        else:
            log_warning("ipapi.com查询失败")

    except Exception as e:
        log_error(f"ipapi.com地理位置查询错误: {e}")
    return None


def get_ip_location(ip):
    """
    使用多个服务查询IP地理位置，优先使用城市信息完整的服务
    
    Args:
        ip: IP地址
        
    Returns:
        dict: 地理位置信息字典
    """
    # 城市信息完整的服务（优先）
    reliable_services = [
        _ipapi_co,  
        _ipinfo_io,
        _ipapi_com,
        _ip_sb,
        _ipwhois,
        _ipgeolocation,
        _extreme_ip_lookup,
        _ipapi_com_json
    ]
    
    # 城市信息可能不完整的服务（备用）
    fallback_services = [
        _freegeoip,
        _ipapi_com_line,
        _db_ip,
        _ipstack
    ]
    
    # 先尝试可靠的服务
    random.shuffle(reliable_services)
    for query_func in reliable_services:
        try:
            result = query_func(ip)
            if result and result.get('city'):  # 确保有城市信息
                log_debug(f"使用 {query_func.__name__} 查询成功，获得城市信息: {result['city']}")
                return result
        except Exception as e:
            log_debug(f"{query_func.__name__} 查询异常: {e}")
            continue
    
    # 如果可靠服务都没有城市信息，尝试备用服务
    random.shuffle(fallback_services)
    for query_func in fallback_services:
        try:
            result = query_func(ip)
            if result:
                log_debug(f"使用备用服务 {query_func.__name__} 查询成功")
                return result
        except Exception as e:
            log_debug(f"{query_func.__name__} 查询异常: {e}")
            continue
    
    log_warning("所有IP地理位置查询服务都失败了")
    return None


# 缓存功能
class IPLocationCache:
    """IP地理位置缓存类"""
    
    def __init__(self):
        self.cache = {}
        self.timeout = 3600  # 1小时缓存
    
    def get(self, ip):
        """从缓存获取IP地理位置信息"""
        if ip in self.cache:
            cache_time, data = self.cache[ip]
            if time.time() - cache_time < self.timeout:
                log_debug(f"缓存命中: {ip}")
                return data
            else:
                # 缓存过期，删除
                del self.cache[ip]
        return None
    
    def set(self, ip, data):
        """将IP地理位置信息存入缓存"""
        self.cache[ip] = (time.time(), data)
        log_debug(f"缓存已更新: {ip}")
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        log_debug("IP缓存已清空")


# 创建全局缓存实例
ip_cache = IPLocationCache()


def get_ip_location_with_cache(ip):
    """
    带缓存的IP地理位置查询
    
    Args:
        ip: IP地址
        
    Returns:
        dict: 地理位置信息字典
    """
    # 检查缓存
    cached_result = ip_cache.get(ip)
    if cached_result:
        return cached_result
    
    # 查询新数据
    result = get_ip_location(ip)
    if result:
        ip_cache.set(ip, result)
    
    return result


def clear_ip_cache():
    """清空IP缓存"""
    ip_cache.clear()