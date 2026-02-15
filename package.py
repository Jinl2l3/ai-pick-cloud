import os
import zipfile

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 打包输出目录
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "dist")

# 要包含的目录和文件
INCLUDE_DIRS = [
    "core",
    "ui"
]

INCLUDE_FILES = [
    "main.py",
    "config.py",
    "requirements.txt",
    "README.md",
    "LICENSE"
]

# 要排除的文件和目录模式
EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "venv",
    ".trae",
    "test",
    "*.db",
    "*.log",
    "settings.json",
    "dist"
]

def should_exclude(path):
    """检查是否应该排除该文件或目录"""
    for pattern in EXCLUDE_PATTERNS:
        if pattern in path:
            return True
    return False

def package_code():
    """打包代码文件"""
    print("开始打包代码...")
    
    # 创建输出目录
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # 打包文件名
    import time
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    package_name = f"ai_pick_cloud_code_{timestamp}.zip"
    package_path = os.path.join(OUTPUT_DIR, package_name)
    
    # 创建zip文件
    with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # 添加目录
        for dir_name in INCLUDE_DIRS:
            dir_path = os.path.join(PROJECT_ROOT, dir_name)
            if os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    # 过滤目录
                    dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        if not should_exclude(file_path):
                            arcname = os.path.relpath(file_path, PROJECT_ROOT)
                            zipf.write(file_path, arcname)
                            print(f"添加: {arcname}")
        
        # 添加单个文件
        for file_name in INCLUDE_FILES:
            file_path = os.path.join(PROJECT_ROOT, file_name)
            if os.path.exists(file_path):
                arcname = os.path.relpath(file_path, PROJECT_ROOT)
                zipf.write(file_path, arcname)
                print(f"添加: {arcname}")
    
    print(f"\n打包完成！")
    print(f"打包文件: {package_path}")
    print(f"文件大小: {os.path.getsize(package_path) / 1024:.2f} KB")

if __name__ == "__main__":
    package_code()
