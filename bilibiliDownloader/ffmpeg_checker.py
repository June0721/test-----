"""
FFmpeg检查和管理模块
"""
import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser

class FFmpegChecker:
    """FFmpeg检查和管理类"""
    
    @staticmethod
    def check_ffmpeg() -> bool:
        """检查系统中是否存在FFmpeg，返回布尔值"""
        return shutil.which('ffmpeg') is not None
    
    @staticmethod
    def get_ffmpeg_version() -> str:
        """获取FFmpeg版本信息"""
        if not FFmpegChecker.check_ffmpeg():
            return "未安装"
        
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'], 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            if result.returncode == 0:
                # 通常第一行就是版本信息
                first_line = result.stdout.strip().split('\n')[0]
                return first_line
            return "无法获取版本"
        except Exception:
            return "检查版本出错"
    
    @staticmethod
    def show_ffmpeg_guide():
        """显示FFmpeg安装指南"""
        window = tk.Tk()
        window.title("FFmpeg安装指南")
        window.geometry("650x500")
        
        main_frame = ttk.Frame(window, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="FFmpeg安装指南", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # 检测状态
        installed = FFmpegChecker.check_ffmpeg()
        status_text = "已安装 - " + FFmpegChecker.get_ffmpeg_version() if installed else "未安装"
        status_color = "green" if installed else "red"
        
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill="x", pady=10)
        
        ttk.Label(status_frame, text="当前状态:").pack(side="left")
        status_label = ttk.Label(status_frame, text=status_text, foreground=status_color)
        status_label.pack(side="left", padx=5)
        
        # 安装指南
        guide_text = """
FFmpeg是处理音视频必要的工具，用于将B站的音视频流合并为完整视频。

下载并安装FFmpeg的步骤:

Windows用户:
1. 下载FFmpeg: 点击下方的"下载FFmpeg"按钮
2. 解压下载的文件到一个固定位置 (如 C:\\FFmpeg)
3. 将FFmpeg的bin目录添加到系统PATH环境变量:
   - 右键"此电脑" > 属性 > 高级系统设置 > 环境变量
   - 在"系统变量"中找到Path，点击编辑
   - 添加FFmpeg的bin目录路径 (如 C:\\FFmpeg\\bin)
4. 重启命令提示符或IDE，输入"ffmpeg -version"验证安装

macOS用户:
1. 使用Homebrew安装:
   brew install ffmpeg

Linux用户:
1. Ubuntu/Debian:
   sudo apt update
   sudo apt install ffmpeg
2. Fedora:
   sudo dnf install ffmpeg
3. Arch Linux:
   sudo pacman -S ffmpeg

安装后请重启程序并再次检查FFmpeg状态。
        """
        
        guide_label = ttk.Label(main_frame, text=guide_text, justify="left", wraplength=600)
        guide_label.pack(pady=10, fill="x")
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        # 下载FFmpeg按钮
        download_btn = ttk.Button(
            button_frame, 
            text="下载FFmpeg", 
            command=lambda: webbrowser.open("https://ffmpeg.org/download.html")
        )
        download_btn.pack(side="left", padx=10)
        
        # 检查安装按钮
        check_btn = ttk.Button(
            button_frame, 
            text="重新检查", 
            command=lambda: status_label.config(
                text="已安装 - " + FFmpegChecker.get_ffmpeg_version() if FFmpegChecker.check_ffmpeg() else "未安装",
                foreground="green" if FFmpegChecker.check_ffmpeg() else "red"
            )
        )
        check_btn.pack(side="left", padx=10)
        
        # 关闭按钮
        close_btn = ttk.Button(button_frame, text="关闭", command=window.destroy)
        close_btn.pack(side="left", padx=10)
        
        window.mainloop()

# 如果直接运行此文件，则显示安装指南
if __name__ == "__main__":
    FFmpegChecker.show_ffmpeg_guide()
