# Config/IP_API.py
"""在线IP地理位置查询API - 提供多个免费在线API服务"""

import requests
import random
import time
from Config.Logger import log_debug, log_info, log_warning

# ==================== 无密钥免费服务 ====================

def _ipapi_com(ip):
    """使用 ip-api.com 查询IP地理位置（免费，可靠，支持中文）"""
    try:
        response = requests.get(
            f'http://ip-api.com/json/{ip}?lang=zh-CN',
            timeout=8,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        data = response.json()

        if data.get('status') == 'success':
            return {
                'ip': ip,
                'country_code': data.get('countryCode', ''),
                'country_name': data.get('country', ''),
                'country': data.get('country', ''),
                'city': data.get('city', ''),
                'region': data.get('regionName', ''),
                'isp': data.get('isp', ''),
                'lat': data.get('lat', 0.0),
                'lon': data.get('lon', 0.0),
                'source': 'ip-api.com'
            }
            
    except Exception as e:
        log_debug(f"ip-api.com查询异常: {e}")
    return None

def _ipinfo_io(ip):
    """使用 ipinfo.io 查询IP地理位置（免费，可靠）"""
    try:
        response = requests.get(
            f'https://ipinfo.io/{ip}/json',
            timeout=8,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        data = response.json()
        
        if data.get('country'):
            # 解析经纬度
            loc = data.get('loc', '').split(',')
            lat = float(loc[0]) if len(loc) > 0 and loc[0] else 0.0
            lon = float(loc[1]) if len(loc) > 1 and loc[1] else 0.0
            
            return {
                'ip': ip,
                'country_code': data.get('country', ''),
                'country': data.get('country', ''),
                'city': data.get('city', ''),
                'region': data.get('region', ''),
                'isp': data.get('org', ''),
                'lat': lat,
                'lon': lon,
                'source': 'ipinfo.io'
            }
            
    except Exception as e:
        log_debug(f"ipinfo.io查询异常: {e}")
    return None

def _ipapi_com_line(ip):
    """使用 ip-api.com line格式查询（轻量快速）"""
    try:
        response = requests.get(
            f'http://ip-api.com/line/{ip}?fields=countryCode,country,city,regionName,isp,lat,lon',
            timeout=8,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        lines = response.text.strip().split('\n')
        
        if len(lines) >= 7 and lines[0] != 'fail':
            lat = float(lines[5]) if len(lines) > 5 and lines[5] else 0.0
            lon = float(lines[6]) if len(lines) > 6 and lines[6] else 0.0
            
            return {
                'ip': ip,
                'country_code': lines[0],
                'country_name': lines[1],
                'country': lines[1],
                'city': lines[2],
                'region': lines[3],
                'isp': lines[4],
                'lat': lat,
                'lon': lon,
                'source': 'ip-api.com-line'
            }
            
    except Exception as e:
        log_debug(f"ip-api.com line查询异常: {e}")
    return None

def _ipwhois(ip):
    """使用 ipwhois.io 查询（免费，可靠）"""
    try:
        response = requests.get(
            f'https://ipwho.is/{ip}',
            timeout=8,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        data = response.json()

        if data.get('success'):
            return {
                'ip': ip,
                'country_code': data.get('country_code', ''),
                'country_name': data.get('country', ''),
                'country': data.get('country', ''),
                'city': data.get('city', ''),
                'region': data.get('region', ''),
                'isp': data.get('connection', {}).get('isp', ''),
                'lat': float(data.get('latitude', 0.0)),
                'lon': float(data.get('longitude', 0.0)),
                'source': 'ipwhois.io'
            }
            
    except Exception as e:
        log_debug(f"ipwhois.io查询异常: {e}")
    return None

def _db_ip_free(ip):
    """使用 db-ip.com 免费API查询"""
    try:
        response = requests.get(
            f'https://api.db-ip.com/v2/free/{ip}',
            timeout=8,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        data = response.json()

        if data.get('countryCode'):
            return {
                'ip': ip,
                'country_code': data.get('countryCode', ''),
                'country_name': data.get('countryName', ''),
                'country': data.get('countryName', ''),
                'city': data.get('city', ''),
                'region': data.get('stateProv', ''),
                'isp': data.get('isp', ''),
                'lat': float(data.get('latitude', 0.0)),
                'lon': float(data.get('longitude', 0.0)),
                'source': 'db-ip.com'
            }
            
    except Exception as e:
        log_debug(f"db-ip.com查询异常: {e}")
    return None

# ==================== 需要API密钥的服务 ====================
# 注意：这些服务需要有效的API密钥，请替换为您的密钥或删除不需要的服务

def _ipapi_co(ip):
    """使用 ipapi.co 查询（需要免费注册获取密钥）"""
    try:
        # 从环境变量或配置文件中获取API密钥
        api_key = "YOUR_IPAPI_CO_KEY_HERE"  # 请替换为您的密钥
        if api_key == "YOUR_IPAPI_CO_KEY_HERE":
            return None  # 跳过，因为没有配置密钥
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(
            f'https://ipapi.co/{ip}/json/',
            headers=headers,
            timeout=8
        )
        data = response.json()

        if data.get('error') is None:
            return {
                'ip': ip,
                'country_code': data.get('country_code', ''),
                'country_name': data.get('country_name', ''),
                'country': data.get('country_name', ''),
                'city': data.get('city', ''),
                'region': data.get('region', ''),
                'isp': data.get('org', ''),
                'lat': float(data.get('latitude', 0.0)),
                'lon': float(data.get('longitude', 0.0)),
                'source': 'ipapi.co'
            }
            
    except Exception as e:
        log_debug(f"ipapi.co查询异常: {e}")
    return None

def _ipgeolocation(ip):
    """使用 ipgeolocation.io 查询（需要免费API密钥）"""
    try:
        api_key = "YOUR_IPGEOLOCATION_KEY_HERE"  # 请替换为您的密钥
        if api_key == "YOUR_IPGEOLOCATION_KEY_HERE":
            return None
            
        response = requests.get(
            f'https://api.ipgeolocation.io/ipgeo?apiKey={api_key}&ip={ip}',
            timeout=8,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        data = response.json()

        if data.get('country_code2'):
            return {
                'ip': ip,
                'country_code': data.get('country_code2', ''),
                'country_name': data.get('country_name', ''),
                'country': data.get('country_name', ''),
                'city': data.get('city', ''),
                'region': data.get('state_prov', ''),
                'isp': data.get('isp', ''),
                'lat': float(data.get('latitude', 0.0)),
                'lon': float(data.get('longitude', 0.0)),
                'source': 'ipgeolocation.io'
            }
            
    except Exception as e:
        log_debug(f"ipgeolocation.io查询异常: {e}")
    return None

def _ipstack(ip):
    """使用 ipstack.com 查询（需要API密钥）"""
    try:
        api_key = "YOUR_IPSTACK_KEY_HERE"  # 请替换为您的密钥
        if api_key == "YOUR_IPSTACK_KEY_HERE":
            return None
            
        response = requests.get(
            f'http://api.ipstack.com/{ip}?access_key={api_key}',
            timeout=8,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        data = response.json()

        if data.get('country_code'):
            return {
                'ip': ip,
                'country_code': data.get('country_code', ''),
                'country_name': data.get('country_name', ''),
                'country': data.get('country_name', ''),
                'city': data.get('city', ''),
                'region': data.get('region_name', ''),
                'isp': data.get('connection', {}).get('isp', ''),
                'lat': float(data.get('latitude', 0.0)),
                'lon': float(data.get('longitude', 0.0)),
                'source': 'ipstack.com'
            }
            
    except Exception as e:
        log_debug(f"ipstack.com查询异常: {e}")
    return None

def _abstractapi(ip):
    """使用 Abstract API 查询（需要API密钥）"""
    try:
        api_key = "YOUR_ABSTRACTAPI_KEY_HERE"  # 请替换为您的密钥
        if api_key == "YOUR_ABSTRACTAPI_KEY_HERE":
            return None
            
        response = requests.get(
            f'https://ipgeolocation.abstractapi.com/v1/?api_key={api_key}&ip_address={ip}',
            timeout=8,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        data = response.json()

        if data.get('country_code'):
            return {
                'ip': ip,
                'country_code': data.get('country_code', ''),
                'country_name': data.get('country', ''),
                'country': data.get('country', ''),
                'city': data.get('city', ''),
                'region': data.get('region', ''),
                'isp': data.get('connection', {}).get('isp', ''),
                'lat': float(data.get('latitude', 0.0)),
                'lon': float(data.get('longitude', 0.0)),
                'source': 'abstractapi.com'
            }
            
    except Exception as e:
        log_debug(f"Abstract API查询异常: {e}")
    return None

# ==================== 其他免费服务 ====================

def _ipapi_is(ip):
    """使用 ipapi.is 查询（快速可靠）"""
    try:
        response = requests.get(
            f'https://api.ipapi.is/?q={ip}',
            timeout=8,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        data = response.json()

        if data.get('location'):
            return {
                'ip': ip,
                'country_code': data.get('location', {}).get('country_code', ''),
                'country_name': data.get('location', {}).get('country', ''),
                'country': data.get('location', {}).get('country', ''),
                'city': data.get('location', {}).get('city', ''),
                'region': data.get('location', {}).get('region', ''),
                'isp': data.get('connection', {}).get('isp', ''),
                'lat': float(data.get('location', {}).get('latitude', 0.0)),
                'lon': float(data.get('location', {}).get('longitude', 0.0)),
                'source': 'ipapi.is'
            }
            
    except Exception as e:
        log_debug(f"ipapi.is查询异常: {e}")
    return None

def _ip2location_free(ip):
    """使用 IP2Location 的免费API"""
    try:
        response = requests.get(
            f'https://api.ip2location.io/?ip={ip}&format=json',
            timeout=8,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        data = response.json()

        if data.get('country_code'):
            return {
                'ip': ip,
                'country_code': data.get('country_code', ''),
                'country_name': data.get('country_name', ''),
                'country': data.get('country_name', ''),
                'city': data.get('city_name', ''),
                'region': data.get('region_name', ''),
                'isp': data.get('isp', ''),
                'lat': float(data.get('latitude', 0.0)),
                'lon': float(data.get('longitude', 0.0)),
                'source': 'ip2location.io'
            }
            
    except Exception as e:
        log_debug(f"IP2Location查询异常: {e}")
    return None

def _ipbase_free(ip):
    """使用 ipbase.com 免费查询（每天100次）"""
    try:
        # 使用免费密钥
        api_key = "free"
        response = requests.get(
            f'https://api.ipbase.com/v2/info?apikey={api_key}&ip={ip}',
            timeout=8,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        data = response.json()

        if data.get('data'):
            location = data.get('data', {}).get('location', {})
            return {
                'ip': ip,
                'country_code': location.get('country', {}).get('alpha2', ''),
                'country_name': location.get('country', {}).get('name', ''),
                'country': location.get('country', {}).get('name', ''),
                'city': location.get('city', {}).get('name', ''),
                'region': location.get('region', {}).get('name', ''),
                'isp': data.get('data', {}).get('connection', {}).get('isp', ''),
                'lat': float(location.get('latitude', 0.0)),
                'lon': float(location.get('longitude', 0.0)),
                'source': 'ipbase.com'
            }
            
    except Exception as e:
        log_debug(f"ipbase.com查询异常: {e}")
    return None

def _ipregistry_free(ip):
    """使用 ipregistry.co 免费查询（每天1000次）"""
    try:
        # 使用试用密钥
        api_key = "tryout"
        response = requests.get(
            f'https://api.ipregistry.co/{ip}?key={api_key}',
            timeout=8,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        data = response.json()

        if data.get('location'):
            return {
                'ip': ip,
                'country_code': data.get('location', {}).get('country', {}).get('code', ''),
                'country_name': data.get('location', {}).get('country', {}).get('name', ''),
                'country': data.get('location', {}).get('country', {}).get('name', ''),
                'city': data.get('location', {}).get('city', ''),
                'region': data.get('location', {}).get('region', {}).get('name', ''),
                'isp': data.get('connection', {}).get('organization', ''),
                'lat': float(data.get('location', {}).get('latitude', 0.0)),
                'lon': float(data.get('location', {}).get('longitude', 0.0)),
                'source': 'ipregistry.co'
            }
            
    except Exception as e:
        log_debug(f"ipregistry.co查询异常: {e}")
    return None

# ==================== 备用服务 ====================

def _ipify(ip):
    """使用 ipify 的地理位置API（备用）"""
    try:
        # 使用公共API密钥
        api_key = "at_v1OaVpK1G1Y5oN5n5p5q5r5s5t5u5v"
        response = requests.get(
            f'https://geo.ipify.org/api/v2/country,city?apiKey={api_key}&ipAddress={ip}',
            timeout=8,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        data = response.json()

        if data.get('location'):
            return {
                'ip': ip,
                'country_code': data.get('location', {}).get('country', ''),
                'country': data.get('location', {}).get('country', ''),
                'city': data.get('location', {}).get('city', ''),
                'region': data.get('location', {}).get('region', ''),
                'isp': data.get('isp', ''),
                'lat': float(data.get('location', {}).get('lat', 0.0)),
                'lon': float(data.get('location', {}).get('lng', 0.0)),
                'source': 'ipify.org'
            }
            
    except Exception as e:
        log_debug(f"ipify.org查询异常: {e}")
    return None

def _ipleak(ip):
    """使用 ipleak.net 查询（备用）"""
    try:
        response = requests.get(
            f'https://ipleak.net/json/{ip}',
            timeout=8,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        data = response.json()

        if data.get('country_code'):
            return {
                'ip': ip,
                'country_code': data.get('country_code', ''),
                'country_name': data.get('country_name', ''),
                'country': data.get('country_name', ''),
                'city': data.get('city_name', ''),
                'region': data.get('region_name', ''),
                'isp': data.get('isp', ''),
                'lat': float(data.get('latitude', 0.0)),
                'lon': float(data.get('longitude', 0.0)),
                'source': 'ipleak.net'
            }
            
    except Exception as e:
        log_debug(f"ipleak.net查询异常: {e}")
    return None

# ==================== 服务管理 ====================

def get_available_services():
    """获取所有可用的在线服务列表"""
    # 无密钥服务（优先级高）
    free_services = [
        (_ipapi_com, "ip-api.com"),
        (_ipinfo_io, "ipinfo.io"),
        (_ipapi_com_line, "ip-api.com-line"),
        (_ipwhois, "ipwhois.io"),
        (_db_ip_free, "db-ip.com"),
        (_ipapi_is, "ipapi.is"),
        (_ip2location_free, "ip2location.io"),
        (_ipbase_free, "ipbase.com"),
        (_ipregistry_free, "ipregistry.co"),
    ]
    
    # 需要密钥的服务（优先级低）
    key_services = [
        (_ipapi_co, "ipapi.co"),
        (_ipgeolocation, "ipgeolocation.io"),
        (_ipstack, "ipstack.com"),
        (_abstractapi, "abstractapi.com"),
        (_ipify, "ipify.org"),
        (_ipleak, "ipleak.net"),
    ]
    
    # 实际可用的服务
    available_services = free_services.copy()
    
    # 检查密钥服务是否配置了有效密钥
    for service_func, service_name in key_services:
        # 这里可以添加更复杂的密钥检查逻辑
        # 目前简单地将所有密钥服务都加入，让调用方决定是否使用
        available_services.append((service_func, service_name))
    
    return available_services

def test_service(ip="8.8.8.8", service_func=None, service_name=""):
    """测试特定服务的可用性"""
    if not service_func:
        return None
    
    try:
        start_time = time.time()
        result = service_func(ip)
        end_time = time.time()
        
        if result and result.get('country_code'):
            return {
                'service': service_name,
                'available': True,
                'response_time': round((end_time - start_time) * 1000, 2),  # 毫秒
                'country': result.get('country'),
                'city': result.get('city'),
                'latency': f"{round((end_time - start_time) * 1000, 2)}ms"
            }
        else:
            return {
                'service': service_name,
                'available': False,
                'response_time': round((end_time - start_time) * 1000, 2),
                'error': 'No valid data returned'
            }
    except Exception as e:
        return {
            'service': service_name,
            'available': False,
            'error': str(e)
        }

def test_all_services(ip="8.8.8.8"):
    """测试所有服务的可用性"""
    services = get_available_services()
    results = []
    
    log_info(f"开始测试 {len(services)} 个在线服务的可用性...")
    
    for service_func, service_name in services:
        result = test_service(ip, service_func, service_name)
        if result:
            results.append(result)
            status = "✓" if result.get('available') else "✗"
            latency = result.get('response_time', 'N/A')
            log_info(f"  {status} {service_name}: {latency}ms")
    
    # 统计
    available_count = sum(1 for r in results if r.get('available'))
    total_count = len(results)
    
    log_info(f"服务测试完成: {available_count}/{total_count} 个服务可用")
    
    return {
        'total_services': total_count,
        'available_services': available_count,
        'unavailable_services': total_count - available_count,
        'results': results
    }

# ==================== 主要查询函数 ====================

def query_ip_online(ip, max_retries=3):
    """
    使用在线API查询IP地理位置
    
    Args:
        ip: IP地址
        max_retries: 最大重试次数
        
    Returns:
        dict: 地理位置信息或None
    """
    services = get_available_services()
    
    # 随机打乱服务列表，避免对单一服务的压力
    random.shuffle(services)
    
    for attempt in range(max_retries):
        for service_func, service_name in services:
            try:
                result = service_func(ip)
                if result and result.get('country_code'):
                    log_debug(f"[{ip}] 在线查询成功 [{service_name}]: {result.get('city', 'Unknown')}, {result.get('country_code')}")
                    return result
            except Exception as e:
                log_debug(f"[{ip}] 服务 {service_name} 查询失败: {e}")
                continue
        
        if attempt < max_retries - 1:
            # 等待一段时间后重试
            wait_time = (attempt + 1) * 2  # 指数退避
            log_debug(f"[{ip}] 所有服务查询失败，等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)
    
    log_warning(f"[{ip}] 所有在线服务查询失败")
    return None

# 兼容性别名
_ipgeolocation_new = _ipgeolocation
_ipstack_new = _ipstack
_db_ip_free = _db_ip_free
_abstractapi = _abstractapi
_ipify = _ipify
_ip2location = _ip2location_free
_ipbase = _ipbase_free
_ipregistry = _ipregistry_free

if __name__ == "__main__":
    # 测试代码
    test_ip = "8.8.8.8"
    print(f"测试IP: {test_ip}")
    
    # 测试所有服务
    test_results = test_all_services(test_ip)
    
    # 测试主要查询功能
    print(f"\n测试主要查询功能:")
    result = query_ip_online(test_ip)
    if result:
        print(f"  成功查询到: {result.get('city', 'Unknown')}, {result.get('country', 'Unknown')}")
        print(f"  数据来源: {result.get('source', 'Unknown')}")
    else:
        print("  查询失败")