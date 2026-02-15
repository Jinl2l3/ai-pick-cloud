import os
import shutil
from datetime import datetime
from typing import Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DEFAULT_TIME_SOURCE, DEFAULT_FOLDER_STRUCTURE, DEFAULT_RENAME_DATE_FORMAT


class FileMover:
    @staticmethod
    def get_file_time(file_path: str, time_source: str = DEFAULT_TIME_SOURCE) -> datetime:
        try:
            stat = os.stat(file_path)
            
            times = []
            try:
                birth_time = datetime.fromtimestamp(stat.st_birthtime)
                times.append(birth_time)
            except AttributeError:
                pass
            
            mtime = datetime.fromtimestamp(stat.st_mtime)
            ctime = datetime.fromtimestamp(stat.st_ctime)
            times.extend([mtime, ctime])
            
            if time_source == "birth":
                try:
                    return datetime.fromtimestamp(stat.st_birthtime)
                except AttributeError:
                    return min(times)
            elif time_source == "modify":
                return mtime
            elif time_source == "access":
                atime = datetime.fromtimestamp(stat.st_atime)
                return atime
            elif time_source == "earliest":
                return min(times)
            elif time_source == "latest":
                return max(times)
            else:
                return min(times)
        except Exception:
            return datetime.now()

    @staticmethod
    def get_unique_path(dest_dir: str, filename: str) -> str:
        name, ext = os.path.splitext(filename)
        counter = 1
        new_path = os.path.join(dest_dir, filename)
        
        while os.path.exists(new_path):
            new_filename = f"{name}_{counter}{ext}"
            new_path = os.path.join(dest_dir, new_filename)
            counter += 1
        
        return new_path

    @staticmethod
    def _copy_or_move_file(
        src_path: str, 
        dest_dir: str, 
        operation: str = "move",
        create_dir: bool = True
    ) -> Optional[str]:
        if not os.path.exists(src_path):
            return None
        
        if create_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
        
        filename = os.path.basename(src_path)
        dest_path = FileMover.get_unique_path(dest_dir, filename)
        
        try:
            if operation == "copy":
                shutil.copy2(src_path, dest_path)
            else:
                shutil.move(src_path, dest_path)
            return dest_path
        except Exception:
            return None

    @staticmethod
    def move_file(
        src_path: str, 
        dest_dir: str, 
        create_dir: bool = True
    ) -> Optional[str]:
        return FileMover._copy_or_move_file(src_path, dest_dir, "move", create_dir)

    @staticmethod
    def copy_file(
        src_path: str, 
        dest_dir: str, 
        create_dir: bool = True
    ) -> Optional[str]:
        return FileMover._copy_or_move_file(src_path, dest_dir, "copy", create_dir)

    @staticmethod
    def organize_by_category_with_date(
        src_path: str, 
        root_dir: str, 
        category: str,
        operation: str = "move",
        time_source: str = DEFAULT_TIME_SOURCE,
        folder_structure: str = DEFAULT_FOLDER_STRUCTURE,
        rename_info: Optional[dict] = None
    ) -> Optional[str]:
        file_time = FileMover.get_file_time(src_path, time_source)
        year_str = f"{file_time.year}年"
        month_str = f"{file_time.month}月"
        
        if folder_structure == "category_time":
            dest_dir = os.path.join(root_dir, category, year_str, month_str)
        elif folder_structure == "time_category":
            dest_dir = os.path.join(root_dir, year_str, month_str, category)
        else:
            dest_dir = os.path.join(root_dir, category, year_str, month_str)
        
        if rename_info and rename_info.get("enabled"):
            # 重命名文件
            old_filename = os.path.basename(src_path)
            old_name, ext = os.path.splitext(old_filename)
            
            # 构建新文件名
            parts = []
            
            # 添加AI生成的描述
            if rename_info.get("description"):
                parts.append(rename_info["description"])
            
            # 添加原始文件名
            if rename_info.get("include_original"):
                parts.append(old_name)
            
            # 添加日期
            date_type = rename_info.get("date_type", "none")
            if date_type != "none":
                date_format = rename_info.get("date_format", DEFAULT_RENAME_DATE_FORMAT)
                file_date = FileMover.get_file_time(src_path, date_type)
                date_str = file_date.strftime(date_format)
                parts.append(date_str)
            
            # 构建最终文件名
            if parts:
                new_name = "_".join(parts)
                # 清理文件名中的非法字符
                new_name = "".join(c for c in new_name if c.isalnum() or c in "_-")
                new_filename = f"{new_name}{ext}"
                
                # 确保目录存在
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir, exist_ok=True)
                
                # 构建目标路径
                dest_path = FileMover.get_unique_path(dest_dir, new_filename)
                
                try:
                    if operation == "copy":
                        shutil.copy2(src_path, dest_path)
                    else:
                        shutil.move(src_path, dest_path)
                    return dest_path
                except Exception:
                    return None
        
        # 不重命名，使用原始方法
        return FileMover._copy_or_move_file(src_path, dest_dir, operation, create_dir=True)

    @staticmethod
    def rename_file(
        src_path: str, 
        description: str,
        include_original: bool = False,
        date_type: str = "none",
        date_format: str = DEFAULT_RENAME_DATE_FORMAT
    ) -> Optional[str]:
        """重命名单个文件"""
        try:
            if not os.path.exists(src_path):
                return None
            
            # 获取原始文件名和扩展名
            old_filename = os.path.basename(src_path)
            old_name, ext = os.path.splitext(old_filename)
            dest_dir = os.path.dirname(src_path)
            
            # 构建新文件名
            parts = []
            
            # 添加描述
            if description:
                parts.append(description)
            
            # 添加原始文件名
            if include_original:
                parts.append(old_name)
            
            # 添加日期
            if date_type != "none":
                file_date = FileMover.get_file_time(src_path, date_type)
                date_str = file_date.strftime(date_format)
                parts.append(date_str)
            
            # 构建最终文件名
            if parts:
                new_name = "_".join(parts)
                # 清理文件名中的非法字符
                new_name = "".join(c for c in new_name if c.isalnum() or c in "_-")
                new_filename = f"{new_name}{ext}"
                
                # 确保路径唯一
                dest_path = FileMover.get_unique_path(dest_dir, new_filename)
                
                # 重命名文件
                os.rename(src_path, dest_path)
                return dest_path
            
            return src_path
        except Exception:
            return None
