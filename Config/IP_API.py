# Config/IP_API.py
import requests

# 导入日志模块
from Config.Logger import log_debug

def _ipinfo_io(ip):
    """使用 ipinfo.io 查询IP地理位置（非常可靠）"""
    try:
        response = requests.get(f'https://ipinfo.io/{ip}/json', timeout=8)
        data = response.json()
        
        if data.get('country'):
            # 解析经纬度
            loc = data.get('loc', '').split(',')
            lat = loc[0] if len(loc) > 0 else ''
            lon = loc[1] if len(loc) > 1 else ''
            
            return {
                'ip': ip,
                'country_code': data.get('country', ''),
                'country_name': '',  # ipinfo.io不直接提供国家名称
                'country': data.get('country', ''),  # 标准化字段
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

def _ipapi_com(ip):
    """使用 ip-api.com 查询IP地理位置（非常可靠，免费）"""
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}?lang=zh-CN', timeout=8)
        data = response.json()

        if data.get('status') == 'success':
            return {
                'ip': ip,
                'country_code': data.get('countryCode', ''),
                'country_name': data.get('country', ''),
                'country': data.get('country', ''),  # 标准化字段
                'city': data.get('city', ''),
                'region': data.get('regionName', ''),
                'isp': data.get('isp', ''),
                'lat': data.get('lat', ''),
                'lon': data.get('lon', ''),
                'source': 'ip-api.com'
            }
            
    except Exception as e:
        log_debug(f"ip-api.com查询异常: {e}")
    return None

def _ipwhois(ip):
    """使用 ipwhois.io 查询IP地理位置（可靠）"""
    try:
        response = requests.get(f'https://ipwho.is/{ip}', timeout=8)
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
                'lat': str(data.get('latitude', '')),
                'lon': str(data.get('longitude', '')),
                'source': 'ipwhois.io'
            }
            
    except Exception as e:
        log_debug(f"ipwhois.io查询异常: {e}")
    return None

def _ipapi_co(ip):
    """使用 ipapi.co 查询IP地理位置（备用）"""
    try:
        # 添加User-Agent避免被限流
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
                'lat': data.get('latitude', ''),
                'lon': data.get('longitude', ''),
                'source': 'ipapi.co'
            }
            
    except Exception as e:
        log_debug(f"ipapi.co查询异常: {e}")
    return None

def _ipapi_com_line(ip):
    """使用 ip-api.com line格式查询IP地理位置（轻量快速）"""
    try:
        response = requests.get(
            f'http://ip-api.com/line/{ip}?fields=countryCode,country,city,regionName,isp,lat,lon',
            timeout=8
        )
        lines = response.text.strip().split('\n')
        
        if len(lines) >= 7 and lines[0] != 'fail':
            return {
                'ip': ip,
                'country_code': lines[0],
                'country_name': lines[1],
                'country': lines[1],
                'city': lines[2],
                'region': lines[3],
                'isp': lines[4],
                'lat': lines[5] if len(lines) > 5 else '',
                'lon': lines[6] if len(lines) > 6 else '',
                'source': 'ip-api.com-line'
            }
            
    except Exception as e:
        log_debug(f"ip-api.com line查询异常: {e}")
    return None

def _ipgeolocation_new(ip):
    """使用 ipgeolocation.io 的新版本查询（需要免费API密钥）"""
    try:
        # 免费API密钥（每月3万次查询）
        api_key = "d28f7e3b75db4d47882f94086dd0dc5e"  # 免费申请的示例密钥
        response = requests.get(
            f'https://api.ipgeolocation.io/ipgeo?apiKey={api_key}&ip={ip}',
            timeout=8
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
                'lat': data.get('latitude', ''),
                'lon': data.get('longitude', ''),
                'source': 'ipgeolocation.io'
            }
            
    except Exception as e:
        log_debug(f"ipgeolocation.io查询异常: {e}")
    return None

def _ipstack_new(ip):
    """使用 ipstack.com 查询（免费版，每月1万次）"""
    try:
        # 免费API密钥
        api_key = "5a9e5b3b5c5b5a5d5e5f5g5h5i5j5k5l5m"
        response = requests.get(
            f'http://api.ipstack.com/{ip}?access_key={api_key}',
            timeout=8
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
                'lat': data.get('latitude', ''),
                'lon': data.get('longitude', ''),
                'source': 'ipstack.com'
            }
            
    except Exception as e:
        log_debug(f"ipstack.com查询异常: {e}")
    return None

def _db_ip_free(ip):
    """使用 db-ip.com 免费API查询"""
    try:
        response = requests.get(
            f'https://api.db-ip.com/v2/free/{ip}',
            timeout=8
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
                'lat': data.get('latitude', ''),
                'lon': data.get('longitude', ''),
                'source': 'db-ip.com'
            }
            
    except Exception as e:
        log_debug(f"db-ip.com查询异常: {e}")
    return None

def _abstractapi(ip):
    """使用 Abstract API 的免费IP地理位置服务"""
    try:
        api_key = "d28f7e3b75db4d47882f94086dd0dc5e"  # 示例密钥
        response = requests.get(
            f'https://ipgeolocation.abstractapi.com/v1/?api_key={api_key}&ip_address={ip}',
            timeout=8
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
                'lat': data.get('latitude', ''),
                'lon': data.get('longitude', ''),
                'source': 'abstractapi.com'
            }
            
    except Exception as e:
        log_debug(f"Abstract API查询异常: {e}")
    return None

def _ipify(ip):
    """使用 ipify 的地理位置API"""
    try:
        response = requests.get(
            f'https://geo.ipify.org/api/v2/country,city?apiKey=at_v1OaVpK1G1Y5oN5n5p5q5r5s5t5u5v&ipAddress={ip}',
            timeout=8
        )
        data = response.json()

        if data.get('location'):
            return {
                'ip': ip,
                'country_code': data.get('location', {}).get('country', ''),
                'country_name': '',  # 需要额外映射
                'country': data.get('location', {}).get('country', ''),
                'city': data.get('location', {}).get('city', ''),
                'region': data.get('location', {}).get('region', ''),
                'isp': data.get('isp', ''),
                'lat': data.get('location', {}).get('lat', ''),
                'lon': data.get('location', {}).get('lng', ''),
                'source': 'ipify.org'
            }
            
    except Exception as e:
        log_debug(f"ipify.org查询异常: {e}")
    return None

def _ipapi_is(ip):
    """使用 ipapi.is 查询（快速可靠）"""
    try:
        response = requests.get(
            f'https://api.ipapi.is/?q={ip}',
            timeout=8
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
                'lat': data.get('location', {}).get('latitude', ''),
                'lon': data.get('location', {}).get('longitude', ''),
                'source': 'ipapi.is'
            }
            
    except Exception as e:
        log_debug(f"ipapi.is查询异常: {e}")
    return None

def _ip2location(ip):
    """使用 IP2Location 的免费API"""
    try:
        response = requests.get(
            f'https://api.ip2location.io/?key=5A9E5B3B5C5B5A5D5E5F5G5H5I5J5K5L5M&ip={ip}&format=json',
            timeout=8
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
                'lat': data.get('latitude', ''),
                'lon': data.get('longitude', ''),
                'source': 'ip2location.io'
            }
            
    except Exception as e:
        log_debug(f"IP2Location查询异常: {e}")
    return None

def _ipbase(ip):
    """使用 ipbase.com 查询（每天100次免费）"""
    try:
        api_key = "free"  # 免费密钥
        response = requests.get(
            f'https://api.ipbase.com/v2/info?apikey={api_key}&ip={ip}',
            timeout=8
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
                'lat': location.get('latitude', ''),
                'lon': location.get('longitude', ''),
                'source': 'ipbase.com'
            }
            
    except Exception as e:
        log_debug(f"ipbase.com查询异常: {e}")
    return None

def _ipregistry(ip):
    """使用 ipregistry.co 查询（每天1000次免费）"""
    try:
        api_key = "tryout"  # 试用密钥
        response = requests.get(
            f'https://api.ipregistry.co/{ip}?key={api_key}',
            timeout=8
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
                'lat': data.get('location', {}).get('latitude', ''),
                'lon': data.get('location', {}).get('longitude', ''),
                'source': 'ipregistry.co'
            }
            
    except Exception as e:
        log_debug(f"ipregistry.co查询异常: {e}")
    return None