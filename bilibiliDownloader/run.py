"""
B站视频下载器启动脚本
"""
import os
import sys

def main():
    """启动下载器"""
    print("启动B站视频下载器...")
    
    try:
        # 检查命令行参数
        if len(sys.argv) > 1:
            # 有命令行参数，转发到main.py
            from main import main as run_main
            run_main()
        else:
            # 无参数，启动GUI
            from gui import DownloaderGUI
            app = DownloaderGUI()
            app.run()
    except ImportError as e:
        print(f"启动失败: {e}")
        print("请确保已安装所有依赖库。可以使用以下命令安装依赖:")
        print("pip install requests")
        
        if input("是否尝试自动安装依赖? (y/n): ").lower() == 'y':
            import subprocess
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
                print("安装完成，请重新运行程序")
            except Exception:
                print("安装失败，请手动安装所需依赖")
    except Exception as e:
        print(f"启动出错: {e}")
        input("按Enter键退出...")
    
if __name__ == "__main__":
    main()
