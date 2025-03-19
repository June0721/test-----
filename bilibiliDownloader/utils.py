"""
工具函数模块，包含各种通用辅助函数
"""
import json
import os
import random
import re
import shutil
import string
import time
from datetime import datetime

import requests

from config import HISTORY_FILE


def ensure_dir(directory):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def format_file_name(name):
    """格式化文件名，移除非法字符"""
    # 替换Windows不支持的文件名字符
    illegal_chars = r'[\\/*?:"<>|]'
    name = re.sub(illegal_chars, '_', name)
    # 限制长度
    return name[:200] if len(name) > 200 else name

def extract_video_id(url):
    """从URL中提取视频ID"""
    # BV号格式
    bv_match = re.search(r'BV\w{10}', url)
    if bv_match:
        return bv_match.group(0)
    
    # av号格式
    av_match = re.search(r'av(\d+)', url)
    if av_match:
        return f"av{av_match.group(1)}"
    
    # 尝试从路径中提取
    if '/video/' in url:
        video_id = url.split('/video/')[-1].split('?')[0].split('/')[0]
        if video_id.startswith('BV') or video_id.startswith('av'):
            return video_id
    
    # 短链接处理
    if 'b23.tv' in url:
        try:
            import requests
            response = requests.head(url, allow_redirects=True)
            return extract_video_id(response.url)
        except:
            pass
    
    return None

def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.1f} MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.2f} GB"

def format_time(seconds):
    """格式化时间"""
    if seconds < 60:
        return f"{int(seconds)}秒"
    elif seconds < 3600:
        return f"{int(seconds/60)}分{int(seconds%60)}秒"
    else:
        return f"{int(seconds/3600)}小时{int((seconds%3600)/60)}分"

def load_history():
    """加载下载历史"""
    if not os.path.exists(HISTORY_FILE):
        return []
        
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取历史记录失败: {e}")
        # 如果文件损坏，备份并创建新的
        if os.path.exists(HISTORY_FILE):
            backup_file = f"{HISTORY_FILE}.bak.{int(time.time())}"
            shutil.copy2(HISTORY_FILE, backup_file)
            print(f"已备份损坏的历史文件到: {backup_file}")
        return []

def save_history(entry):
    """保存下载历史"""
    history = load_history()
    
    # 添加下载时间，如果不存在
    if 'downloaded_at' not in entry and 'download_time' not in entry:
        entry['downloaded_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 添加新记录
    history.append(entry)
    
    # 保存到文件
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存历史记录失败: {e}")

def clear_history():
    """清空下载历史"""
    if os.path.exists(HISTORY_FILE):
        # 创建备份
        backup_file = f"{HISTORY_FILE}.bak.{int(time.time())}"
        shutil.copy2(HISTORY_FILE, backup_file)
        # 删除原文件
        os.remove(HISTORY_FILE)
        return True
    return False

def get_system_info():
    """获取系统信息"""
    import platform
    info = {
        "os": platform.system(),
        "version": platform.version(),
        "architecture": platform.architecture(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version()
    }
    return info

def test_network():
    """测试网络连接"""
    import requests
    try:
        response = requests.get("https://www.bilibili.com", timeout=5)
        return response.status_code == 200
    except:
        return False

# 添加调试/优化相关工具函数
def profile_function(func):
    """性能分析装饰器"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        print(f"函数 {func.__name__} 执行耗时: {elapsed:.4f} 秒")
        return result
    return wrapper

def get_file_size(url: str) -> int:
    """获取远程文件大小"""
    try:
        response = requests.head(url)
        response.raise_for_status()
        content_length = int(response.headers.get('content-length', 0))
        return content_length
    except Exception as e:
        print(f"警告: 无法获取文件大小 - {str(e)}")
        return 0

def get_quality_description(quality_code: int) -> str:
    """根据画质代码返回画质描述"""
    from config import QUALITY_MAP
    return QUALITY_MAP.get(quality_code, f"未知画质({quality_code})")

def log_debug(message: str, debug_mode: bool = True) -> None:
    """记录调试信息"""
    if debug_mode:
        print(f"Debug - {message}")

def find_best_quality(available_qualities: list, requested_quality: int) -> int:
    """从可用画质中找到最接近请求画质的选项"""
    if not available_qualities:
        return requested_quality
    
    # 如果请求的画质就在可用列表中
    if requested_quality in available_qualities:
        return requested_quality
    
    # 否则找到不超过请求画质的最高可用画质
    best_match = None
    for qn in sorted(available_qualities, reverse=True):
        if qn <= requested_quality:
            best_match = qn
            break
    
    # 如果没找到更低的画质，则返回可用的最高画质
    if best_match is None and available_qualities:
        best_match = max(available_qualities)
    
    return best_match or requested_quality

def format_degradation_message(degradation_info: dict) -> str:
    """格式化画质降级信息为可读消息"""
    if not degradation_info:
        return ""
    
    from_quality = degradation_info.get('requested_name', '未知')
    to_quality = degradation_info.get('current_name', '未知')
    reason = degradation_info.get('reason', '未知原因')
    
    return f"画质已从 {from_quality} 降级为 {to_quality}。原因: {reason}"

def prepare_url(url: str) -> str:
    """预处理URL，确保格式正确"""
    if not url:
        return ""
        
    # 修剪空格
    url = url.strip()
    
    # 修正常见的URL格式问题
    if url.startswith(('BV', 'bv')) and len(url) >= 10:
        # 直接输入的BV号，转为标准URL
        return f"https://www.bilibili.com/video/{url}"
    
    if url.startswith(('av', 'AV')) and url[2:].isdigit():
        # 直接输入的av号，转为标准URL
        return f"https://www.bilibili.com/video/{url}"
    
    if url.isdigit():
        # 纯数字，假设是av号
        return f"https://www.bilibili.com/video/av{url}"
    
    # 已经是完整URL或其他格式，保持不变
    return url

def generate_temp_id() -> str:
    """生成临时标识符"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))
