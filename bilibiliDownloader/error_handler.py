"""
错误处理器，提供用户友好的错误信息
"""
import re
import traceback
from typing import Tuple

def analyze_error(error: Exception) -> Tuple[str, str, bool]:
    """
    分析错误并返回用户友好的错误信息
    
    Args:
        error: 发生的异常
        
    Returns:
        Tuple[str, str, bool]: (错误标题, 错误详情, 是否致命错误)
    """
    error_msg = str(error)
    error_type = type(error).__name__
    stack_trace = traceback.format_exc()
    is_fatal = True  # 默认认为是致命错误
    
    # 网络错误处理
    if "ConnectionError" in error_type or "Timeout" in error_type:
        title = "网络连接错误"
        detail = "无法连接到B站服务器，请检查您的网络连接。"
        is_fatal = False
    
    # 403权限错误
    elif "403" in error_msg:
        title = "访问权限错误"
        detail = "服务器拒绝访问，可能是因为:\n1. Cookie失效或过期\n2. 请求过于频繁\n3. IP地址被限制\n\n建议重新登录或稍后再试。"
        is_fatal = False
    
    # 视频不存在
    elif "视频不存在" in error_msg or "获取视频信息失败" in error_msg:
        title = "视频不存在或已被删除"
        detail = "请检查视频链接是否正确，或该视频可能已被作者删除。"
        is_fatal = True
    
    # 登录相关错误
    elif "登录" in error_msg or "SESSDATA" in error_msg:
        title = "登录凭证错误"
        detail = "登录凭证无效或已过期，请重新登录。"
        is_fatal = False
    
    # FFmpeg错误
    elif "ffmpeg" in error_msg.lower():
        title = "视频合并错误"
        detail = "FFmpeg工具出错，无法合并视频和音频。请确保FFmpeg已正确安装。"
        is_fatal = False
    
    # 默认错误处理
    else:
        title = f"下载错误({error_type})"
        detail = f"{error_msg}\n\n详细信息:\n{stack_trace[:300]}..."
        is_fatal = True
    
    return title, detail, is_fatal
