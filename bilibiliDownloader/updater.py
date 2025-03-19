"""
自动更新检查模块
"""
import os
import json
import threading
import time
import tkinter as tk
from tkinter import messagebox
import requests
from config import DEFAULT_CONFIG
from logger import logger

class Updater:
    """更新检查器"""
    VERSION = "1.0.0"
    REPO_API = "https://api.github.com/repos/yourusername/bilibiliDownloader/releases/latest"
    
    @staticmethod
    def check_update(silent=False):
        """
        检查更新
        
        Args:
            silent: 是否静默检查，True不显示"已是最新"提示
            
        Returns:
            bool: 是否有更新
        """
        try:
            # 获取最新版本信息
            response = requests.get(Updater.REPO_API, timeout=10)
            if response.status_code != 200:
                logger.warning(f"检查更新失败: HTTP {response.status_code}")
                return False
                
            latest = response.json()
            latest_version = latest["tag_name"].lstrip("v")
            
            # 比较版本
            if Updater.compare_versions(latest_version, Updater.VERSION) > 0:
                # 有更新
                if not silent:
                    root = tk.Tk()
                    root.withdraw()
                    result = messagebox.askyesno(
                        "发现新版本", 
                        f"当前版本: v{Updater.VERSION}\n"
                        f"最新版本: v{latest_version}\n\n"
                        f"更新内容: {latest['body'][:200]}...\n\n"
                        "是否前往下载页面？"
                    )
                    if result:
                        import webbrowser
                        webbrowser.open(latest["html_url"])
                return True
            else:
                # 已是最新
                if not silent:
                    root = tk.Tk()
                    root.withdraw()
                    messagebox.showinfo("检查更新", f"当前已是最新版本 v{Updater.VERSION}")
                return False
                
        except Exception as e:
            logger.error(f"检查更新异常: {str(e)}")
            return False
    
    @staticmethod
    def compare_versions(v1, v2):
        """比较版本号大小，返回: 1 表示v1>v2, -1 表示v1<v2, 0 表示相等"""
        v1_parts = [int(x) for x in v1.split('.')]
        v2_parts = [int(x) for x in v2.split('.')]
        
        # 补齐位数
        while len(v1_parts) < 3:
            v1_parts.append(0)
        while len(v2_parts) < 3:
            v2_parts.append(0)
            
        # 比较
        for i in range(3):
            if v1_parts[i] > v2_parts[i]:
                return 1
            elif v1_parts[i] < v2_parts[i]:
                return -1
        
        return 0
    
    @staticmethod
    def background_check():
        """后台检查更新"""
        def _check():
            # 等待一段时间后再检查，避免影响程序启动速度
            time.sleep(5)
            Updater.check_update(silent=True)
            
        thread = threading.Thread(target=_check, daemon=True)
        thread.start()

# 在导入时执行后台更新检查
if DEFAULT_CONFIG.get("auto_check_update", True):
    Updater.background_check()
