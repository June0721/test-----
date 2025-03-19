"""
输入验证模块，用于验证视频URL和保存路径
"""
import os
import re
from typing import Tuple, Optional

def validate_video_url(url: str) -> Tuple[bool, str]:
    """
    验证视频URL是否合法
    
    Args:
        url: 输入的URL字符串
        
    Returns:
        Tuple[bool, str]: (是否有效, 错误信息/修正的URL)
    """
    if not url or not isinstance(url, str):
        return False, "URL不能为空"
    
    # 去除首尾空格
    url = url.strip()
    
    # 检查是否为空或只有空格
    if not url:
        return False, "URL不能为空或只包含空格"
    
    # 检查基本的B站视频URL格式
    bilibili_pattern = re.search(r'(bilibili\.com/video/|b23\.tv/|BV\w+|av\d+)', url, re.IGNORECASE)
    if not bilibili_pattern:
        # 检查是否是纯BV号或av号
        if re.match(r'^[Bb][Vv][A-Za-z0-9]{10}$', url): 
            return True, url  # 有效的BV号
        elif re.match(r'^[Aa][Vv]\d+$', url):
            return True, url  # 有效的av号
        elif url.isdigit():  # 纯数字视为av号
            return True, f"av{url}"
        else:
            return False, "无效的URL格式，请输入完整的B站视频链接、BV号或av号"
    
    return True, url  # 有效的URL

def validate_save_dir(directory: str) -> Tuple[bool, str]:
    """
    验证保存目录是否合法
    
    Args:
        directory: 目录路径
        
    Returns:
        Tuple[bool, str]: (是否有效, 错误信息/目录路径)
    """
    if not directory:
        return False, "保存目录不能为空"
    
    # 去除首尾空格
    directory = directory.strip()
    
    # 检查是否为空或只有空格
    if not directory:
        return False, "保存目录不能为空或只包含空格"
    
    # 检查路径是否合法
    try:
        # 确保目录存在或可创建
        if not os.path.exists(directory):
            os.makedirs(directory)
        return True, directory
    except Exception as e:
        return False, f"无效的目录路径: {str(e)}"

def format_bilibili_url(url: str) -> str:
    """
    将各种形式的B站视频标识符格式化为标准URL
    
    Args:
        url: 输入的URL或视频ID
        
    Returns:
        str: 格式化后的URL
    """
    url = url.strip()
    
    # 直接是BV号
    bv_match = re.match(r'^[Bb][Vv][A-Za-z0-9]{10}$', url)
    if bv_match:
        return f"https://www.bilibili.com/video/{url}"
    
    # 直接是av号
    av_match = re.match(r'^[Aa][Vv](\d+)$', url)
    if av_match:
        return f"https://www.bilibili.com/video/{url}"
    
    # 纯数字（当作av号处理）
    if url.isdigit():
        return f"https://www.bilibili.com/video/av{url}"
    
    # 已经是完整URL，返回原值
    return url

def extract_video_details(url: str) -> Optional[dict]:
    """
    从URL中提取视频详细信息
    
    Args:
        url: 视频URL
        
    Returns:
        Optional[dict]: 包含视频ID类型和ID的字典，失败时返回None
    """
    if not url:
        return None
    
    # BV号格式
    bv_match = re.search(r'([Bb][Vv][A-Za-z0-9]{10})', url)
    if bv_match:
        bv_id = bv_match.group(1)
        if not bv_id.startswith('BV'):  # 确保大写BV
            bv_id = 'BV' + bv_id[2:]
        return {
            'id_type': 'bvid',
            'id': bv_id
        }
    
    # av号格式
    av_match = re.search(r'[Aa][Vv](\d+)', url)
    if av_match:
        av_num = av_match.group(1)
        return {
            'id_type': 'aid',
            'id': av_num
        }
    
    return None
