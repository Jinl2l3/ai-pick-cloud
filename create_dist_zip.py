import os
import zipfile
from datetime import datetime

def create_zip():
    dist_dir = "dist"
    source_dir = "."  # 从根目录读取
    
    # 生成带时间戳的文件名（英文）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"ai-media-organizer_v{timestamp}.zip"
    zip_path = os.path.join(dist_dir, zip_filename)
    
    # 要包含的文件和目录
    items_to_include = [
        "main.py",
        "config.py",
        "requirements.txt",
        "README.md",
        "LICENSE",
        "core",
        "ui",
        "doc"
    ]
    
    # 要排除的文件
    items_to_exclude = [
        "settings.json",
        "file_index.db",
        "__pycache__",
        "*.pyc",
        "*.log",
        ".trae",
        "test/"
    ]
    
    print(f"正在创建压缩包: {zip_filename}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in items_to_include:
            item_path = os.path.join(source_dir, item)
            if os.path.exists(item_path):
                if os.path.isfile(item_path):
                    zipf.write(item_path, item)
                    print(f"  添加文件: {item}")
                elif os.path.isdir(item_path):
                    for root, dirs, files in os.walk(item_path):
                        # 排除 __pycache__ 目录
                        dirs[:] = [d for d in dirs if d != '__pycache__']
                        for file in files:
                            # 排除 .pyc 文件
                            if not file.endswith('.pyc'):
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, source_dir)
                                zipf.write(file_path, arcname)
                                print(f"  添加文件: {arcname}")
                print(f"  添加目录: {item}")
            else:
                print(f"  警告: {item} 不存在")
        
        # 检查并添加排除的文件
        for item in items_to_exclude:
            item_path = os.path.join(source_dir, item)
            if os.path.exists(item_path):
                if os.path.isfile(item_path):
                    print(f"  排除文件: {item}")
                elif os.path.isdir(item_path):
                    for root, dirs, files in os.walk(item_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            print(f"  排除文件: {os.path.relpath(file_path, source_dir)}")
    
    print(f"压缩包创建完成: {zip_path}")
    print(f"文件大小: {os.path.getsize(zip_path) / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    create_zip()