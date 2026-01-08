# Config/Logger.py
import os
import datetime
import sys

class Logger:
    """日志记录器类"""
    
    def __init__(self, log_file_path, console_output=True, log_level="INFO"):
        """
        初始化日志记录器
        
        Args:
            log_file_path: 日志文件路径
            console_output: 是否输出到控制台
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        """
        self.log_file_path = log_file_path
        self.console_output = console_output
        self.log_level = self._get_log_level_value(log_level)
        self.log_entries = []
        self._ensure_output_directory()
        
        # 初始化颜色支持
        self._init_colors()
        
    def _init_colors(self):
        """初始化颜色设置"""
        # ANSI 颜色代码
        self.colors = {
            "INFO": "\033[92m",    # 绿色
            "WARNING": "\033[93m", # 黄色
            "ERROR": "\033[91m",   # 红色
            "DEBUG": "\033[94m",   # 蓝色
        }
        self.reset = "\033[0m"
        
    def _get_log_level_value(self, level_str):
        """将日志级别字符串转换为数值"""
        levels = {
            'DEBUG': 10,
            'INFO': 20,
            'WARNING': 30,
            'ERROR': 40
        }
        return levels.get(level_str.upper(), 20)  # 默认为INFO
    
    def _ensure_output_directory(self):
        """确保输出目录存在"""
        if self.log_file_path:
            os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
    
    def info(self, message):
        """记录信息级别日志"""
        return self._log("INFO", message)
    
    def warning(self, message):
        """记录警告级别日志"""
        return self._log("WARNING", message)
    
    def error(self, message):
        """记录错误级别日志"""
        return self._log("ERROR", message)
    
    def debug(self, message):
        """记录调试级别日志"""
        return self._log("DEBUG", message)
    
    def _log(self, level, message):
        """
        记录日志消息
        
        Args:
            level: 日志级别
            message: 日志消息
            
        Returns:
            str: 格式化的日志条目
        """
        # 检查日志级别
        level_value = self._get_log_level_value(level)
        if level_value < self.log_level:
            return ""
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # 添加到内存中的日志条目列表
        self.log_entries.append(log_entry)
        
        # 实时写入文件
        self._write_to_file(log_entry)
        
        # 根据设置决定是否输出到控制台
        if self.console_output:
            self._print_to_console(level, log_entry)
        
        return log_entry
    
    def _write_to_file(self, log_entry):
        """将日志条目写入文件"""
        if not self.log_file_path:
            return
            
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"写入日志文件时出错: {str(e)}")
    
    def _print_to_console(self, level, log_entry):
        """在控制台输出日志（带颜色）"""
        color = self.colors.get(level, self.reset)
        print(f"{color}{log_entry}{self.reset}")
        sys.stdout.flush()  # 确保立即输出
    
    def clear_log(self):
        """清空日志文件（每次运行开始时调用）"""
        if not self.log_file_path:
            return
            
        try:
            with open(self.log_file_path, "w", encoding="utf-8") as f:
                f.write(f"节点处理日志 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n")
            
            # 在控制台也输出清空信息（带颜色）
            if self.console_output:
                color = self.colors.get("INFO")
                print(f"{color}已清空日志文件: {self.log_file_path}{self.reset}")
                sys.stdout.flush()
                
        except Exception as e:
            error_msg = f"清空日志文件时出错: {str(e)}"
            if self.console_output:
                color = self.colors.get("ERROR")
                print(f"{color}{error_msg}{self.reset}")
                sys.stdout.flush()

    def save_summary(self, summary_title="处理总结", summary_content=""):
        """
        保存处理总结
        
        Args:
            summary_title: 总结标题
            summary_content: 总结内容
        """
        if not self.log_file_path:
            return
            
        try:
            summary_text = f"""
{"=" * 80}
{summary_title}
{"=" * 80}
{summary_content}
{"=" * 80}
"""
            
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(summary_text)
                
            # 在控制台也输出总结信息（带颜色）
            if self.console_output:
                color = self.colors.get("INFO")
                print(f"{color}{summary_text}{self.reset}")
                sys.stdout.flush()
                
        except Exception as e:
            error_msg = f"保存处理总结时出错: {str(e)}"
            if self.console_output:
                color = self.colors.get("ERROR")
                print(f"{color}{error_msg}{self.reset}")
                sys.stdout.flush()
    
    def get_log_entries(self):
        """获取所有日志条目"""
        return self.log_entries.copy()
    
    def get_recent_logs(self, count=50):
        """获取最近的日志条目"""
        return self.log_entries[-count:] if self.log_entries else []
    
    def print_color_test(self):
        """测试所有颜色输出"""
        print("\n=== 日志颜色测试 ===")
        self.debug("这是一个DEBUG级别的测试消息")
        self.info("这是一个INFO级别的测试消息")
        self.warning("这是一个WARNING级别的测试消息")
        self.error("这是一个ERROR级别的测试消息")
        print("===================\n")

# 全局日志记录器实例
_global_logger = None

def get_logger():
    """获取全局日志记录器实例"""
    global _global_logger
    if _global_logger is None:
        log_file_path = "output/log.txt"
        _global_logger = Logger(log_file_path, console_output=True, log_level="INFO")
    return _global_logger

def init_logger(log_file_path="output/log.txt", console_output=True, log_level="INFO"):
    """初始化全局日志记录器"""
    global _global_logger
    _global_logger = Logger(log_file_path, console_output, log_level)
    return _global_logger

# 便捷函数
def log_info(message):
    """记录信息级别日志（便捷函数）"""
    return get_logger().info(message)

def log_warning(message):
    """记录警告级别日志（便捷函数）"""
    return get_logger().warning(message)

def log_error(message):
    """记录错误级别日志（便捷函数）"""
    return get_logger().error(message)

def log_debug(message):
    """记录调试级别日志（便捷函数）"""
    return get_logger().debug(message)

def test_logger_colors():
    """测试日志颜色输出"""
    logger = Logger("test_log.txt", console_output=True, log_level="DEBUG")
    logger.print_color_test()