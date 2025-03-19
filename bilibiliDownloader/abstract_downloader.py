"""
下载器抽象基类，定义统一接口
"""
import abc
from typing import Dict, Optional, Callable

class AbstractDownloader(abc.ABC):
    """下载器抽象基类"""
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        """初始化下载器"""
        self.progress_callback = progress_callback
        self.is_downloading = False
        self.cancellation_event = None  # 子类实现
        
    @abc.abstractmethod
    def download_video(self, url: str, save_dir: str, quality: str) -> Dict:
        """下载视频的抽象方法"""
        pass
        
    @abc.abstractmethod
    def stop_download(self):
        """停止下载的抽象方法"""
        pass
