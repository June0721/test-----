"""
缓存管理器，用于缓存API响应和视频信息
"""
import os
import json
import time


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_dir: str = None, max_age_seconds: int = 3600):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录，默认为程序目录下的cache文件夹
            max_age_seconds: 缓存最大有效期（秒），默认1小时
        """
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
        
        self.cache_dir = cache_dir
        self.max_age = max_age_seconds
        
        # 确保缓存目录存在
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_key(self, key: str) -> str:
        """
        将键转换为文件安全的缓存键
        
        Args:
            key: 原始缓存键
            
        Returns:
            str: 文件安全的缓存键
        """
        if isinstance(key, str):
            # 使用MD5生成固定长度、文件名安全的键
            return hashlib.md5(key.encode('utf-8')).hexdigest()
        return hashlib.md5(str(key).encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, key: str) -> str:
        """
        获取缓存文件路径
        
        Args:
            key: 缓存键
            
        Returns:
            str: 缓存文件路径
        """
        cache_key = self._get_cache_key(key)
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存内容
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存内容，如果不存在或已过期则返回None
        """
        cache_path = self._get_cache_path(key)
        
        # 检查缓存是否存在
        if not os.path.exists(cache_path):
            return None
        
        try:
            # 读取缓存
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 检查是否过期
            if time.time() - cache_data['timestamp'] > self.max_age:
                return None
            
            return cache_data['data']
        except Exception:
            # 任何错误都认为缓存无效
            return None
    
    def set(self, key: str, data: Any) -> bool:
        """
        设置缓存内容
        
        Args:
            key: 缓存键
            data: 要缓存的数据
            
        Returns:
            bool: 是否成功设置缓存
        """
        cache_path = self._get_cache_path(key)
        
        try:
            # 准备缓存数据
            cache_data = {
                'timestamp': time.time(),
                'data': data
            }
            
            # 写入缓存
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f)
            
            return True
        except Exception:
            return False
    
    def clear(self, key: str = None) -> bool:
        """
        清除缓存
        
        Args:
            key: 要清除的缓存键，如果为None则清除所有缓存
            
        Returns:
            bool: 是否成功清除缓存
        """
        if key:
            # 清除指定键的缓存
            cache_path = self._get_cache_path(key)
            if os.path.exists(cache_path):
                try:
                    os.remove(cache_path)
                    return True
                except Exception:
                    return False
            return True
        else:
            # 清除所有缓存
            try:
                for filename in os.listdir(self.cache_dir):
                    file_path = os.path.join(self.cache_dir, filename)
                    if os.path.isfile(file_path) and filename.endswith('.json'):
                        os.remove(file_path)
                return True
            except Exception:
                return False
    
    def cleanup(self) -> int:
        """
        清理过期的缓存
        
        Returns:
            int: 清理的缓存数量
        """
        count = 0
        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path) and filename.endswith('.json'):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)
                        
                        # 检查是否过期
                        if time.time() - cache_data['timestamp'] > self.max_age:
                            os.remove(file_path)
                            count += 1
                    except Exception:
                        # 无法读取，视为损坏的缓存，删除
                        os.remove(file_path)
                        count += 1
            return count
        except Exception:
            return count

# 创建全局缓存管理器
cache_manager = CacheManager()
