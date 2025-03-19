"""
程序入口点，负责初始化环境并启动GUI
"""
import os
import sys
import traceback
import tkinter as tk
from tkinter import messagebox

def check_dependencies():
    """检查依赖项"""
    try:
        import requests
        return True
    except ImportError:
        return False

def setup_environment():
    """设置环境"""
    # 确保当前工作目录正确
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 添加当前目录到搜索路径
    if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # 创建必要的目录
    for directory in ["logs", "cache", "temp"]:
        dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), directory)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Bilibili视频下载器')
    parser.add_argument('--cli', action='store_true',
                       help='使用命令行模式而不是GUI模式')
    parser.add_argument('--url', type=str,
                       help='要下载的视频URL')
    parser.add_argument('--quality', choices=['ultra', 'superhigh', 'high', 'medium', 'low'],
                       default='superhigh', help='视频画质: ultra (8K), superhigh (4K), high (1080P60), medium (1080P), low (720P)')
    parser.add_argument('--output', '-o', type=str,
                       help='保存目录路径')
    parser.add_argument('--settings', action='store_true', 
                       help='打开设置界面')
    parser.add_argument('--login', action='store_true',
                       help='打开登录助手')
    parser.add_argument('--fix-login', action='store_true',
                       help='修复登录问题')
    parser.add_argument('--direct-login', action='store_true',
                       help='使用简单模式设置登录凭证')
    return parser.parse_args()

def progress_callback(current_bytes: int):
    """命令行模式的进度显示"""
    sys.stdout.write(f'\r已下载: {current_bytes} bytes')
    sys.stdout.flush()

def main():
    """主函数"""
    try:
        # 设置环境
        setup_environment()
        
        # 检查依赖
        if not check_dependencies():
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            messagebox.showerror(
                "缺少依赖", 
                "缺少必要的依赖库！\n请运行以下命令安装：\npip install -r requirements.txt"
            )
            return
        
        args = parse_args()
        
        # 处理所有登录相关功能
        if args.login or args.direct_login or args.fix_login:
            try:
                from login_helper import LoginHelper
                helper = LoginHelper(cli_mode=args.direct_login)
                if args.direct_login:
                    helper.cli_login()
                else:
                    helper.show_login_guide()
            except Exception as e:
                print(f"登录操作失败: {str(e)}")
            return

        # 打开设置界面
        if args.settings:
            settings = SettingsManager()
            settings.show_settings_window()
            return
        
        # 导入下载器工厂
        from downloader_factory import create_downloader

        if args.cli:
            # 命令行模式
            if not args.url:
                print("错误: 命令行模式下必须提供--url参数")
                sys.exit(1)
                
            try:
                print(f"正在下载视频: {args.url}")
                print(f"画质选择: {args.quality}")
                
                # 使用工厂创建下载器
                downloader = create_downloader(progress_callback=progress_callback)
                result = downloader.download_video(
                    url=args.url,
                    quality=args.quality,
                    save_dir=args.output
                )
                save_history(result)
                
                print(f"\n下载成功! 保存至: {result['save_path']}")
                print(f"视频画质: {result.get('actual_quality', '未知')}")
                
                # 显示画质降级信息
                if result.get('degradation_info'):
                    info = result['degradation_info']
                    print(f"\n⚠️ 画质降级: 从 {info['requested_name']} 降级为 {info['current_name']}")
                    print(f"原因: {info['reason']}")
                
            except Exception as e:
                # 使用错误分析器提供友好提示
                from error_handler import analyze_error
                title, detail, is_fatal = analyze_error(e)
                print(f"\n❌ {title}")
                print(detail)
                sys.exit(1)
                
        else:
            # 导入并启动GUI
            from gui import DownloaderGUI
            app = DownloaderGUI()
            app.run()
            
    except Exception as e:
        # 显示错误对话框
        error_msg = f"启动失败: {str(e)}\n\n{traceback.format_exc()}"
        try:
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            messagebox.showerror("错误", error_msg)
        except:
            print(error_msg)
        
        # 记录错误日志
        try:
            from logger import logger
            logger.critical(error_msg)
        except:
            with open("error.log", "a", encoding="utf-8") as f:
                f.write(f"{datetime.datetime.now()}: {error_msg}\n")

if __name__ == "__main__":
    main()
