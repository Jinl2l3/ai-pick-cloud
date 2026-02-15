import os
from typing import List, Tuple
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS


class FileScanner:
    def __init__(self):
        self.image_extensions = IMAGE_EXTENSIONS
        self.video_extensions = VIDEO_EXTENSIONS

    def is_image_file(self, file_path: str) -> bool:
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.image_extensions

    def is_video_file(self, file_path: str) -> bool:
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.video_extensions

    def is_media_file(self, file_path: str) -> bool:
        return self.is_image_file(file_path) or self.is_video_file(file_path)

    def scan_directory(
        self, 
        root_dir: str, 
        recursive: bool = True
    ) -> Tuple[List[str], List[str]]:
        image_files = []
        video_files = []

        if not os.path.exists(root_dir):
            return image_files, video_files

        if recursive:
            for dirpath, _, filenames in os.walk(root_dir):
                for filename in filenames:
                    file_path = os.path.abspath(os.path.join(dirpath, filename))
                    if self.is_image_file(file_path):
                        image_files.append(file_path)
                    elif self.is_video_file(file_path):
                        video_files.append(file_path)
        else:
            for filename in os.listdir(root_dir):
                file_path = os.path.abspath(os.path.join(root_dir, filename))
                if os.path.isfile(file_path):
                    if self.is_image_file(file_path):
                        image_files.append(file_path)
                    elif self.is_video_file(file_path):
                        video_files.append(file_path)

        return sorted(image_files), sorted(video_files)

    def get_all_media_files(self, root_dir: str, recursive: bool = True) -> List[str]:
        images, videos = self.scan_directory(root_dir, recursive)
        return images + videos
