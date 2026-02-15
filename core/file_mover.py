import os
import shutil
from datetime import datetime
from typing import Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DEFAULT_TIME_SOURCE, DEFAULT_FOLDER_STRUCTURE


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
        folder_structure: str = DEFAULT_FOLDER_STRUCTURE
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
        
        return FileMover._copy_or_move_file(src_path, dest_dir, operation, create_dir=True)
