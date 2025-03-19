"""
更新导入引用的脚本
将enhanced_bilibili_downloader导入替换为downloader_factory
"""
import os
import re

def update_file_imports(file_path):
    """更新文件中的导入语句"""
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return False
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换对enhanced_bilibili_downloader的导入
    updated = re.sub(
        r'from enhanced_bilibili_downloader import BilibiliDownloader',
        'from downloader_factory import create_downloader',
        content
    )
    
    # 替换对BilibiliDownloader的实例化
    updated = re.sub(
        r'self.downloader = BilibiliDownloader\(progress_callback=([^)]+)\)',
        r'self.downloader = create_downloader(progress_callback=\1)',
        updated
    )
    
    if updated != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated)
        return True
    return False

def main():
    """更新所有Python文件中的导入"""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    updated_files = []
    
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if update_file_imports(file_path):
                    updated_files.append(file_path)
    
    if updated_files:
        print(f"已更新 {len(updated_files)} 个文件:")
        for file in updated_files:
            print(f" - {os.path.basename(file)}")
    else:
        print("没有文件需要更新")

if __name__ == "__main__":
    main()
