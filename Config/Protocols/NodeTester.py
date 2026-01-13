"""
节点测试器 - 测试节点延迟和获取地理位置
"""
import socket
import requests
import time
import ipaddress
import concurrent.futures
from Config.Logger import log_debug, log_error, log_info, log_warning

# 只从IP_Test.py导入需要的功能，不再直接导入Local或IP_API
from Config.IP_Test import get_ip_location, get_ip_location_with_fallback, get_ip_location_force_online, get_query_stats, clear_geo_cache, check_local_city_coverage, check_ip_has_city_local


def is_private_or_special_ip(ip):
    """
    检查IP地址是否为私有地址、回环地址或特殊地址
    
    Args:
        ip: IP地址字符串
        
    Returns:
        bool: 如果是私有/特殊地址返回True，否则返回False
    """
    try:
        ip_obj = ipaddress.ip_address(ip)
        
        # 检查是否为回环地址 (127.0.0.0/8)
        if ip_obj.is_loopback:
            return True
        
        # 检查是否为私有地址 (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
        if ip_obj.is_private:
            return True
        
        # 检查是否为链路本地地址 (169.254.0.0/16)
        if ip_obj.is_link_local:
            return True
        
        # 检查是否为多播地址 (224.0.0.0/4)
        if ip_obj.is_multicast:
            return True
        
        # 检查是否为未指定地址 (0.0.0.0)
        if ip_obj.is_unspecified:
            return True
        
        # 特殊检查：127.0.0.53 (Linux系统的DNS解析器地址)
        if ip == "127.0.0.53":
            return True
        
        # 特殊检查：其他常见的本地地址
        if ip in ["0.0.0.0", "255.255.255.255", "::1", "fe80::", "ff00::"]:
            return True
        
        # 检查是否为运营商级NAT地址 (100.64.0.0/10) - 仅IPv4
        if ip_obj.version == 4:
            cgnat_network = ipaddress.ip_network("100.64.0.0/10")
            if ip_obj in cgnat_network:
                return True
            
        return False
        
    except ValueError:
        # 无效的IP地址格式
        return True


def get_ip_address(hostname):
    """获取域名对应的IP地址，并验证是否为合法公网IP"""
    try:
        ip = socket.gethostbyname(hostname)
        
        # 验证IP地址
        if is_private_or_special_ip(ip):
            log_warning(f"跳过私有/特殊IP地址: {hostname} -> {ip}")
            return None
            
        return ip
    except socket.gaierror as e:
        log_error(f"解析域名失败 {hostname}: DNS查询失败 - {e}")
        return None
    except Exception as e:
        log_error(f"解析域名失败 {hostname}: {e}")
        return None


def create_unknown_location_result(ip, name, server, port, node_info):
    """创建未知位置的结果"""
    return {
        'node_name': name,
        'original_server': server,
        'ip': ip if ip else server,
        'port': port,
        'country': '未知',
        'country_code': '',
        'city': '未知',
        'city_en': 'Unknown',
        'region': '',
        'isp': '',
        'lat': 0.0,
        'lon': 0.0,
        'source': 'private_ip',
        'local_query': False,
        'has_city': False,
        'accuracy': 'low',
        'timezone': '',
        'postal_code': '',
        'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'node_info': node_info,
        'is_private_ip': True
    }


def _get_node_ip_address(server):
    """
    获取节点IP地址并进行验证
    
    Args:
        server: 服务器地址（可以是域名或IP）
        
    Returns:
        tuple: (ip_address, validation_result)
               validation_result: "valid" | "private_ip" | "resolve_failed"
    """
    try:
        # 检查是否为IP地址
        try:
            ip_obj = ipaddress.ip_address(server)
            # 如果是IP地址，直接检查是否为私有/特殊IP
            if is_private_or_special_ip(server):
                return server, "private_ip"
            return server, "valid"
        except ValueError:
            # 不是有效的IP地址，假设是域名，需要解析
            log_info(f"解析域名: {server}")
            ip = get_ip_address(server)
            
            if not ip:
                return None, "resolve_failed"
            
            # 解析后再次检查是否为私有/特殊IP
            if is_private_or_special_ip(ip):
                log_warning(f"域名解析为私有/特殊IP地址: {server} -> {ip}")
                return ip, "private_ip"
            
            return ip, "valid"
    except Exception as e:
        log_error(f"获取IP地址失败 {server}: {e}")
        return None, "resolve_failed"


def _query_location_online(ip):
    """
    在线查询地理位置
    
    Args:
        ip: IP地址
        
    Returns:
        dict: 在线查询结果，如果失败返回None
    """
    online_location = get_ip_location_force_online(ip)
    
    if online_location:
        service_detail = online_location.get('source', 'unknown_api')
        if online_location.get('has_city'):
            city_name = online_location.get('city', 'Unknown')
            country_code = online_location.get('country_code', 'Unknown')
            # log_info(f"[{ip}] 在线查询成功[{service_detail}]: {city_name}, {country_code}")
        else:
            country_code = online_location.get('country_code', 'Unknown')
            log_warning(f"[{ip}] 在线查询完成但无城市信息[{service_detail}]: {country_code}")
        return online_location
    else:
        log_error(f"[{ip}] 在线查询失败: 所有在线服务均无法获取位置信息")
        return None


def _query_location_with_fallback(ip):
    """
    智能地理位置查询策略：本地优先，在线降级
    
    Args:
        ip: IP地址
        
    Returns:
        dict: 地理位置查询结果
    """
    # 1. 检查本地数据库是否有城市信息
    local_has_city = check_ip_has_city_local(ip)
    # log_info(f"城市信息可用性: {local_has_city}")
    
    # 2. 根据情况选择查询策略
    if local_has_city:
        # 本地有城市信息，使用本地查询（不启用降级）
        location = get_ip_location(ip, enable_fallback=False)
        if location and location.get('has_city'):
            log_info(f"[{ip}] 本地查询成功（有城市信息）[GeoLite2-City.mmdb]: "
                    f"{location.get('city', 'Unknown')}, {location.get('country_code', 'Unknown')}")
            return location
        elif location:
            # 本地查询成功但没有城市信息
            log_info(f"[{ip}] 本地查询（无城市信息）: {location.get('country_code', 'Unknown')}")
            return location
        else:
            # 本地查询失败
            log_info(f"[{ip}] 本地查询失败，切换到在线查询...")
            return _query_location_online(ip)
    else:
        # 本地数据库无此IP城市信息，直接在线查询
        log_info(f"[{ip}] 本地数据库无此IP城市信息，切换到在线查询...")
        return _query_location_online(ip)


def _process_city_mapping(location_result, city_mappings):
    """
    处理城市名称映射（英文->中文）
    
    Args:
        location_result: 地理位置查询结果
        city_mappings: 城市映射表
        
    Returns:
        tuple: (city_zh, city_en)
    """
    # 获取城市英文名
    city_en = location_result.get('city_en', location_result.get('city', ''))
    
    # 使用映射表获取中文城市名
    if city_en:
        city_zh = city_mappings.get(city_en, city_en)
    else:
        city_zh = location_result.get('city', '未知')
    
    # 如果仍然没有城市名，标记为未知
    if not city_zh or city_zh == '':
        city_zh = '未知'
        city_en = 'Unknown'
    
    return city_zh, city_en


def _build_final_result(ip, name, server, port, location_result, city_zh, city_en, node_info):
    """
    构建最终的结果字典
    
    Args:
        ip: IP地址
        name: 节点名称
        server: 原始服务器地址
        port: 端口
        location_result: 地理位置查询结果
        city_zh: 中文城市名
        city_en: 英文城市名
        node_info: 原始节点信息
        
    Returns:
        dict: 完整的结果字典
    """
    # 获取数据来源信息
    source = location_result.get('source', 'unknown')
    service_detail = location_result.get('source', '')
    
    # 确定查询来源类型
    if location_result.get('local_query'):
        source_type = "local_with_city" if location_result.get('has_city') else "local_no_city"
    else:
        source_type = "online_fallback"
    
    # 构建结果
    result = {
        'node_name': name,
        'original_server': server,
        'ip': ip,
        'port': port,
        'country': location_result.get('country', '未知'),
        'country_code': location_result.get('country_code', ''),
        'city': city_zh,
        'city_en': city_en if city_en != 'Unknown' else '',
        'region': location_result.get('region', ''),
        'isp': location_result.get('isp', ''),
        'lat': location_result.get('lat', 0.0),
        'lon': location_result.get('lon', 0.0),
        'source': source_type,
        'service_detail': service_detail,
        'local_query': location_result.get('local_query', False),
        'has_city': location_result.get('has_city', False) and city_zh != '未知',
        'accuracy': location_result.get('accuracy', 'unknown'),
        'timezone': location_result.get('timezone', ''),
        'postal_code': location_result.get('postal_code', ''),
        'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'node_info': node_info,
        'is_private_ip': False
    }
    
    return result


def _log_final_result(ip, city_zh, location_result):
    """
    记录最终查询结果
    
    Args:
        ip: IP地址
        city_zh: 中文城市名
        location_result: 地理位置查询结果
    """
    source_type = "local_with_city" if location_result.get('local_query') else "online_fallback"
    service_detail = location_result.get('source', '')
    country = location_result.get('country', '未知')
    country_code = location_result.get('country_code', '')
    
    if city_zh != '未知':
        if source_type == "online_fallback":
            log_info(f"[{ip}] 位置查询完成[{service_detail}]: {city_zh}, {country_code}")
            None
        else:
            # log_info(f"[{ip}] 位置查询完成: {city_zh}, {country_code}")
            None
    else:
        if source_type == "online_fallback":
            log_warning(f"[{ip}] 位置查询完成但城市信息未知[{service_detail}]: {country}")
        else:
            log_warning(f"[{ip}] 位置查询完成但城市信息未知: {country}")


def test_node_with_fallback(node_info, city_mappings):
    """
    测试节点获取位置信息 - 智能降级策略
    
    优先使用本地数据库，如果没有城市信息则切换到在线测试
    
    Args:
        node_info: 节点信息字典
        city_mappings: 城市名称映射表
        
    Returns:
        dict: 位置测试结果，包含地理位置信息和测试状态
    """
    try:
        # 1. 提取节点基本信息
        server = node_info.get('server', '')
        port = node_info.get('port', 443)
        name = node_info.get('name', server)
        
        if not server:
            log_error("节点信息缺少server字段")
            return None
        
        log_info(f"开始测试节点: {name} ({server}:{port})")
        
        # 2. 获取节点IP地址
        ip, ip_validation_result = _get_node_ip_address(server)
        if ip_validation_result == "private_ip":
            log_warning(f"节点为私有/特殊IP: {server}")
            return create_unknown_location_result(ip, name, server, port, node_info)
        elif ip_validation_result == "resolve_failed":
            log_warning(f"无法解析节点地址: {server}")
            return create_unknown_location_result(None, name, server, port, node_info)
        
        log_info(f"节点IP地址: {ip}")
        
        # 3. 智能地理位置查询
        location_result = _query_location_with_fallback(ip)
        if not location_result:
            log_error(f"[{ip}] 所有地理位置查询都失败")
            return create_unknown_location_result(ip, name, server, port, node_info)
        
        # 4. 处理城市名称映射
        city_zh, city_en = _process_city_mapping(location_result, city_mappings)
        
        # 5. 构建最终结果
        result = _build_final_result(
            ip=ip,
            name=name,
            server=server,
            port=port,
            location_result=location_result,
            city_zh=city_zh,
            city_en=city_en,
            node_info=node_info
        )
        
        # 6. 记录最终结果
        _log_final_result(ip, city_zh, location_result)
        
        return result
            
    except Exception as e:
        log_error(f"测试节点失败 {node_info.get('name', 'Unknown')}: {e}")
        import traceback
        log_error(traceback.format_exc())
        return create_unknown_location_result(None, node_info.get('name', 'Unknown'), 
                                             node_info.get('server', ''), 
                                             node_info.get('port', 443), 
                                             node_info)


def test_node(node_info, city_mappings, enable_fallback=True):
    """兼容原有接口的测试函数"""
    return test_node_with_fallback(node_info, city_mappings)


def test_latency(host, port, timeout=5):
    """测试TCP连接延迟"""
    try:
        # 检查是否为私有/特殊地址
        try:
            if is_private_or_special_ip(host):
                log_warning(f"[{host}] 跳过私有地址延迟测试")
                return None
        except:
            pass  # 如果不是IP地址，继续尝试
        
        start_time = time.time()
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        end_time = time.time()
        
        latency = int((end_time - start_time) * 1000)  # 转换为毫秒
        
        log_debug(f"[{host}:{port}] TCP延迟测试: {latency}ms")
        return latency
    except socket.timeout:
        log_debug(f"[{host}:{port}] TCP延迟测试超时")
        return None
    except ConnectionRefusedError:
        log_debug(f"[{host}:{port}] TCP连接被拒绝")
        return None
    except Exception as e:
        log_debug(f"[{host}:{port}] TCP延迟测试失败: {e}")
        return None


def batch_test_nodes(node_list, city_mappings, max_workers=10):
    """
    批量测试节点 - 使用智能降级策略
    
    Args:
        node_list: 节点信息列表
        city_mappings: 城市映射表
        max_workers: 最大并发数
        
    Returns:
        list: 测试结果列表
    """
    results = []
    failed_nodes = []
    successful_nodes = []
    private_nodes = []
    
    log_info(f"开始批量测试 {len(node_list)} 个节点，最大并发数: {max_workers}")
    log_info(f"测试策略: 先本地数据库 → 无城市信息 → 在线查询 → 私有IP标记为未知")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_node = {
            executor.submit(test_node_with_fallback, node, city_mappings): node 
            for node in node_list
        }
        
        # 处理完成的任务
        for future in concurrent.futures.as_completed(future_to_node):
            node = future_to_node[future]
            node_name = node.get('name', node.get('server', 'Unknown'))
            
            try:
                result = future.result()
                if result:
                    results.append(result)
                    
                    # 分类统计
                    if result.get('is_private_ip'):
                        private_nodes.append(node_name)
                        log_info(f"私有IP节点: {node_name} -> 标记为未知")
                    elif result.get('has_city'):
                        successful_nodes.append(node_name)
                    else:
                        failed_nodes.append(node_name)
                else:
                    failed_nodes.append(node_name)
            except Exception as e:
                log_error(f"节点测试异常 {node_name}: {e}")
                failed_nodes.append(node_name)
    
    # 输出统计信息
    log_info(f"批量测试完成:")
    log_info(f"  成功获取城市信息: {len(successful_nodes)} 个")
    log_info(f"  私有IP标记为未知: {len(private_nodes)} 个")
    log_info(f"  失败或无城市信息: {len(failed_nodes)} 个")
    
    # 输出查询来源统计
    source_stats = {}
    service_stats = {}
    for result in results:
        source = result.get('source', 'unknown')
        source_stats[source] = source_stats.get(source, 0) + 1
        
        service = result.get('service_detail', 'unknown')
        if service:
            service_stats[service] = service_stats.get(service, 0) + 1
    
    if source_stats:
        log_info(f"数据来源统计:")
        for source, count in sorted(source_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(results) * 100) if results else 0
            log_info(f"  - {source}: {count} ({percentage:.1f}%)")
    
    if service_stats:
        log_info(f"服务使用统计:")
        for service, count in sorted(service_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(results) * 100) if results else 0
            log_info(f"  - {service}: {count} ({percentage:.1f}%)")
    
    # 输出地理位置查询统计
    stats = get_query_stats()
    if stats:
        log_info(f"地理位置查询统计:")
        log_info(f"  - 总查询数: {stats['total_queries']}")
        log_info(f"  - 本地查询成功率: {stats['local_success_rate']}%")
        log_info(f"  - 本地有城市信息的比例: {stats['local_city_available_rate']}%")
        log_info(f"  - 在线降级率: {stats['online_fallback_rate']}%")
        log_info(f"  - 在线查询成功率: {stats['online_success_rate']}%")
    
    return results


def get_node_statistics(results):
    """
    获取节点测试统计信息
    
    Args:
        results: 测试结果列表
        
    Returns:
        dict: 统计信息
    """
    if not results:
        return {}
    
    stats = {
        'total_nodes': len(results),
        'countries': {},
        'sources': {},
        'services': {},
        'local_queries': 0,
        'online_queries': 0,
        'has_city_count': 0,
        'no_city_count': 0,
        'private_ip_count': 0
    }
    
    for result in results:
        # 私有IP统计
        if result.get('is_private_ip'):
            stats['private_ip_count'] += 1
            continue
            
        # 国家统计
        country = result.get('country_code', 'Unknown')
        stats['countries'][country] = stats['countries'].get(country, 0) + 1
        
        # 数据来源统计
        source = result.get('source', 'Unknown')
        stats['sources'][source] = stats['sources'].get(source, 0) + 1
        
        # 服务统计
        service = result.get('service_detail', 'Unknown')
        stats['services'][service] = stats['services'].get(service, 0) + 1
        
        # 查询方式统计
        if result.get('local_query'):
            stats['local_queries'] += 1
        else:
            stats['online_queries'] += 1
        
        # 城市信息统计
        if result.get('has_city'):
            stats['has_city_count'] += 1
        else:
            stats['no_city_count'] += 1
    
    # 计算百分比
    total_public = stats['total_nodes'] - stats['private_ip_count']
    if total_public > 0:
        stats['local_query_percentage'] = (stats['local_queries'] / total_public * 100)
        stats['online_query_percentage'] = (stats['online_queries'] / total_public * 100)
        stats['has_city_percentage'] = (stats['has_city_count'] / total_public * 100)
        stats['no_city_percentage'] = (stats['no_city_count'] / total_public * 100)
    else:
        stats['local_query_percentage'] = 0
        stats['online_query_percentage'] = 0
        stats['has_city_percentage'] = 0
        stats['no_city_percentage'] = 0
    
    stats['private_ip_percentage'] = (stats['private_ip_count'] / stats['total_nodes'] * 100) if stats['total_nodes'] > 0 else 0
    
    # 计算国家分布（前10）
    sorted_countries = sorted(stats['countries'].items(), key=lambda x: x[1], reverse=True)[:10]
    stats['top_countries'] = sorted_countries
    
    # 计算来源分布
    sorted_sources = sorted(stats['sources'].items(), key=lambda x: x[1], reverse=True)[:5]
    stats['top_sources'] = sorted_sources
    
    # 计算服务分布
    sorted_services = sorted(stats['services'].items(), key=lambda x: x[1], reverse=True)[:5]
    stats['top_services'] = sorted_services
    
    return stats