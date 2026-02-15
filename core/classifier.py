import os
from typing import Optional, Dict, Any, List
from .file_scanner import FileScanner
from .image_processor import ImageProcessor
from .ollama_client import OllamaClient
from .network_client import NetworkClient
from .file_mover import FileMover
from .database import Database
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    DEFAULT_API_TYPE, DEFAULT_OLLAMA_URL, DEFAULT_OLLAMA_MODEL, CATEGORIES,
    DEFAULT_OPERATION_MODE, DEFAULT_VIDEO_FRAME_COUNT,
    DEFAULT_TIME_SOURCE, DEFAULT_FOLDER_STRUCTURE,
    DEFAULT_VIDEO_FRAME_MODE,
    DEFAULT_NETWORK_API_URL, DEFAULT_NETWORK_API_KEY, DEFAULT_NETWORK_API_MODEL
)


class MediaClassifier:
    def __init__(
        self,
        api_type: str = DEFAULT_API_TYPE,
        ollama_url: str = DEFAULT_OLLAMA_URL,
        ollama_model: str = DEFAULT_OLLAMA_MODEL,
        network_api_url: str = DEFAULT_NETWORK_API_URL,
        network_api_key: str = DEFAULT_NETWORK_API_KEY,
        network_api_model: str = DEFAULT_NETWORK_API_MODEL,
        categories: List[str] = None,
        prompt_template: str = None,
        operation_mode: str = DEFAULT_OPERATION_MODE,
        video_frame_count: int = DEFAULT_VIDEO_FRAME_COUNT,
        video_frame_mode: str = DEFAULT_VIDEO_FRAME_MODE,
        time_source: str = DEFAULT_TIME_SOURCE,
        folder_structure: str = DEFAULT_FOLDER_STRUCTURE
    ):
        self.scanner = FileScanner()
        self.processor = ImageProcessor(video_frame_count=video_frame_count, video_frame_mode=video_frame_mode)
        
        # Initialize both clients
        self.ollama = OllamaClient(
            url=ollama_url,
            model=ollama_model,
            categories=categories,
            prompt_template=prompt_template
        )
        
        self.network = NetworkClient(
            url=network_api_url,
            api_key=network_api_key,
            model=network_api_model,
            categories=categories,
            prompt_template=prompt_template
        )
        
        self.api_type = api_type
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.network_api_url = network_api_url
        self.network_api_key = network_api_key
        self.network_api_model = network_api_model
        
        self.mover = FileMover()
        self.db = Database()
        self.operation_mode = operation_mode
        self.video_frame_count = video_frame_count
        self.video_frame_mode = video_frame_mode
        self.time_source = time_source
        self.folder_structure = folder_structure

    def update_settings(
        self,
        api_type: str = None,
        ollama_url: str = None,
        ollama_model: str = None,
        network_api_url: str = None,
        network_api_key: str = None,
        network_api_model: str = None,
        categories: List[str] = None,
        prompt_template: str = None,
        operation_mode: str = None,
        video_frame_count: int = None,
        video_frame_mode: str = None,
        time_source: str = None,
        folder_structure: str = None
    ):
        if api_type:
            self.api_type = api_type
        if ollama_url:
            self.ollama.url = ollama_url.rstrip('/')
            self.ollama_url = ollama_url
        if ollama_model:
            self.ollama.set_model(ollama_model)
            self.ollama_model = ollama_model
        if network_api_url:
            self.network.url = network_api_url.rstrip('/')
            self.network_api_url = network_api_url
        if network_api_key:
            self.network.set_api_key(network_api_key)
            self.network_api_key = network_api_key
        if network_api_model:
            self.network.set_model(network_api_model)
            self.network_api_model = network_api_model
        if categories:
            self.ollama.set_categories(categories)
            self.network.set_categories(categories)
        if prompt_template:
            self.ollama.set_prompt_template(prompt_template)
            self.network.set_prompt_template(prompt_template)
        if operation_mode:
            self.operation_mode = operation_mode
        if video_frame_count:
            self.video_frame_count = video_frame_count
            self.processor.video_frame_count = video_frame_count
        if video_frame_mode:
            self.video_frame_mode = video_frame_mode
            self.processor.video_frame_mode = video_frame_mode
        if time_source:
            self.time_source = time_source
        if folder_structure:
            self.folder_structure = folder_structure

    def process_single_file(
        self, 
        file_path: str, 
        target_dir: str
    ) -> Dict[str, Any]:
        result = {
            "success": False,
            "file_path": file_path,
            "category": None,
            "error": None,
            "ai_result": None
        }

        try:
            if not os.path.exists(file_path):
                result["error"] = "文件不存在"
                return result

            if self.db.is_file_processed(file_path):
                result["error"] = "文件已处理过"
                return result

            is_video = self.scanner.is_video_file(file_path)
            img, base64_img = self.processor.process_media(
                file_path, 
                is_video=is_video,
                frame_count=self.video_frame_count,
                frame_mode=self.video_frame_mode
            )

            if not img or not base64_img:
                result["error"] = "图像处理失败"
                return result

            # Use the appropriate AI client based on api_type
            if self.api_type == "network":
                ai_response = self.network.analyze_image(base64_img)
            else:
                ai_response = self.ollama.analyze_image(base64_img)

            if not ai_response or not ai_response.get("success"):
                result["error"] = ai_response.get("error", "AI识别失败") if ai_response else "AI识别失败"
                return result

            category = ai_response.get("category", "其他")
            raw_response = ai_response.get("raw_response", "")

            moved_path = self.mover.organize_by_category_with_date(
                file_path, 
                target_dir, 
                category,
                self.operation_mode,
                self.time_source,
                self.folder_structure
            )

            if moved_path:
                self.db.add_processed_file(
                    file_path, 
                    category, 
                    raw_response
                )
                result["success"] = True
                result["category"] = category
                result["ai_result"] = raw_response
                result["moved_to"] = moved_path
            else:
                result["error"] = "文件移动/复制失败"

        except Exception as e:
            result["error"] = str(e)

        return result
