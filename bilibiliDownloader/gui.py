"""
图形界面模块 - 重写版本
"""
import os
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, Menu, messagebox
from typing import Optional, Dict

from config import DEFAULT_CONFIG
from utils import load_history, save_history, format_size
from downloader import VideoDownloader
from settings import SettingsManager
from login_helper import LoginHelper
from ffmpeg_checker import FFmpegChecker
from download_manager import download_manager

class DownloaderGUI:
    """B站下载器图形界面类"""
    
    def __init__(self):
        """初始化下载器GUI"""
        self.downloader: Optional[VideoDownloader] = None
        self.download_thread: Optional[threading.Thread] = None
        self.window = None
        self.progress_var = None
        self.progress_bar = None
        self.status_label = None
        self.url_var = None
        self.url_entry = None
        self.save_dir_var = None
        self.save_dir_entry = None
        self.quality_var = None
        self.download_button = None
        self.stop_button = None
        self.history_list = None
        self.task_tree = None
        self.task_progress = {}  # 存储任务进度信息
        self.status_map = {}     # 任务状态映射
        
    def create_main_window(self):
        """创建主窗口"""
        self.window = tk.Tk()
        self.window.title('Bilibili视频下载器')
        self.window.geometry('800x600')
        self.window.minsize(800, 600)
        
        # 创建菜单栏
        self._create_menu()

        # 主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)  # URL输入框列可拉伸

        # 标题和帮助信息
        title_label = ttk.Label(main_frame, text="Bilibili视频下载器", font=('Arial', 16))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        help_text = "支持的链接格式：\n1. 完整链接: https://www.bilibili.com/video/BVxxxxxx\n2. BV号: BVxxxxxx\n3. av号: av12345\n4. 短链接: https://b23.tv/xxxxx"
        help_label = ttk.Label(main_frame, text=help_text, justify=tk.LEFT)
        help_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

        # URL输入
        ttk.Label(main_frame, text="视频链接:").grid(row=2, column=0, sticky=tk.W)
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=60)
        self.url_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 粘贴按钮
        paste_btn = ttk.Button(main_frame, text="粘贴", width=6, 
                             command=self._paste_from_clipboard)
        paste_btn.grid(row=2, column=2, padx=5)

        # 画质选择
        ttk.Label(main_frame, text="画质选择:").grid(row=3, column=0, sticky=tk.W)
        self.quality_var = tk.StringVar(value="superhigh")
        
        quality_frame = ttk.Frame(main_frame)
        quality_frame.grid(row=3, column=1, columnspan=2, sticky=tk.W)
        
        # 第一行画质选项
        ttk.Radiobutton(quality_frame, text="超清 8K", variable=self.quality_var, 
                       value="ultra").grid(row=0, column=0, sticky=tk.W, padx=10)
        ttk.Radiobutton(quality_frame, text="超清 4K", variable=self.quality_var,
                       value="superhigh").grid(row=0, column=1, sticky=tk.W, padx=10)
        ttk.Radiobutton(quality_frame, text="高清 1080P60", variable=self.quality_var,
                       value="high").grid(row=0, column=2, sticky=tk.W, padx=10)
                       
        # 第二行画质选项
        ttk.Radiobutton(quality_frame, text="高清 1080P", variable=self.quality_var,
                       value="medium").grid(row=1, column=0, sticky=tk.W, padx=10)
        ttk.Radiobutton(quality_frame, text="高清 720P", variable=self.quality_var,
                       value="low").grid(row=1, column=1, sticky=tk.W, padx=10)
        
        # 画质说明文本
        quality_note = ttk.Label(quality_frame, text="(注：部分高画质需要大会员，程序会自动尝试最高可用画质)", font=("Arial", 8))
        quality_note.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))

        # 保存位置
        ttk.Label(main_frame, text="保存位置:").grid(row=4, column=0, sticky=tk.W)
        self.save_dir_var = tk.StringVar(value=DEFAULT_CONFIG['download_dir'])
        self.save_dir_entry = ttk.Entry(main_frame, textvariable=self.save_dir_var, width=50)
        self.save_dir_entry.grid(row=4, column=1, sticky=(tk.W, tk.E))
        
        # 注册保存位置验证函数
        self.save_dir_var.trace_add("write", self._validate_save_dir)
        
        # 浏览按钮
        browse_btn = ttk.Button(main_frame, text="浏览", command=self.browse_folder)
        browse_btn.grid(row=4, column=2, padx=5)

        # 进度条
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(main_frame, length=500, mode='determinate',
                                          variable=self.progress_var)
        self.progress_bar.grid(row=5, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        self.progress_bar.grid_remove()  # 初始隐藏

        # 状态标签
        self.status_label = ttk.Label(main_frame, text="", wraplength=500)
        self.status_label.grid(row=6, column=0, columnspan=3)

        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=5)
        
        self.download_button = ttk.Button(button_frame, text="开始下载", command=self.add_download_task)
        self.download_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="停止下载", command=self.stop_download)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        self.stop_button.pack_forget()  # 初始隐藏
        
        # 设置按钮
        self.settings_button = ttk.Button(button_frame, text="设置", command=self.open_settings)
        self.settings_button.pack(side=tk.LEFT, padx=5)

        # 下载任务列表
        self._init_download_list(main_frame)
        
        # 下载历史
        history_frame = ttk.LabelFrame(main_frame, text="下载历史", padding="5")
        history_frame.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.history_list = tk.Listbox(history_frame, height=6)
        self.history_list.pack(fill=tk.BOTH, expand=True)
        self.update_history_list()
        
        # 检查FFmpeg状态并显示提示
        self._check_ffmpeg()

        # 在窗口加载完成后检查登录状态
        self.window.after(1000, self._check_login_status)

        return self.window
        
    def _create_menu(self):
        """创建菜单栏"""
        menubar = Menu(self.window)
        
        # 文件菜单
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="设置", command=self.open_settings)
        file_menu.add_command(label="登录", command=self.open_login)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._quit)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        # 工具菜单
        tools_menu = Menu(menubar, tearoff=0)
        tools_menu.add_command(label="FFmpeg安装检查", command=self._open_ffmpeg_guide)
        tools_menu.add_command(label="清空下载历史", command=self._clear_history)
        menubar.add_cascade(label="工具", menu=tools_menu)
        
        # 帮助菜单
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="使用说明", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        self.window.config(menu=menubar)

    def _init_download_list(self, frame):
        """初始化下载列表区域"""
        # 创建下载列表框架
        list_frame = ttk.LabelFrame(frame, text="下载队列")
        list_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # 创建Treeview显示下载任务
        columns = ("状态", "文件名", "进度", "速度", "剩余时间")
        self.task_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=6)
        
        # 设置列宽和标题
        self.task_tree.column("状态", width=80, anchor="center")
        self.task_tree.column("文件名", width=300)
        self.task_tree.column("进度", width=80, anchor="center")
        self.task_tree.column("速度", width=100, anchor="center")
        self.task_tree.column("剩余时间", width=100, anchor="center")
        
        for col in columns:
            self.task_tree.heading(col, text=col)
        
        # 添加垂直滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        # 放置控件
        self.task_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 任务状态映射
        self.status_map = {
            "pending": "等待中...",
            "downloading": "下载中",
            "completed": "已完成",
            "failed": "失败",
            "canceled": "已取消"
        }
        
        # 添加任务控制按钮
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill="x", pady=5)
        
        # 清除完成任务按钮
        clear_btn = ttk.Button(button_frame, text="清除已完成", command=self._clear_completed_tasks)
        clear_btn.pack(side="right", padx=5)
        
        # 停止选中任务按钮
        cancel_btn = ttk.Button(button_frame, text="停止选中", command=self._cancel_selected_task)
        cancel_btn.pack(side="right", padx=5)
        
        # 设置下载管理器回调
        download_manager.set_status_callback(self.update_task_status)

    def run(self):
        """运行GUI程序"""
        self.window = self.create_main_window()
        
        # 添加窗口关闭处理
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # 启动主事件循环
        self.window.mainloop()

    def _on_closing(self):
        """窗口关闭时的处理"""
        if messagebox.askokcancel("退出", "确定要退出程序吗？\n正在进行的下载将被取消。"):
            # 关闭下载管理器
            download_manager.shutdown()
            # 销毁窗口
            self.window.destroy()

    def _quit(self):
        """退出程序"""
        self._on_closing()

    def _validate_save_dir(self, *args):
        """验证保存目录是否有效"""
        path = self.save_dir_var.get()
        try:
            from utils import ensure_dir
            ensure_dir(path)
            self.save_dir_entry.config(background="white")
        except Exception as e:
            print(f"Debug - 保存位置验证失败: {str(e)}")
            self.save_dir_entry.config(background="#ffe0e0")  # 轻微红色背景提示

    def browse_folder(self):
        """选择保存目录"""
        current_dir = self.save_dir_var.get()
        print(f"Debug - 当前保存目录: {current_dir}")
        
        # 检查当前目录是否存在
        if not os.path.exists(current_dir):
            # 尝试使用系统下载目录作为默认
            current_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            if not os.path.exists(current_dir):
                # 如果还不存在，使用当前工作目录
                current_dir = os.getcwd()
                
        folder = filedialog.askdirectory(initialdir=current_dir)
        if folder:
            print(f"Debug - 用户选择的新保存目录: {folder}")
            self.save_dir_var.set(folder)
            # 确保更新已应用到输入框
            self.save_dir_entry.update()
        else:
            print("Debug - 用户取消了目录选择")

    def update_progress(self, current_bytes: int):
        """更新下载进度"""
        if self.downloader and hasattr(self.downloader, 'total_size') and self.downloader.total_size > 0:
            percentage = min(100, int(current_bytes * 100 / self.downloader.total_size))
            self.progress_var.set(percentage)
            self.status_label["text"] = f'已下载: {format_size(current_bytes)} / {format_size(self.downloader.total_size)} ({percentage}%)'

    def update_history_list(self):
        """更新历史记录列表"""
        self.history_list.delete(0, tk.END)
        for item in self._format_history():
            self.history_list.insert(0, item)

    def _format_history(self) -> list:
        """格式化历史记录显示"""
        history = load_history()
        formatted = []
        for item in history:
            date = item.get('downloaded_at', '') or item.get('download_time', '未知时间')
            title = item.get('title', '未知标题')
            
            # 使用actual_quality来显示实际使用的画质
            quality = item.get('actual_quality', '未知画质')
                
            formatted.append(f"{date} - [{quality}] {title}")
        return formatted
    
    def _paste_from_clipboard(self):
        """从剪贴板粘贴内容并显示调试信息"""
        try:
            # 获取剪贴板内容
            clipboard_content = self.window.clipboard_get().strip()
            print(f"Debug - 从剪贴板获取的内容: '{clipboard_content}'")
            
            # 设置变量值
            self.url_var.set(clipboard_content)
            
            # 确保输入框内容已更新
            self.url_entry.update()
            
            # 打印当前输入框内容以验证
            current_content = self.url_var.get()
            print(f"Debug - 粘贴后URL输入框内容: '{current_content}'")
            
            # 清除错误状态
            self.url_entry.config(background="white")
            self.status_label.config(text=f"已粘贴链接: {clipboard_content[:30]}...", foreground="black")
        except Exception as e:
            print(f"Debug - 粘贴内容失败: {str(e)}")
            self.status_label.config(text=f"粘贴内容失败: {str(e)}", foreground="red")
    
    def add_download_task(self):
        """添加下载任务到队列"""
        # 获取输入值
        url = self.url_var.get().strip()
        save_dir = self.save_dir_var.get()
        quality = self.quality_var.get()
        
        # 先验证输入值是否有效
        from input_validator import validate_video_url, validate_save_dir
        
        # 验证URL
        url_valid, url_msg = validate_video_url(url)
        if not url_valid:
            self._show_error("无效的视频链接", url_msg)
            return
        
        # 验证保存目录
        dir_valid, dir_msg = validate_save_dir(save_dir)
        if not dir_valid:
            self._show_error("无效的保存目录", dir_msg)
            return
        
        if not url:
            self._show_error("输入错误", "请输入视频链接！\n\n提示：可以点击\"粘贴\"按钮从剪贴板粘贴内容。")
            self.url_entry.focus_set()
            self.url_entry.config(background="#ffe0e0")
            self.window.after(3000, lambda: self.url_entry.config(background="white"))
            return
            
        # 使用下载管理器添加任务
        task_id = download_manager.add_task(url, save_dir, quality)
        
        # 清空输入框，准备下一个任务
        self.url_var.set("")
        
        # 添加到任务列表
        self.task_tree.insert("", "end", task_id, values=(
            self.status_map["pending"], 
            f"正在获取: {url.split('/')[-1] if '/' in url else url}",
            "0%",
            "-",
            "-"
        ))
        
        # 初始化进度跟踪
        self.task_progress[task_id] = {
            'bytes': 0,
            'time': datetime.now(),
            'speed': "-"
        }
        
        # 状态提示
        self.status_label.config(text="任务已添加到下载队列", foreground="blue")
        
    def update_task_status(self, task_id, status, progress, result=None, error=None):
        """更新任务状态（下载管理器回调）"""
        if task_id not in self.task_progress:
            self.task_progress[task_id] = {
                'bytes': 0,
                'time': datetime.now(),
                'speed': "-"
            }
        
        # 获取任务
        task = download_manager.get_task(task_id)
        if not task:
            return
            
        # 更新状态显示
        status_text = self.status_map.get(status, status)
        
        # 处理不同状态
        if status == "downloading":
            # 初始化变量，确保在任何情况下都有值
            speed_text = "-"
            eta = "计算中..."
            
            # 计算下载速度
            current_time = datetime.now()
            last_update = self.task_progress[task_id]['time']
            if (current_time - last_update).total_seconds() >= 1:  # 至少1秒更新一次
                if hasattr(task.downloader, 'current_progress'):
                    current_bytes = task.downloader.current_progress
                    last_bytes = self.task_progress[task_id]['bytes']
                    bytes_diff = current_bytes - last_bytes
                    time_diff = (current_time - last_update).total_seconds()
                    
                    if time_diff > 0:
                        speed = bytes_diff / time_diff
                        
                        # 格式化速度显示
                        if speed < 1024:
                            speed_text = f"{speed:.1f} B/s"
                        elif speed < 1024 * 1024:
                            speed_text = f"{speed / 1024:.1f} KB/s"
                        else:
                            speed_text = f"{speed / (1024 * 1024):.1f} MB/s"
                        
                        self.task_progress[task_id]['speed'] = speed_text
                        
                        # 计算剩余时间
                        if speed > 0 and hasattr(task.downloader, 'total_size') and task.downloader.total_size > 0:
                            remaining_bytes = task.downloader.total_size - current_bytes
                            remaining_seconds = remaining_bytes / speed
                            
                            # 格式化剩余时间
                            if remaining_seconds < 60:
                                eta = f"{int(remaining_seconds)}秒"
                            elif remaining_seconds < 3600:
                                eta = f"{int(remaining_seconds / 60)}分钟"
                            else:
                                eta = f"{int(remaining_seconds / 3600)}小时{int((remaining_seconds % 3600) / 60)}分钟"
                    else:
                        # 如果时间差为0，使用上次的速度
                        speed_text = self.task_progress[task_id]['speed']
                    
                    self.task_progress[task_id]['bytes'] = current_bytes
                    self.task_progress[task_id]['time'] = current_time
                
                # 如果没有当前进度属性，使用默认值
                else:
                    speed_text = "-"
            else:
                # 更新间隔不够1秒，使用上次的速度
                speed_text = self.task_progress[task_id]['speed']
            
            # 更新显示
            self.task_tree.item(task_id, values=(status_text, task.url.split('/')[-1] if '/' in task.url else task.url, f"{progress}%", speed_text, eta))
            
        elif status == "completed" and result:
            # 完成时显示文件名
            filename = os.path.basename(result['save_path'])
            self.task_tree.item(task_id, values=(status_text, filename, "100%", "-", "-"))
            
            # 可选：播放提示音
            import winsound
            winsound.MessageBeep(winsound.MB_OK)
            
            # 更新历史记录列表
            self.update_history_list()
            
            # 显示降级提示
            if result.get('degradation_info'):
                info = result['degradation_info']
                messagebox.showinfo(
                    "画质降级提示", 
                    f"视频已降级: 从 {info['requested_name']} 降级为 {info['current_name']}\n\n原因: {info['reason']}"
                )
            
        elif status == "failed":
            # 显示错误信息
            error_short = error[:30] + "..." if len(error) > 30 else error
            self.task_tree.item(task_id, values=(status_text, error_short, "-", "-", "-"))
            
        else:
            # 其他状态
            self.task_tree.item(task_id, values=(status_text, task.url.split('/')[-1] if '/' in task.url else task.url, f"{progress}%", "-", "-"))
    
    def _clear_completed_tasks(self):
        """清除已完成任务"""
        # 获取所有任务
        for task_id in list(self.task_tree.get_children()):
            item = self.task_tree.item(task_id)
            status = item['values'][0]
            if status in ["已完成", "已取消", "失败"]:
                self.task_tree.delete(task_id)
                if task_id in self.task_progress:
                    del self.task_progress[task_id]
    
    def _cancel_selected_task(self):
        """取消选中的下载任务"""
        selected_items = self.task_tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请先选择要停止的任务")
            return
            
        for task_id in selected_items:
            download_manager.cancel_task(task_id)
    
    def start_download(self):
        """单文件下载（旧方法，保留用于兼容）"""
        self.add_download_task()  # 转为使用下载管理器
    
    def stop_download(self):
        """停止下载"""
        # 获取所有选中的任务
        selected_items = self.task_tree.selection()
        if selected_items:
            # 如果有选中的任务，停止它们
            for task_id in selected_items:
                download_manager.cancel_task(task_id)
        else:
            # 如果没有选中的任务，尝试停止最老的正在下载的任务
            for task_id in self.task_tree.get_children():
                item = self.task_tree.item(task_id)
                status = item['values'][0]
                if status == "下载中":
                    download_manager.cancel_task(task_id)
                    break
    
    def _show_error(self, title, message):
        """显示错误提示"""
        messagebox.showerror(title, message)
        self.status_label.config(text=f"错误: {title}", foreground="red")

    def open_settings(self):
        """打开设置窗口"""
        settings = SettingsManager()
        settings.show_settings_window()
        # 重新加载配置
        from config import load_user_config, DEFAULT_CONFIG
        user_config = load_user_config()
        self.save_dir_var.set(user_config.get("download_dir", DEFAULT_CONFIG["download_dir"]))
        self.quality_var.set(user_config.get("default_quality", DEFAULT_CONFIG["default_quality"]))

    def open_login(self):
        """打开登录助手"""
        helper = LoginHelper()
        helper.show_login_guide()
        # 登录窗口关闭后检查是否有新的登录信息
        self._check_login_status()

    def _check_login_status(self):
        """检查登录状态"""
        from config import load_user_config
        user_config = load_user_config()
        if user_config.get('sessdata'):
            self.status_label.config(text="已登录状态", foreground="green")
        else:
            self.status_label.config(text="未登录状态", foreground="orange")

    def _check_ffmpeg(self):
        """检查FFmpeg状态并显示提示"""
        if not FFmpegChecker.check_ffmpeg():
            self.status_label.config(
                text="⚠️ 未检测到FFmpeg，高画质视频可能无法正常下载。请在'工具'菜单中安装FFmpeg。",
                foreground="red"
            )

    def _open_ffmpeg_guide(self):
        """打开FFmpeg安装指南"""
        FFmpegChecker.show_ffmpeg_guide()

    def _clear_history(self):
        """清空下载历史"""
        if messagebox.askyesno("确认", "确定要清空所有下载历史记录吗？"):
            try:
                from config import HISTORY_FILE
                if os.path.exists(HISTORY_FILE):
                    os.remove(HISTORY_FILE)
                self.update_history_list()
                self.status_label.config(text="下载历史已清空", foreground="blue")
            except Exception as e:
                messagebox.showerror("错误", f"清空历史失败: {str(e)}")

    def _show_help(self):
        """显示使用说明"""
        help_window = tk.Toplevel(self.window)
        help_window.title("使用说明")
        help_window.geometry("600x500")
        help_window.minsize(600, 400)
        
        help_frame = ttk.Frame(help_window, padding=20)
        help_frame.pack(fill="both", expand=True)
        
        # 标题
        title_label = ttk.Label(help_frame, text="Bilibili视频下载器使用说明", font=('Arial', 14, 'bold'))
        title_label.pack(pady=10)
        
        # 内容
        help_text = """
1. 基本使用：
   - 复制B站视频链接，粘贴到"视频链接"输入框
   - 选择想要的视频画质
   - 选择保存位置
   - 点击"开始下载"按钮

2. 画质说明：
   - 8K、4K等高画质需要登录大会员账号
   - 可以在"文件"菜单的"登录"中设置账号
   - 如果指定画质不可用，将自动降级到可用的最高画质

3. 下载目录：
   - 点击"浏览"按钮可以更改保存位置
   - 默认保存在系统下载目录的bilibili_videos文件夹中

4. 高画质视频支持：
   - 高画质视频下载需要安装FFmpeg
   - 可以在"工具"菜单中查看FFmpeg安装指南

5. 其他功能：
   - 设置：可以在"文件"菜单中调整下载参数
   - 下载历史：主界面底部会显示历史下载记录
   - 下载队列：可以同时添加多个下载任务
"""
        help_content = tk.Text(help_frame, wrap="word", height=20, width=70)
        help_content.pack(fill="both", expand=True, pady=10)
        help_content.insert("1.0", help_text)
        help_content.config(state="disabled")  # 设为只读
        
        # 关闭按钮
        close_btn = ttk.Button(help_frame, text="关闭", command=help_window.destroy)
        close_btn.pack(pady=10)

    def _show_about(self):
        """显示关于信息"""
        about_window = tk.Toplevel(self.window)
        about_window.title("关于")
        about_window.geometry("400x300")
        
        about_frame = ttk.Frame(about_window, padding=20)
        about_frame.pack(fill="both", expand=True)
        
        # 标题和版本
        title_label = ttk.Label(about_frame, text="Bilibili视频下载器", font=('Arial', 14, 'bold'))
        title_label.pack(pady=5)
        version_label = ttk.Label(about_frame, text="版本 1.0")
        version_label.pack()
        
        # 描述
        desc_text = """
一个简单易用的B站视频下载工具，支持多种画质和登录功能。

特性：
- 支持最高8K画质下载（需登录大会员）
- 多线程并发下载，速度更快
- 自动画质降级确保下载成功
- 下载历史记录与管理
- 多任务队列下载
"""
        desc_label = ttk.Label(about_frame, text=desc_text, justify="center", wraplength=350)
        desc_label.pack(pady=10)
        
        # 关闭按钮
        close_btn = ttk.Button(about_frame, text="关闭", command=about_window.destroy)
        close_btn.pack(pady=10)
