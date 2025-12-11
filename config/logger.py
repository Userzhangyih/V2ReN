# config/logger.py
import os
import datetime

class Logger:
    """日志记录器类"""
    
    def __init__(self, log_file_path):
        """
        初始化日志记录器
        
        Args:
            log_file_path: 日志文件路径
        """
        self.log_file_path = log_file_path
        self.log_entries = []
        self._ensure_output_directory()
        
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
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # 添加到内存中的日志条目列表
        self.log_entries.append(log_entry)
        
        # 实时写入文件
        self._write_to_file(log_entry)
        
        # 同时在控制台输出（根据级别使用不同颜色）
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
        colors = {
            "INFO": "\033[92m",    # 绿色
            "WARNING": "\033[93m", # 黄色
            "ERROR": "\033[91m",   # 红色
            "DEBUG": "\033[94m",   # 蓝色
        }
        reset = "\033[0m"
        
        color = colors.get(level, "\033[0m")
        print(f"{color}{log_entry}{reset}")
    
    def clear_log(self):
        """清空日志文件（每次运行开始时调用）"""
        if not self.log_file_path:
            return
            
        try:
            with open(self.log_file_path, "w", encoding="utf-8") as f:
                f.write(f"节点处理日志 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n")
        except Exception as e:
            print(f"清空日志文件时出错: {str(e)}")
    
    def save_summary(self, summary_title="处理总结"):
        """
        保存处理总结
        
        Args:
            summary_title: 总结标题
        """
        if not self.log_file_path or not self.log_entries:
            return
            
        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"{summary_title}\n")
                f.write("=" * 80 + "\n")
                for entry in self.log_entries[-20:]:  # 保存最近20条记录
                    f.write(entry + "\n")
        except Exception as e:
            print(f"保存处理总结时出错: {str(e)}")
    
    def get_log_entries(self):
        """获取所有日志条目"""
        return self.log_entries.copy()
    
    def get_recent_logs(self, count=50):
        """获取最近的日志条目"""
        return self.log_entries[-count:] if self.log_entries else []

# 全局日志记录器实例
_global_logger = None

def get_logger():
    """获取全局日志记录器实例"""
    global _global_logger
    if _global_logger is None:
        log_file_path = "output/log.txt"
        _global_logger = Logger(log_file_path)
    return _global_logger

def init_logger(log_file_path="output/log.txt"):
    """初始化全局日志记录器"""
    global _global_logger
    _global_logger = Logger(log_file_path)
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