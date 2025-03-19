"""
B站登录助手，帮助用户获取登录凭证
"""
import os
import sys
import json
import time
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import requests
from config import CONFIG_FILE, DEFAULT_CONFIG, save_user_config, load_user_config

class LoginHelper:
    def __init__(self, cli_mode=False):
        self.user_config = load_user_config()
        self.window = None
        self.cli_mode = cli_mode
        
    def show_login_guide(self):
        """显示登录指引窗口"""
        self.window = tk.Tk()
        self.window.title("B站登录助手")
        self.window.geometry("700x650")  # 增加高度以容纳新的元素
        self.window.resizable(True, True)
        
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="B站登录凭证获取指南", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # 说明文本
        guide_text = """
要下载高画质视频，需要大会员账号和登录凭证。请按以下步骤操作：

1. 点击"打开B站"按钮，用浏览器打开B站并登录您的账号
2. 在浏览器中按F12打开开发者工具，选择"应用程序/Application"标签
3. 在左侧找到"Cookie"，展开并选择"https://www.bilibili.com"
4. 在Cookie列表中找到以下三个值并复制到下方对应输入框：
   - SESSDATA
   - bili_jct
   - buvid3

注意：这些信息等同于您的登录状态，请勿分享给他人！
程序只会保存在本地配置文件中，仅用于视频下载。
        """
        guide_label = ttk.Label(main_frame, text=guide_text, justify="left", wraplength=650)
        guide_label.pack(pady=10, fill="x")
        
        # 打开B站按钮
        open_btn = ttk.Button(main_frame, text="打开B站", command=lambda: webbrowser.open("https://www.bilibili.com"))
        open_btn.pack(pady=10)
        
        # 输入框 - 不使用StringVar绑定，直接使用Entry
        input_frame = ttk.LabelFrame(main_frame, text="登录凭证信息", padding=10)
        input_frame.pack(fill="x", pady=10)
        
        # SESSDATA
        ttk.Label(input_frame, text="SESSDATA: (必填)").grid(row=0, column=0, sticky="w", pady=5)
        # 使用正常的Entry而不是ttk.Entry，某些情况下ttk样式可能导致问题
        self.sessdata_entry = tk.Entry(input_frame, width=50)
        self.sessdata_entry.grid(row=0, column=1, sticky="we", padx=5)
        # 如果有已保存的值，预填入输入框
        if self.user_config.get("sessdata"):
            self.sessdata_entry.insert(0, self.user_config.get("sessdata"))
        
        # bili_jct
        ttk.Label(input_frame, text="bili_jct:").grid(row=1, column=0, sticky="w", pady=5)
        self.bili_jct_entry = tk.Entry(input_frame, width=50)
        self.bili_jct_entry.grid(row=1, column=1, sticky="we", padx=5)
        if self.user_config.get("bili_jct"):
            self.bili_jct_entry.insert(0, self.user_config.get("bili_jct"))
        
        # buvid3
        ttk.Label(input_frame, text="buvid3:").grid(row=2, column=0, sticky="w", pady=5)
        self.buvid3_entry = tk.Entry(input_frame, width=50)
        self.buvid3_entry.grid(row=2, column=1, sticky="we", padx=5)
        if self.user_config.get("buvid3"):
            self.buvid3_entry.insert(0, self.user_config.get("buvid3"))
        
        # 登录状态信息
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill="x", pady=10)
        
        ttk.Label(status_frame, text="当前状态:").pack(side="left")
        self.status_label = ttk.Label(status_frame, text="未登录", foreground="red")
        self.status_label.pack(side="left", padx=5)
        
        if self.user_config.get("sessdata"):
            last_updated = self.user_config.get("last_updated", "未知时间")
            self.status_label.config(text=f"已保存登录信息 (更新时间: {last_updated})", foreground="green")
        
        # 按钮框架 - 使用更明显的布局
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20, fill="x")
        
        # 保存按钮 - 使用主要颜色突出显示
        self.save_btn = ttk.Button(button_frame, text="保存登录信息", command=self.save_login_info)
        self.save_btn.pack(side="top", fill="x", pady=5)
        
        # 其他按钮行
        sub_button_frame = ttk.Frame(button_frame)
        sub_button_frame.pack(fill="x", pady=5)
        
        # 测试按钮
        test_btn = ttk.Button(sub_button_frame, text="测试登录状态", command=self.test_login)
        test_btn.pack(side="left", padx=5, expand=True, fill="x")
        
        # 清除按钮
        clear_btn = ttk.Button(sub_button_frame, text="清除登录信息", command=self.clear_login_info)
        clear_btn.pack(side="left", padx=5, expand=True, fill="x")
        
        # 关闭按钮
        close_btn = ttk.Button(sub_button_frame, text="关闭", command=self.window.destroy)
        close_btn.pack(side="left", padx=5, expand=True, fill="x")
        
        # 保存信息提示框
        save_info_frame = ttk.LabelFrame(main_frame, text="保存说明", padding=10)
        save_info_frame.pack(fill="x", pady=10)
        
        save_info_text = """
1. 输入凭证后点击"保存登录信息"立即生效，无需重启程序
2. 登录凭证会保存在程序目录下的user_config.json文件中
3. 凭证有效期通常为1个月，过期后需重新获取
4. 保存后可点击"测试登录状态"验证凭证是否有效
        """
        save_info_label = ttk.Label(save_info_frame, text=save_info_text, justify="left", wraplength=650)
        save_info_label.pack(pady=5)
        
        # 帮助说明
        help_text = """
常见问题:
1. 如何知道我的登录信息是否有效？
   点击"测试登录状态"按钮可以验证。

2. 获取Cookie后能下什么画质？
   - 普通会员：最高1080P
   - 大会员：最高可达4K、8K、杜比视界等
   
3. 信息保存在哪里？
   所有信息仅保存在本地的user_config.json文件中。
        """
        help_label = ttk.Label(main_frame, text=help_text, justify="left", wraplength=650)
        help_label.pack(pady=10, fill="x")
        
        # 尝试创建强调样式
        try:
            style = ttk.Style()
            style.configure("Accent.TButton", font=('Arial', 10, 'bold'))
            self.save_btn.configure(style="Accent.TButton")
        except Exception as e:
            print(f"无法应用样式: {e}")
        
        self.window.mainloop()
    
    def save_login_info(self):
        """保存登录信息"""
        # 直接从输入框获取内容，而不是通过StringVar
        sessdata = self.sessdata_entry.get().strip() if hasattr(self, 'sessdata_entry') else ""
        bili_jct = self.bili_jct_entry.get().strip() if hasattr(self, 'bili_jct_entry') else ""
        buvid3 = self.buvid3_entry.get().strip() if hasattr(self, 'buvid3_entry') else ""
        
        # 添加对粘贴内容的预处理
        sessdata = self._preprocess_cookie_value(sessdata)
        
        # 额外打印原始文本，帮助调试
        print(f"Debug - 原始SESSDATA内容: '{sessdata}'")
        print(f"Debug - 准备保存登录信息")
        print(f"Debug - SESSDATA长度: {len(sessdata)}")
        print(f"Debug - bili_jct长度: {len(bili_jct)}")
        print(f"Debug - buvid3长度: {len(buvid3)}")
        
        # 确保SESSDATA不为空
        if not sessdata:
            # 添加的调试步骤，检查输入框中文本是否真的为空
            try:
                actual_content = repr(self.sessdata_entry.get())
                print(f"Debug - 输入框实际内容: {actual_content}")
                
                # 尝试其他方法获取内容
                self.sessdata_entry.update()
                updated_content = self.sessdata_entry.get()
                print(f"Debug - 更新后的输入框内容: {repr(updated_content)}")
                
                if updated_content and updated_content.strip():
                    # 如果更新后能获得内容，就使用这个内容
                    sessdata = updated_content.strip()
                    print(f"Debug - 使用更新后获取的内容: '{sessdata}'")
                    
                else:
                    from tkinter import messagebox
                    messagebox.showerror("错误", f"必须填写SESSDATA! 当前值为空。\n调试信息: 实际内容='{actual_content}'")
                    return
            except Exception as e:
                print(f"Debug - 检查输入框内容时出错: {str(e)}")
                from tkinter import messagebox
                messagebox.showerror("错误", "必须填写SESSDATA!")
                return
        
        # 额外检查SESSDATA格式是否正确
        if not self._validate_sessdata(sessdata):
            from tkinter import messagebox
            messagebox.showerror(
                "错误", 
                "SESSDATA格式不正确。B站的SESSDATA通常包含字母、数字、特殊符号且长度较长。\n"
                "请确保完整复制了cookie值。"
            )
            return
            
        # 更新配置
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.user_config.update({
            "sessdata": sessdata,
            "bili_jct": bili_jct,
            "buvid3": buvid3,
            "last_updated": timestamp
        })
        
        # 保存配置到文件
        try:
            # 调用保存函数前先打印配置信息
            print(f"Debug - 即将保存配置: sessdata长度={len(sessdata)}, bili_jct长度={len(bili_jct)}")
            
            # 更新全局配置
            DEFAULT_CONFIG["sessdata"] = sessdata
            DEFAULT_CONFIG["bili_jct"] = bili_jct
            DEFAULT_CONFIG["buvid3"] = buvid3
            
            # 保存到文件
            save_user_config(self.user_config)
            
            # 更新状态标签
            if hasattr(self, 'status_label'):
                self.status_label.config(text=f"已保存登录信息 (更新时间: {timestamp})", foreground="green")
            
            # 显示保存位置和更多信息
            info_text = f"登录信息已保存至: {os.path.abspath(CONFIG_FILE)}"
            print(f"Debug - {info_text}")
            
            # 测试保存是否成功
            saved_config = load_user_config()
            if saved_config.get("sessdata") == sessdata:
                print("Debug - 验证成功：配置已正确保存")
            else:
                print(f"Debug - 验证失败：保存的SESSDATA与当前不匹配")
                print(f"Debug - 保存的SESSDATA长度: {len(saved_config.get('sessdata', ''))}")
            
            # 添加验证按钮，鼓励用户验证凭证是否有效
            from tkinter import messagebox
            messagebox.showinfo(
                "保存成功", 
                "登录信息已成功保存!\n\n"
                "提示: 请点击「测试登录状态」按钮验证凭证是否有效。\n"
                "保存后即时生效，现在可以下载高画质视频了。"
            )
            
            # 闪烁按钮提示用户测试登录状态
            self._flash_button()
            
        except Exception as e:
            import traceback
            print(f"Debug - 保存登录信息时出错: {str(e)}")
            print(traceback.format_exc())
            from tkinter import messagebox
            messagebox.showerror("错误", f"保存登录信息时出错: {str(e)}")

    def _preprocess_cookie_value(self, value):
        """预处理Cookie值，处理常见的粘贴问题"""
        if not value:
            return ""
            
        # 处理可能的"name=value"格式
        if value.startswith("SESSDATA="):
            value = value.split("=", 1)[1].strip()
            
        # 处理多行粘贴的情况
        value = value.replace("\n", "").replace("\r", "")
        
        # 处理引号和额外空格
        value = value.strip('"\'').strip()
        
        # 处理可能的分号结尾(从完整cookie复制)
        if value.endswith(';'):
            value = value[:-1]
            
        return value

    def _validate_sessdata(self, sessdata: str) -> bool:
        """验证SESSDATA是否有效"""
        # SESSDATA通常是一长串字符，包含字母数字和特殊符号
        # 简单验证长度和基本格式
        if len(sessdata) < 10:  # SESSDATA通常很长
            return False
        
        # 通常包含%等URL编码字符
        if not any(c in sessdata for c in ['%', '_', '-']):
            # 至少包含一些特殊字符
            if not (any(c.isdigit() for c in sessdata) and any(c.isalpha() for c in sessdata)):
                return False
        
        return True
        
    def clear_login_info(self):
        """清除登录信息"""
        if messagebox.askyesno("确认", "确定要清除所有登录信息吗？"):
            self.sessdata_entry.delete(0, tk.END)
            self.bili_jct_entry.delete(0, tk.END)
            self.buvid3_entry.delete(0, tk.END)
            
            self.user_config.update({
                "sessdata": "",
                "bili_jct": "",
                "buvid3": ""
            })
            
            try:
                save_user_config(self.user_config)
                self.status_label.config(text="未登录", foreground="red")
                messagebox.showinfo("成功", "登录信息已清除")
                
                # 更新全局登录状态
                self._update_global_login_status()
            except Exception as e:
                messagebox.showerror("错误", f"清除登录信息时出错: {str(e)}")
    
    def test_login(self):
        """测试登录状态"""
        # 直接从输入框获取内容
        sessdata = self.sessdata_entry.get().strip() if hasattr(self, 'sessdata_entry') else ""
        bili_jct = self.bili_jct_entry.get().strip() if hasattr(self, 'bili_jct_entry') else ""
        buvid3 = self.buvid3_entry.get().strip() if hasattr(self, 'buvid3_entry') else ""
        
        if not sessdata:
            from tkinter import messagebox
            messagebox.showerror("错误", "请先填写SESSDATA! 当前值为空。")
            return
        
        # 读取用户配置
        bili_jct = self.bili_jct_entry.get().strip() if hasattr(self, 'bili_jct_entry') else ""
        buvid3 = self.buvid3_entry.get().strip() if hasattr(self, 'buvid3_entry') else ""
        
        # 准备Cookies
        cookies = {
            'SESSDATA': sessdata,
            'bili_jct': bili_jct,
            'buvid3': buvid3
        }
        
        print(f"Debug - 测试登录使用的cookies: SESSDATA长度={len(cookies['SESSDATA'])}, bili_jct长度={len(cookies['bili_jct'])}")
        
        try:
            # 使用B站用户信息API测试登录状态
            import requests
            response = requests.get(
                "https://api.bilibili.com/x/web-interface/nav",
                cookies=cookies,
                timeout=10
            )
            data = response.json()
            
            print(f"Debug - 登录测试API返回: {data}")
            
            if data.get("code") == 0 and data.get("data", {}).get("isLogin"):
                user_info = data.get("data", {})
                username = user_info.get("uname", "用户")
                vip_status = user_info.get("vipStatus", 0)
                vip_type = user_info.get("vipType", 0)
                
                # 登录成功，更新全局配置
                self._force_update_login_info(sessdata, bili_jct, buvid3)
                
                if vip_type > 0:
                    if hasattr(self, 'window'):
                        messagebox.showinfo("登录成功", f"已登录为: {username}\n当前为大会员账号，可下载高画质视频")
                    else:
                        print(f"\n✅ 已登录为: {username} (大会员账号)")
                    if hasattr(self, 'status_label'):
                        self.status_label.config(text=f"大会员已登录: {username}", foreground="green")
                else:
                    if hasattr(self, 'window'):
                        messagebox.showinfo("登录成功", f"已登录为: {username}\n当前为普通账号，仅能下载1080P及以下画质")
                    else:
                        print(f"\n✅ 已登录为: {username} (普通账号)")
                    if hasattr(self, 'status_label'):
                        self.status_label.config(text=f"普通会员已登录: {username}", foreground="blue")
            else:
                error_msg = data.get("message", "未知错误")
                if hasattr(self, 'window'):
                    messagebox.showerror("登录失败", f"登录验证失败: {error_msg}")
                else:
                    print(f"\n❌ 登录验证失败: {error_msg}")
                if hasattr(self, 'status_label'):
                    self.status_label.config(text="登录验证失败", foreground="red")
        
        except Exception as e:
            import traceback
            print(f"Debug - 测试登录失败: {str(e)}")
            print(traceback.format_exc())
            if hasattr(self, 'window'):
                messagebox.showerror("网络错误", f"网络请求失败: {str(e)}")
            else:
                print(f"\n❌ 网络请求失败: {str(e)}")
            if hasattr(self, 'status_label'):
                self.status_label.config(text="网络请求失败", foreground="red")
    
    def _update_global_login_status(self):
        """立即更新全局登录状态"""
        try:
            # 直接从输入框获取，确保获取最新内容
            sessdata = self.sessdata_entry.get().strip() if hasattr(self, 'sessdata_entry') else ""
            bili_jct = self.bili_jct_entry.get().strip() if hasattr(self, 'bili_jct_entry') else ""
            buvid3 = self.buvid3_entry.get().strip() if hasattr(self, 'buvid3_entry') else ""
            
            # 更新全局配置
            DEFAULT_CONFIG["sessdata"] = sessdata
            DEFAULT_CONFIG["bili_jct"] = bili_jct
            DEFAULT_CONFIG["buvid3"] = buvid3
            
            print(f"Debug - 已更新全局登录状态: SESSDATA长度={len(sessdata)}")
        except Exception as e:
            print(f"Debug - 更新全局登录状态失败: {str(e)}")
            
    def _flash_button(self, times=5):
        """闪烁按钮提示用户点击"""
        if not hasattr(self, "window") or not self.window or times <= 0:
            return
            
        try:
            # 使用ttk样式系统来改变按钮样式，而不是直接设置background
            style = ttk.Style()
            
            # 创建交替的两种样式
            if times % 2 == 0:
                # 创建一个自定义的绿色按钮样式
                style.configure("Green.TButton", foreground="dark green")
                self.save_btn.configure(style="Green.TButton")
            else:
                # 恢复默认样式
                self.save_btn.configure(style="TButton")
                
            # 继续闪烁
            self.window.after(500, lambda: self._flash_button(times-1))
        except Exception as e:
            print(f"Debug - 闪烁按钮失败: {str(e)}")
            # 失败时确保按钮恢复正常样式
            try:
                self.save_btn.configure(style="TButton")
            except:
                pass
    
    def _force_update_login_info(self, sessdata, bili_jct, buvid3):
        """更新登录信息到全局变量"""
        try:
            # 更新全局配置
            DEFAULT_CONFIG["sessdata"] = sessdata
            DEFAULT_CONFIG["bili_jct"] = bili_jct
            DEFAULT_CONFIG["buvid3"] = buvid3
            
            # 再次保存配置以确保持久化
            self.user_config.update({
                "sessdata": sessdata,
                "bili_jct": bili_jct,
                "buvid3": buvid3,
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            save_user_config(self.user_config)
            
            print(f"Debug - 更新登录信息成功")
        except Exception as e:
            print(f"Debug - 更新登录信息失败: {str(e)}")

    def cli_login(self):
        """命令行模式登录"""
        print("\n====== B站登录凭证保存工具 ======\n")
        print("该工具用于直接输入和保存登录凭证")
        
        # 获取用户输入
        print("\n请输入SESSDATA值 (必须):")
        sessdata = input("> ").strip()
        
        if not sessdata:
            print("错误: SESSDATA不能为空！")
            return
        
        print("\n请输入bili_jct值 (可选):")
        bili_jct = input("> ").strip()
        
        print("\n请输入buvid3值 (可选):")
        buvid3 = input("> ").strip()
        
        # 更新配置
        self.user_config.update({
            "sessdata": sessdata,
            "bili_jct": bili_jct,
            "buvid3": buvid3,
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # 保存配置
        try:
            save_user_config(self.user_config)
            print(f"\n✅ 登录凭证已保存!")
            
            # 更新全局配置
            DEFAULT_CONFIG["sessdata"] = sessdata
            DEFAULT_CONFIG["bili_jct"] = bili_jct
            DEFAULT_CONFIG["buvid3"] = buvid3
            
            # 测试登录
            print("\n是否测试登录状态？(y/n)")
            if input("> ").strip().lower() in ('y', 'yes'):
                self.test_login()
                
        except Exception as e:
            print(f"\n❌ 保存配置失败: {str(e)}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='B站登录助手')
    parser.add_argument('--cli', action='store_true', help='使用命令行模式')
    args = parser.parse_args()
    
    helper = LoginHelper(cli_mode=args.cli)
    if args.cli:
        helper.cli_login()
    else:
        helper.show_login_guide()
