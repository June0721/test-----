"""
设置管理模块
"""
import os
import sys
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from config import DEFAULT_CONFIG, USER_CONFIG, save_user_config, load_user_config, update_config
from login_helper import LoginHelper
from ffmpeg_checker import FFmpegChecker

class SettingsManager:
    """设置管理类"""
    
    def __init__(self):
        self.user_config = load_user_config()
        self.temp_config = {**DEFAULT_CONFIG, **self.user_config}
        
    def show_settings_window(self):
        """显示设置窗口"""
        window = tk.Tk()
        window.title("下载器设置")
        window.geometry("700x600")
        
        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 常规设置选项卡
        general_tab = ttk.Frame(notebook, padding=20)
        notebook.add(general_tab, text="常规设置")
        
        # 账号设置选项卡
        account_tab = ttk.Frame(notebook, padding=20)
        notebook.add(account_tab, text="账号设置")
        
        # 高级设置选项卡
        advanced_tab = ttk.Frame(notebook, padding=20)
        notebook.add(advanced_tab, text="高级设置")
        
        # 常规设置内容
        self._create_general_settings(general_tab)
        
        # 账号设置内容
        self._create_account_settings(account_tab)
        
        # 高级设置内容
        self._create_advanced_settings(advanced_tab)
        
        # 底部按钮
        button_frame = ttk.Frame(window)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        save_btn = ttk.Button(button_frame, text="保存设置", command=lambda: self._save_settings(window))
        save_btn.pack(side="right", padx=5)
        
        cancel_btn = ttk.Button(button_frame, text="取消", command=window.destroy)
        cancel_btn.pack(side="right", padx=5)
        
        reset_btn = ttk.Button(button_frame, text="恢复默认", command=self._reset_settings)
        reset_btn.pack(side="left", padx=5)
        
        window.mainloop()
    
    def _create_general_settings(self, parent):
        """创建常规设置界面"""
        # 下载目录
        dir_frame = ttk.Frame(parent)
        dir_frame.pack(fill="x", pady=5)
        
        ttk.Label(dir_frame, text="下载目录:").grid(row=0, column=0, sticky="w", pady=5)
        self.save_dir_var = tk.StringVar(value=self.temp_config.get("download_dir", DEFAULT_CONFIG["download_dir"]))
        save_dir_entry = ttk.Entry(dir_frame, textvariable=self.save_dir_var, width=50)
        save_dir_entry.grid(row=0, column=1, sticky="we", padx=5)
        
        browse_btn = ttk.Button(dir_frame, text="浏览", command=self._browse_folder)
        browse_btn.grid(row=0, column=2, padx=5)
        
        # 默认画质
        quality_frame = ttk.LabelFrame(parent, text="默认画质")
        quality_frame.pack(fill="x", pady=10)
        
        self.quality_var = tk.StringVar(value=self.temp_config.get("default_quality", DEFAULT_CONFIG["default_quality"]))
        
        qualities = [
            ("超清 8K", "ultra"),
            ("超清 4K", "superhigh"),
            ("高清 1080P60", "high"),
            ("高清 1080P", "medium"),
            ("高清 720P", "low")
        ]
        
        for i, (text, value) in enumerate(qualities):
            ttk.Radiobutton(
                quality_frame, 
                text=text, 
                value=value,
                variable=self.quality_var
            ).pack(anchor="w", padx=20, pady=2)
        
        # 注意标签
        note_text = "注意：4K、8K等高画质需要大会员账号\n且需要在\"账号设置\"标签页中配置登录凭证"
        ttk.Label(quality_frame, text=note_text, foreground="red").pack(pady=5)
        
        # 调试模式
        debug_frame = ttk.Frame(parent)
        debug_frame.pack(fill="x", pady=10)
        
        self.debug_var = tk.BooleanVar(value=self.temp_config.get("debug", DEFAULT_CONFIG["debug"]))
        debug_check = ttk.Checkbutton(debug_frame, text="启用调试模式 (显示更多下载信息)", variable=self.debug_var)
        debug_check.pack(anchor="w")
    
    def _create_account_settings(self, parent):
        """创建账号设置界面"""
        # 账号状态
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill="x", pady=5)
        
        ttk.Label(status_frame, text="登录状态:").pack(side="left")
        
        login_status = "已登录" if self.temp_config.get("sessdata") else "未登录"
        status_color = "green" if self.temp_config.get("sessdata") else "red"
        
        self.status_label = ttk.Label(status_frame, text=login_status, foreground=status_color)
        self.status_label.pack(side="left", padx=5)
        
        # 登录助手按钮
        login_btn = ttk.Button(parent, text="打开登录助手", command=self._open_login_helper)
        login_btn.pack(anchor="w", pady=10)
        
        # 登录信息显示
        info_frame = ttk.LabelFrame(parent, text="当前登录信息")
        info_frame.pack(fill="x", pady=10)
        
        # SESSDATA (部分隐藏)
        sessdata = self.temp_config.get("sessdata", "")
        masked_sessdata = self._mask_string(sessdata)
        
        ttk.Label(info_frame, text="SESSDATA:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Label(info_frame, text=masked_sessdata).grid(row=0, column=1, sticky="w", padx=5)
        
        # bili_jct (部分隐藏)
        bili_jct = self.temp_config.get("bili_jct", "")
        masked_bili_jct = self._mask_string(bili_jct)
        
        ttk.Label(info_frame, text="bili_jct:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Label(info_frame, text=masked_bili_jct).grid(row=1, column=1, sticky="w", padx=5)
        
        # 最后更新时间
        last_updated = self.temp_config.get("last_updated", "从未")
        ttk.Label(info_frame, text="最后更新:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Label(info_frame, text=last_updated).grid(row=2, column=1, sticky="w", padx=5)
        
        # 安全提示
        security_text = """
安全提示:
1. 登录信息等同于您在B站的账号密码，请勿分享给他人
2. 所有信息仅保存在您的计算机上，不会上传到任何服务器
3. 定期更新登录凭证以保持高画质下载能力
        """
        security_label = ttk.Label(parent, text=security_text, justify="left", wraplength=650)
        security_label.pack(fill="x", pady=10)
    
    def _create_advanced_settings(self, parent):
        """创建高级设置界面"""
        # 线程设置
        thread_frame = ttk.Frame(parent)
        thread_frame.pack(fill="x", pady=5)
        
        ttk.Label(thread_frame, text="下载线程数:").grid(row=0, column=0, sticky="w", pady=5)
        
        thread_values = list(range(1, 17))  # 1-16线程
        self.thread_var = tk.IntVar(value=self.temp_config.get("thread_count", DEFAULT_CONFIG["thread_count"]))
        thread_combo = ttk.Combobox(thread_frame, values=thread_values, textvariable=self.thread_var, width=5)
        thread_combo.grid(row=0, column=1, sticky="w", padx=5)
        
        thread_note = ttk.Label(thread_frame, text="(更多线程可能加快下载速度，但也可能导致不稳定)")
        thread_note.grid(row=0, column=2, sticky="w", padx=5)
        
        # 分块大小
        chunk_frame = ttk.Frame(parent)
        chunk_frame.pack(fill="x", pady=5)
        
        ttk.Label(chunk_frame, text="分块大小:").grid(row=0, column=0, sticky="w", pady=5)
        
        chunk_sizes = ["512KB", "1MB", "2MB", "4MB", "8MB"]
        chunk_values = [512*1024, 1024*1024, 2*1024*1024, 4*1024*1024, 8*1024*1024]
        
        current_chunk = self.temp_config.get("chunk_size", DEFAULT_CONFIG["chunk_size"])
        current_index = chunk_values.index(current_chunk) if current_chunk in chunk_values else 1
        
        self.chunk_var = tk.StringVar(value=chunk_sizes[current_index])
        chunk_combo = ttk.Combobox(chunk_frame, values=chunk_sizes, textvariable=self.chunk_var, width=5)
        chunk_combo.grid(row=0, column=1, sticky="w", padx=5)
        
        # FFmpeg设置
        ffmpeg_frame = ttk.LabelFrame(parent, text="FFmpeg设置")
        ffmpeg_frame.pack(fill="x", pady=10)
        
        # 检查FFmpeg是否已安装
        is_installed = FFmpegChecker.check_ffmpeg()
        status_text = "已安装" if is_installed else "未安装"
        status_color = "green" if is_installed else "red"
        
        ttk.Label(ffmpeg_frame, text="FFmpeg状态:").grid(row=0, column=0, sticky="w", pady=5)
        ffmpeg_status = ttk.Label(ffmpeg_frame, text=status_text, foreground=status_color)
        ffmpeg_status.grid(row=0, column=1, sticky="w", padx=5)
        
        if is_installed:
            version_text = FFmpegChecker.get_ffmpeg_version()
            ttk.Label(ffmpeg_frame, text="版本:").grid(row=1, column=0, sticky="w", pady=5)
            ttk.Label(ffmpeg_frame, text=version_text).grid(row=1, column=1, sticky="w", padx=5)
        
        ffmpeg_btn = ttk.Button(ffmpeg_frame, text="FFmpeg安装指南", command=FFmpegChecker.show_ffmpeg_guide)
        ffmpeg_btn.grid(row=2, column=0, columnspan=2, sticky="w", pady=10)
        
        # 说明文本
        note_text = """
FFmpeg用于将B站的视频流和音频流合并为完整的MP4文件。
当下载高质量视频时，B站会分别提供视频和音频文件，需要FFmpeg进行合并。
如果未安装FFmpeg，高画质视频将无法正常合并。
        """
        note_label = ttk.Label(ffmpeg_frame, text=note_text, justify="left", wraplength=650)
        note_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=5)
    
    def _browse_folder(self):
        """选择文件夹"""
        folder = filedialog.askdirectory(initialdir=self.save_dir_var.get())
        if folder:
            self.save_dir_var.set(folder)
    
    def _mask_string(self, text: str) -> str:
        """部分隐藏字符串，用于显示敏感信息"""
        if not text:
            return "未设置"
        if len(text) <= 8:
            return "*" * len(text)
        return text[:3] + "*" * (len(text) - 6) + text[-3:]
    
    def _save_settings(self, window):
        """保存设置"""
        try:
            # 获取所有设置值
            download_dir = self.save_dir_var.get()
            quality = self.quality_var.get()
            debug_mode = self.debug_var.get()
            thread_count = self.thread_var.get()
            
            # 解析分块大小
            chunk_size_str = self.chunk_var.get()
            chunk_sizes = {"512KB": 512*1024, "1MB": 1024*1024, "2MB": 2*1024*1024, 
                       "4MB": 4*1024*1024, "8MB": 8*1024*1024}
            chunk_size = chunk_sizes.get(chunk_size_str, 1024*1024)
            
            # 创建配置对象
            new_config = {
                "download_dir": download_dir,
                "default_quality": quality,
                "debug": debug_mode,
                "thread_count": thread_count,
                "chunk_size": chunk_size
            }
            
            # 保留登录信息
            for key in ["sessdata", "bili_jct", "buvid3", "last_updated"]:
                if key in self.user_config:
                    new_config[key] = self.user_config[key]
            
            # 验证设置
            if not os.path.exists(download_dir):
                try:
                    os.makedirs(download_dir)
                except Exception as e:
                    messagebox.showerror("错误", f"无法创建下载目录: {str(e)}")
                    return
            
            # 保存设置
            save_user_config(new_config)
            self.user_config = new_config
            self.temp_config = new_config.copy()
            
            messagebox.showinfo("成功", "设置已保存")
            window.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"保存设置失败: {str(e)}")
    
    def _reset_settings(self):
        """恢复默认设置"""
        if messagebox.askyesno("确认", "确定要恢复所有设置到默认值吗？\n(注意: 不会清除登录信息)"):
            # 保留登录信息
            login_info = {}
            for key in ["sessdata", "bili_jct", "buvid3", "last_updated"]:
                if key in self.user_config:
                    login_info[key] = self.user_config[key]
            
            # 重置其他设置
            self.save_dir_var.set(DEFAULT_CONFIG["download_dir"])
            self.quality_var.set(DEFAULT_CONFIG["default_quality"])
            self.debug_var.set(DEFAULT_CONFIG["debug"])
            self.thread_var.set(DEFAULT_CONFIG["thread_count"])
            
            # 设置分块大小
            chunk_size = DEFAULT_CONFIG["chunk_size"]
            chunk_sizes = [512*1024, 1024*1024, 2*1024*1024, 4*1024*1024, 8*1024*1024]
            chunk_size_text = ["512KB", "1MB", "2MB", "4MB", "8MB"]
            if chunk_size in chunk_sizes:
                index = chunk_sizes.index(chunk_size)
                self.chunk_var.set(chunk_size_text[index])
            else:
                self.chunk_var.set("1MB")
    
    def _open_login_helper(self):
        """打开登录助手"""
        helper = LoginHelper()
        helper.show_login_guide()
        
        # 重新加载登录信息以反映可能的更改
        new_config = load_user_config()
        if new_config.get("sessdata"):
            self.status_label.config(text="已登录", foreground="green")
        else:
            self.status_label.config(text="未登录", foreground="red")

# 如果直接运行此文件，启动设置管理界面
if __name__ == "__main__":
    manager = SettingsManager()
    manager.show_settings_window()