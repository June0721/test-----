"""
统一日志系统，提供不同级别日志支持
"""
import logging
import os
import sys
from datetime import datetime

class Logger:
    """日志管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._setup_logger()
        return cls._instance
    
    @staticmethod
    def _setup_logger():
        """初始化日志系统"""
        # 创建日志目录
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # 创建日志文件名（包含日期）
        log_file = os.path.join(log_dir, f"downloader_{datetime.now().strftime('%Y%m%d')}.log")
        
        # 配置根日志器
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # 控制台只显示INFO以上级别
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        
        # 添加处理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        Logger._instance = logger
    
    @staticmethod
    def debug(message):
        """调试级别日志"""
        logging.debug(message)
    
    @staticmethod
    def info(message):
        """信息级别日志"""
        logging.info(message)
    
    @staticmethod
    def warning(message):
        """警告级别日志"""
        logging.warning(message)
    
    @staticmethod
    def error(message):
        """错误级别日志"""
        logging.error(message)
    
    @staticmethod
    def critical(message):
        """严重错误级别日志"""
        logging.critical(message)

# 创建全局日志对象
logger = Logger()
