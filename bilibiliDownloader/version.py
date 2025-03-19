"""
存储
版本信息
"""

VERSION = "1.0.0"
BUILD_DATE = "2025-03-02"
AUTHOR = "B站视频下载器开发团队"
GITHUB = "https://github.com/your-username/bilibiliDownloader"

def get_version_info():
    """
    获取格式化的版本信息
    """
    return f"版本 {VERSION} (构建于 {BUILD_DATE})"

def get_about_info():
    """
    获取关于信息
    """
    return f"""
Bilibili视频下载器 v{VERSION}
构建日期: {BUILD_DATE}

一个简单易用的B站视频下载工具，支持多种画质和登录功能。
支持画质：从360P到8K超清。
支持批量下载、多线程下载，自动画质降级以确保成功。

开发者: {AUTHOR}
项目主页: {GITHUB}
"""
