"""
安全工具函数 (简化版本，不依赖cryptography库)
"""
import os
import base64
import json
import hashlib
import hmac
from typing import Dict, Any, Optional

class SecurityUtils:
    """安全工具类，提供基本的敏感数据处理功能"""

    @staticmethod
    def mask_sensitive_string(text: str, visible_prefix: int = 3, visible_suffix: int = 3) -> str:
        """
        遮盖敏感字符串，只显示前几个和后几个字符
        
        Args:
            text: 敏感字符串
            visible_prefix: 前面显示的字符数
            visible_suffix: 后面显示的字符数
            
        Returns:
            str: 遮盖后的字符串
        """
        if not text:
            return ""
            
        text_len = len(text)
        if text_len <= (visible_prefix + visible_suffix):
            return "*" * text_len
            
        prefix = text[:visible_prefix]
        suffix = text[-visible_suffix:] if visible_suffix > 0 else ""
        mask_len = text_len - visible_prefix - visible_suffix
        
        return prefix + "*" * mask_len + suffix
    
    @staticmethod
    def generate_device_id() -> str:
        """
        生成设备ID，用于模拟浏览器环境
        
        Returns:
            str: 设备ID
        """
        import platform
        import uuid
        
        # 获取系统信息
        system_info = platform.system() + platform.version() + platform.machine()
        
        # 获取MAC地址
        mac = uuid.getnode()
        
        # 生成唯一标识符
        device_id = hashlib.md5((system_info + str(mac)).encode()).hexdigest()
        
        return device_id
    
    @staticmethod
    def simple_encrypt(data: str, key: str) -> str:
        """简单加密数据 (不如cryptography安全，但不需要外部依赖)"""
        if not data or not key:
            return ""
            
        # 生成密钥的哈希
        key_hash = hashlib.sha256(key.encode()).digest()
        
        # Base64编码输入数据
        data_b64 = base64.b64encode(data.encode()).decode()
        
        # 生成HMAC签名
        signature = hmac.new(key_hash, data_b64.encode(), hashlib.sha256).hexdigest()
        
        # 组合结果
        result = {
            "data": data_b64,
            "signature": signature,
            "timestamp": str(int(import_time()))  # 需要时间模块
        }
        
        return base64.b64encode(json.dumps(result).encode()).decode()
    
    @staticmethod
    def simple_decrypt(encrypted_data: str, key: str) -> Optional[str]:
        """简单解密数据"""
        if not encrypted_data or not key:
            return None
            
        try:
            # 解码结果
            result_json = base64.b64decode(encrypted_data).decode()
            result = json.loads(result_json)
            
            # 验证签名
            data_b64 = result["data"]
            stored_signature = result["signature"]
            
            # 生成密钥的哈希
            key_hash = hashlib.sha256(key.encode()).digest()
            
            # 验证HMAC签名
            calculated_signature = hmac.new(key_hash, data_b64.encode(), hashlib.sha256).hexdigest()
            if calculated_signature != stored_signature:
                return None
                
            # 解码数据
            return base64.b64decode(data_b64).decode()
            
        except Exception:
            return None

# 添加所需的时间函数
def import_time():
    """导入时间模块并返回当前时间戳"""
    import time
    return time.time()