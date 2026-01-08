"""
节点测试器 - 测试节点延迟和获取地理位置
"""
import socket
import requests
import time
import ipaddress
import concurrent.futures
from Config.Logger import log_debug, log_error, log_info, log_warning
from Config.IP_Test import get_ip_location, get_ip_location_with_fallback, get_ip_location_force_online, get_query_stats, clear_geo_cache, check_local_city_coverage


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


def test_node_with_fallback(node_info, city_mappings):
    """
    测试节点获取位置信息 - 智能降级策略
    
    优先使用本地数据库，如果没有城市信息则切换到在线测试
    """
    try:
        server = node_info.get('server', '')
        port = node_info.get('port', 443)
        name = node_info.get('name', server)
        
        if not server:
            log_error("节点信息缺少server字段")
            return None
        
        log_info(f"开始测试节点: {name} ({server}:{port})")
        
        # 步骤1: 检查服务器地址是否为域名或IP
        try:
            # 尝试将地址解析为IP对象
            ip_obj = ipaddress.ip_address(server)
            # 如果是IP地址，直接检查是否为私有/特殊IP
            if is_private_or_special_ip(server):
                log_warning(f"检测到私有/特殊服务器地址: {server}，标记为未知")
                return create_unknown_location_result(server, name, server, port, node_info)
            ip = server
        except ValueError:
            # 不是有效的IP地址，假设是域名，需要解析
            log_debug(f"解析域名: {server}")
            ip = get_ip_address(server)
            
            if not ip:
                # 无法解析或为私有IP
                log_warning(f"无法获取有效公网IP地址: {server}，标记为未知")
                return create_unknown_location_result(None, name, server, port, node_info)
            
            # 解析后再次检查是否为私有/特殊IP
            if is_private_or_special_ip(ip):
                log_warning(f"域名解析为私有/特殊IP地址: {server} -> {ip}，标记为未知")
                return create_unknown_location_result(ip, name, server, port, node_info)
        
        log_debug(f"节点IP地址: {ip}")
        
        # 步骤2: 先尝试本地数据库查询
        from Config.IP_Test import check_ip_has_city_local, get_ip_location
        
        local_has_city = check_ip_has_city_local(ip)
        log_debug(f"本地数据库城市信息可用性: {local_has_city}")
        
        location = None
        source = "unknown"
        service_detail = ""  # 记录具体的服务名称
        
        if local_has_city:
            # 使用本地数据库（不启用降级）
            location = get_ip_location(ip, enable_fallback=False)
            if location:
                if location.get('has_city'):
                    source = "local_with_city"
                    service_detail = "GeoLite2-City.mmdb"
                    log_info(f"[{ip}] 本地查询成功（有城市信息）[{service_detail}]: {location.get('city', 'Unknown')}, {location.get('country_code', 'Unknown')}")
                else:
                    source = "local_no_city"
                    service_detail = "GeoLite2-City.mmdb"
                    # 输出本地查询到的结果，即使没有城市信息
                    country_code = location.get('country_code', 'Unknown')
                    log_info(f"[{ip}] 本地查询（无城市信息）: {country_code}")
                    # 也可以输出其他已查询到的信息
                    if location.get('country'):
                        log_debug(f"[{ip}] 国家: {location.get('country')}")
                    if location.get('region'):
                        log_debug(f"[{ip}] 地区: {location.get('region')}")
            else:
                source = "local_no_data"
                log_warning(f"[{ip}] 本地查询失败: 无法获取任何位置信息")
        else:
            source = "local_no_city_available"
            log_debug(f"[{ip}] 本地数据库无此IP城市信息")
        
        # 步骤3: 如果本地没有城市信息，切换到在线测试
        if not location or not location.get('has_city'):
            log_info(f"[{ip}] 本地查询无城市信息，切换到在线查询...")
            online_location = get_ip_location_force_online(ip)
            
            if online_location:
                location = online_location
                source = "online_fallback"
                service_detail = location.get('source', 'unknown_api')
                
                if online_location.get('has_city'):
                    city_name = online_location.get('city', 'Unknown')
                    country_code = online_location.get('country_code', 'Unknown')
                    log_info(f"[{ip}] 在线查询成功[{service_detail}]: {city_name}, {country_code}")
                else:
                    country_code = online_location.get('country_code', 'Unknown')
                    log_warning(f"[{ip}] 在线查询完成但无城市信息[{service_detail}]: {country_code}")
            else:
                log_error(f"[{ip}] 在线查询失败: 所有在线服务均无法获取位置信息")
        
        # 步骤4: 处理查询结果
        if location:
            # 获取城市英文名和中文名映射
            city_en = location.get('city_en', location.get('city', ''))
            if city_en:
                # 使用映射表获取中文城市名
                city_zh = city_mappings.get(city_en, city_en)
            else:
                city_zh = location.get('city', '未知')
            
            # 如果仍然没有城市名，标记为未知
            if not city_zh or city_zh == '':
                city_zh = '未知'
                city_en = 'Unknown'
            
            # 获取国家信息
            country = location.get('country', '未知')
            country_code = location.get('country_code', '')
            
            # 获取服务详情
            if not service_detail and location.get('source'):
                service_detail = location.get('source')
            
            # 构建完整结果
            result = {
                'node_name': name,
                'original_server': server,
                'ip': ip,
                'port': port,
                'country': country,
                'country_code': country_code,
                'city': city_zh,
                'city_en': city_en if city_en != 'Unknown' else '',
                'region': location.get('region', ''),
                'isp': location.get('isp', ''),
                'lat': location.get('lat', 0.0),
                'lon': location.get('lon', 0.0),
                'source': source,
                'service_detail': service_detail,  # 添加服务详情字段
                'local_query': location.get('local_query', False),
                'has_city': location.get('has_city', False) and city_zh != '未知',
                'accuracy': location.get('accuracy', 'unknown'),
                'timezone': location.get('timezone', ''),
                'postal_code': location.get('postal_code', ''),
                'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'node_info': node_info,
                'is_private_ip': False
            }
            
            # 记录最终结果
            if city_zh != '未知':
                if source == "online_fallback":
                    log_info(f"[{ip}] 位置查询完成[{service_detail}]: {city_zh}, {country_code}")
                else:
                    log_info(f"[{ip}] 位置查询完成: {city_zh}, {country_code}")
            else:
                if source == "online_fallback":
                    log_warning(f"[{ip}] 位置查询完成但城市信息未知[{service_detail}]: {country}")
                else:
                    log_warning(f"[{ip}] 位置查询完成但城市信息未知: {country}")
            
            return result
        else:
            # 所有查询都失败
            log_error(f"[{ip}] 所有地理位置查询都失败")
            return create_unknown_location_result(ip, name, server, port, node_info)
            
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