"""
下载器工厂，根据需求创建合适的下载器实例
"""
from typing import Optional, Callable
from downloader import VideoDownloader

def create_downloader(progress_callback: Optional[Callable] = None, use_enhanced: bool = True):
    """
    创建下载器实例
    
    Args:
        progress_callback: 进度回调函数
        use_enhanced: 是否使用增强特性 (参数保留但不再需要切换不同下载器)
        
    Returns:
        下载器实例，具有download_video方法
    """
    # 由于增强功能已经合并到VideoDownloader中，直接返回该实例
    print("Info - 使用B站下载器 (已包含403错误修复功能)")
    return VideoDownloader(progress_callback=progress_callback)
