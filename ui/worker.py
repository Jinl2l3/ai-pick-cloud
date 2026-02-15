import os
import time
from PyQt5.QtCore import QThread, pyqtSignal, QMutex
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.classifier import MediaClassifier
from core.file_scanner import FileScanner
from core.database import Database
from core.image_processor import ImageProcessor
from config import (
    DEFAULT_MAX_CONCURRENT, DEFAULT_VIDEO_FRAME_COUNT, 
    DEFAULT_OPERATION_MODE, DEFAULT_TIME_SOURCE, DEFAULT_FOLDER_STRUCTURE,
    DEFAULT_VIDEO_FRAME_MODE,
    DEFAULT_API_TYPE, DEFAULT_NETWORK_API_URL, DEFAULT_NETWORK_API_KEY,
    DEFAULT_NETWORK_API_MODEL, DEFAULT_NETWORK_API_MAX_CONCURRENT
)

class MediaProcessorWorker(QThread):
    progress_updated = pyqtSignal(int, int)
    file_processed = pyqtSignal(dict)
    log_message = pyqtSignal(str)
    preview_image = pyqtSignal(object)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(
        self, 
        source_dir: str, 
        target_dir: str, 
        recursive: bool = True,
        settings: dict = None
    ):
        super().__init__()
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.recursive = recursive
        self.settings = settings or {}
        self._is_running = True
        self._is_paused = False
        self._progress_mutex = QMutex()
        self._processed_count = 0
        
        # API Configuration
        self.api_type = self.settings.get("api_type", DEFAULT_API_TYPE)
        self.ollama_url = self.settings.get("ollama_url")
        self.ollama_model = self.settings.get("ollama_model")
        self.network_api_url = self.settings.get("network_api_url")
        self.network_api_key = self.settings.get("network_api_key")
        self.network_api_model = self.settings.get("network_api_model")
        
        # Determine max concurrent based on API type
        if self.api_type == "network":
            self.max_concurrent = self.settings.get("network_api_max_concurrent", DEFAULT_NETWORK_API_MAX_CONCURRENT)
        else:
            self.max_concurrent = self.settings.get("max_concurrent", DEFAULT_MAX_CONCURRENT)
        
        self.categories = self.settings.get("categories")
        self.prompt_template = self.settings.get("prompt")
        self.operation_mode = self.settings.get("operation_mode", DEFAULT_OPERATION_MODE)
        self.video_frame_count = self.settings.get("video_frame_count", DEFAULT_VIDEO_FRAME_COUNT)
        self.video_frame_mode = self.settings.get("video_frame_mode", DEFAULT_VIDEO_FRAME_MODE)
        self.time_source = self.settings.get("time_source", DEFAULT_TIME_SOURCE)
        self.folder_structure = self.settings.get("folder_structure", DEFAULT_FOLDER_STRUCTURE)
        self.process_images = self.settings.get("process_images", True)
        self.process_videos = self.settings.get("process_videos", True)
        
        self.base_classifier = MediaClassifier(
            api_type=self.api_type,
            ollama_url=self.ollama_url,
            ollama_model=self.ollama_model,
            network_api_url=self.network_api_url,
            network_api_key=self.network_api_key,
            network_api_model=self.network_api_model,
            categories=self.categories,
            prompt_template=self.prompt_template,
            operation_mode=self.operation_mode,
            video_frame_count=self.video_frame_count,
            video_frame_mode=self.video_frame_mode,
            time_source=self.time_source,
            folder_structure=self.folder_structure
        )
        self.scanner = FileScanner()
        self.db = Database()
        self.processor = ImageProcessor(video_frame_count=self.video_frame_count, video_frame_mode=self.video_frame_mode)

    def _process_single_file(self, file_path: str) -> Dict[str, Any]:
        if not self._is_running:
            return {"success": False, "file_path": file_path, "error": "已停止"}

        while self._is_paused and self._is_running:
            self.msleep(100)

        if not self._is_running:
            return {"success": False, "file_path": file_path, "error": "已停止"}

        try:
            self.log_message.emit(f"处理: {os.path.basename(file_path)}")

            try:
                is_video = self.scanner.is_video_file(file_path)
                img, _ = self.processor.process_media(
                    file_path, 
                    is_video=is_video,
                    frame_count=self.video_frame_count,
                    frame_mode=self.video_frame_mode
                )
                if img:
                    self.preview_image.emit(img)
            except Exception:
                pass

            classifier = MediaClassifier(
                api_type=self.api_type,
                ollama_url=self.ollama_url,
                ollama_model=self.ollama_model,
                network_api_url=self.network_api_url,
                network_api_key=self.network_api_key,
                network_api_model=self.network_api_model,
                categories=self.categories,
                prompt_template=self.prompt_template,
                operation_mode=self.operation_mode,
                video_frame_count=self.video_frame_count,
                video_frame_mode=self.video_frame_mode,
                time_source=self.time_source,
                folder_structure=self.folder_structure
            )
            result = classifier.process_single_file(file_path, self.target_dir)
            return result

        except Exception as e:
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e)
            }

    def run(self):
        try:
            self.log_message.emit(f"开始扫描目录: {self.source_dir}")
            self.log_message.emit(f"最大并发数: {self.max_concurrent}")
            
            invalid_count = self.db.clear_invalid_records()
            if invalid_count > 0:
                self.log_message.emit(f"清理了 {invalid_count} 条无效的已处理记录")
            
            image_files, video_files = self.scanner.scan_directory(
                self.source_dir, 
                self.recursive
            )
            
            all_files = []
            if self.process_images:
                all_files.extend(image_files)
            if self.process_videos:
                all_files.extend(video_files)
            
            if not all_files:
                if not self.process_images and not self.process_videos:
                    self.log_message.emit("图片和视频处理都已关闭，请在设置中开启")
                else:
                    self.log_message.emit("未找到符合条件的媒体文件")
                self.finished.emit()
                return

            unprocessed = self.db.get_unprocessed_files(all_files)
            total = len(unprocessed)
            
            self.log_message.emit(f"找到 {len(all_files)} 个文件，其中 {total} 个未处理")

            if total == 0:
                self.log_message.emit("所有文件都已处理过！")
                self.log_message.emit("提示：如果想重新处理这些文件，可以手动删除数据库或使用重新处理功能")
                self.finished.emit()
                return

            self._processed_count = 0

            with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
                futures = {
                    executor.submit(self._process_single_file, file_path): file_path
                    for file_path in unprocessed
                }

                for future in as_completed(futures):
                    if not self._is_running:
                        break

                    try:
                        result = future.result()
                        self.file_processed.emit(result)

                        self._progress_mutex.lock()
                        self._processed_count += 1
                        current = self._processed_count
                        self._progress_mutex.unlock()

                        self.progress_updated.emit(current, total)

                        if result["success"]:
                            self.log_message.emit(
                                f"✓ 分类完成: {result['category']} - {os.path.basename(result['file_path'])}"
                            )
                        else:
                            self.log_message.emit(
                                f"✗ 失败: {result.get('error', '未知错误')} - {os.path.basename(result['file_path'])}"
                            )
                    except Exception as e:
                        self.log_message.emit(f"✗ 处理异常: {str(e)}")

            self.log_message.emit("处理完成")
            self.finished.emit()

        except Exception as e:
            self.error_occurred.emit(str(e))
            self.finished.emit()

    def pause(self):
        self._is_paused = True
        self.log_message.emit("已暂停")

    def resume(self):
        self._is_paused = False
        self.log_message.emit("继续处理")

    def stop(self):
        self._is_running = False
        self._is_paused = False
        self.log_message.emit("正在停止...")
