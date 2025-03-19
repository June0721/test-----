"""
启动设置界面的快捷脚本
"""
from settings import SettingsManager

if __name__ == "__main__":
    manager = SettingsManager()
    manager.show_settings_window()
