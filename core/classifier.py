import os
from datetime import datetime
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
        network_api_models: List[str] = None,
        network_api_round_robin: bool = True,
        network_api_model_max_concurrent: int = 2,
        categories: List[str] = None,
        prompt_template: str = None,
        video_prompt_template: str = None,
        image_structured_output_prompt: str = None,
        video_structured_output_prompt: str = None,
        operation_mode: str = DEFAULT_OPERATION_MODE,
        video_frame_count: int = DEFAULT_VIDEO_FRAME_COUNT,
        video_frame_mode: str = DEFAULT_VIDEO_FRAME_MODE,
        time_source: str = DEFAULT_TIME_SOURCE,
        folder_structure: str = DEFAULT_FOLDER_STRUCTURE,
        # Rename settings
        rename_enabled: bool = False,
        rename_prompt: str = None,
        video_rename_prompt: str = None,
        rename_include_original: bool = False,
        rename_date_type: str = "none",
        rename_date_format: str = "%Y%m%d",
        # Network retry and error export settings
        retry_enabled: bool = True,
        retry_count: int = 3,
        retry_delay: int = 2,
        request_timeout: int = 180,
        error_export_enabled: bool = True,
        error_export_folder: str = "error_files"
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
            models=network_api_models,
            categories=categories,
            prompt_template=prompt_template,
            video_prompt_template=video_prompt_template,
            # Retry settings
            retry_enabled=retry_enabled,
            retry_count=retry_count,
            retry_delay=retry_delay,
            request_timeout=request_timeout,
            # Round robin settings
            round_robin=network_api_round_robin,
            # Model concurrency settings
            model_max_concurrent=network_api_model_max_concurrent
        )
        
        self.api_type = api_type
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.network_api_url = network_api_url
        self.network_api_key = network_api_key
        self.network_api_model = network_api_model
        self.categories = categories or CATEGORIES
        
        # Rename settings
        self.rename_enabled = rename_enabled
        self.rename_prompt = rename_prompt
        self.video_rename_prompt = video_rename_prompt
        self.rename_include_original = rename_include_original
        self.rename_date_type = rename_date_type
        self.rename_date_format = rename_date_format
        
        # Structured output prompts
        self.image_structured_output_prompt = image_structured_output_prompt or ""
        self.video_structured_output_prompt = video_structured_output_prompt or ""
        
        # Network retry and error export settings
        self.retry_enabled = retry_enabled
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.error_export_enabled = error_export_enabled
        self.error_export_folder = error_export_folder
        
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
        network_api_models: List[str] = None,
        network_api_round_robin: bool = None,
        network_api_model_max_concurrent: int = None,
        categories: List[str] = None,
        prompt_template: str = None,
        video_prompt_template: str = None,
        image_structured_output_prompt: str = None,
        video_structured_output_prompt: str = None,
        operation_mode: str = None,
        video_frame_count: int = None,
        video_frame_mode: str = None,
        time_source: str = None,
        folder_structure: str = None,
        # Rename settings
        rename_enabled: bool = None,
        rename_prompt: str = None,
        video_rename_prompt: str = None,
        rename_include_original: bool = None,
        rename_date_type: str = None,
        rename_date_format: str = None,
        # Network retry and error export settings
        retry_enabled: bool = None,
        retry_count: int = None,
        retry_delay: int = None,
        request_timeout: int = None,
        error_export_enabled: bool = None,
        error_export_folder: str = None
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
        if network_api_models:
            self.network.set_models(network_api_models)
        if network_api_round_robin is not None:
            self.network.round_robin = network_api_round_robin
        if network_api_model_max_concurrent is not None:
            self.network.model_max_concurrent = network_api_model_max_concurrent
        if categories:
            self.ollama.set_categories(categories)
            self.network.set_categories(categories)
        if prompt_template:
            self.ollama.set_prompt_template(prompt_template)
            self.network.set_prompt_template(prompt_template)
        if video_prompt_template:
            self.network.video_prompt_template = video_prompt_template
        if image_structured_output_prompt is not None:
            self.image_structured_output_prompt = image_structured_output_prompt
        if video_structured_output_prompt is not None:
            self.video_structured_output_prompt = video_structured_output_prompt
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
        # Rename settings
        if rename_enabled is not None:
            self.rename_enabled = rename_enabled
        if rename_prompt:
            self.rename_prompt = rename_prompt
        if video_rename_prompt:
            self.video_rename_prompt = video_rename_prompt
        if rename_include_original is not None:
            self.rename_include_original = rename_include_original
        if rename_date_type:
            self.rename_date_type = rename_date_type
        if rename_date_format:
            self.rename_date_format = rename_date_format
        # Network retry and error export settings
        if retry_enabled is not None:
            self.retry_enabled = retry_enabled
            self.network.retry_enabled = retry_enabled
        if retry_count is not None:
            self.retry_count = retry_count
            self.network.retry_count = retry_count
        if retry_delay is not None:
            self.retry_delay = retry_delay
            self.network.retry_delay = retry_delay
        if request_timeout is not None:
            self.network.request_timeout = request_timeout
        if error_export_enabled is not None:
            self.error_export_enabled = error_export_enabled
        if error_export_folder:
            self.error_export_folder = error_export_folder

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
                if is_video:
                    custom_structured_output = self.video_structured_output_prompt
                    current_rename_prompt = self.video_rename_prompt
                else:
                    custom_structured_output = self.image_structured_output_prompt
                    current_rename_prompt = self.rename_prompt
                
                if custom_structured_output:
                    structured_output_prompt = custom_structured_output
                elif self.rename_enabled:
                    structured_output_prompt = """- 只返回JSON格式，格式如下：{"category": "类别名称", "description": "简短描述"}
- 类别必须且只能从指定列表中选择。
- 描述要简洁明了，突出图片核心内容。
- 不要包含任何其他文字或标点符号。
- 不要使用markdown代码块格式（不要使用```标记）。
- 直接返回纯JSON文本，不要任何格式化。"""
                else:
                    structured_output_prompt = """- 只返回JSON格式，格式如下：{"category": "类别名称"}
- 类别必须且只能从指定列表中选择。
- 不要包含任何其他文字或标点符号。
- 不要使用markdown代码块格式（不要使用```标记）。
- 直接返回纯JSON文本，不要任何格式化。"""
                ai_response = self.network.analyze_image(base64_img, is_video, structured_output_prompt, current_rename_prompt)
            else:
                ai_response = self.ollama.analyze_image(base64_img)

            if not ai_response or not ai_response.get("success"):
                result["error"] = ai_response.get("error", "AI识别失败") if ai_response else "AI识别失败"
                return result

            category = ai_response.get("category", "其他")
            raw_response = ai_response.get("raw_response", "")
            
            # Extract description from JSON response if rename is enabled
            description = None
            if self.rename_enabled and ai_response.get("success"):
                try:
                    import json
                    response_text = ai_response.get("raw_response", "")
                    if response_text:
                        # 清理响应文本，移除markdown代码块标记
                        cleaned_text = self._clean_json_response(response_text)
                        
                        # 尝试解析JSON
                        parsed = json.loads(cleaned_text)
                        description = parsed.get("description", "")
                        if description:
                            print(f"成功解析JSON描述: {description}")
                except json.JSONDecodeError as e:
                    print(f"JSON解析失败: {e}")
                    print(f"原始响应内容: {response_text[:500]}...")
                    # 如果JSON解析失败，尝试从响应中提取描述
                    description = self._extract_description_from_text(response_text)
                except Exception as e:
                    print(f"处理响应时发生异常: {e}")
                    print(f"原始响应内容: {response_text[:500]}...")
                    description = self._extract_description_from_text(response_text)
            
            # Build rename_info if description is available
            rename_info = None
            if description:
                rename_info = {
                    "enabled": True,
                    "description": description,
                    "include_original": self.rename_include_original,
                    "date_type": self.rename_date_type,
                    "date_format": self.rename_date_format
                }

            moved_path = self.mover.organize_by_category_with_date(
                file_path, 
                target_dir, 
                category,
                self.operation_mode,
                self.time_source,
                self.folder_structure,
                rename_info=rename_info
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
                error_msg = "文件移动/复制失败"
                result["error"] = error_msg
                
                # Export error file if enabled
                if self.error_export_enabled:
                    self._export_error_file(file_path, error_msg)

        except Exception as e:
            error_msg = str(e)
            print(f"处理文件时发生异常: {file_path}, 错误: {error_msg}")
            result["error"] = error_msg
            
            # Export error file if enabled
            if self.error_export_enabled:
                self._export_error_file(file_path, error_msg)

        return result

    def _clean_json_response(self, text: str) -> str:
        """清理JSON响应，移除markdown代码块标记和其他干扰"""
        try:
            import re
            
            # 移除markdown代码块标记 ```json ... ```
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*$', '', text)
            
            # 移除其他markdown代码块标记 ``` ... ```
            text = re.sub(r'```\s*', '', text)
            
            # 移除开头和结尾的空白字符
            text = text.strip()
            
            # 移除可能的前导和尾随引号（如果整个JSON被包裹在引号中）
            if text.startswith('"') and text.endswith('"'):
                text = text[1:-1]
            
            return text
        except Exception as e:
            print(f"清理JSON响应时发生异常: {e}")
            return text

    def _extract_description_from_text(self, text: str) -> str:
        """从非JSON格式的文本中提取描述"""
        try:
            import re
            
            # 首先尝试清理文本
            cleaned_text = self._clean_json_response(text)
            
            # 尝试直接从清理后的文本中提取JSON
            try:
                import json
                parsed = json.loads(cleaned_text)
                description = parsed.get("description", "")
                if description:
                    print(f"从清理后的文本中成功提取JSON描述: {description}")
                    return description[:20]
            except:
                pass
            
            # 尝试提取引号中的内容
            matches = re.findall(r'["\']([^"\']+)["\']', cleaned_text)
            if matches:
                # 返回第一个匹配项，且长度不超过20个字符
                for match in matches:
                    if len(match) <= 30 and match not in self.categories:
                        return match[:20]
            
            # 如果没有找到，尝试提取中文描述
            # 查找连续的中文字符
            chinese_matches = re.findall(r'[\u4e00-\u9fa5]{2,10}', cleaned_text)
            if chinese_matches:
                return chinese_matches[0][:20]
            
            # 如果还是没有，返回前20个非空字符
            cleaned = ''.join(char for char in cleaned_text if not char.isspace())
            return cleaned[:20] if cleaned else ""
        except Exception as e:
            print(f"提取描述时发生异常: {e}")
            return ""

    def _export_error_file(self, file_path: str, error_msg: str):
        """导出错误文件到指定目录"""
        try:
            import shutil
            
            # 创建错误文件目录
            error_dir = os.path.join(os.path.dirname(file_path), self.error_export_folder)
            if not os.path.exists(error_dir):
                os.makedirs(error_dir, exist_ok=True)
            
            # 构建目标路径
            filename = os.path.basename(file_path)
            dest_path = os.path.join(error_dir, filename)
            
            # 确保文件名唯一
            counter = 1
            name, ext = os.path.splitext(filename)
            while os.path.exists(dest_path):
                new_filename = f"{name}_{counter}{ext}"
                dest_path = os.path.join(error_dir, new_filename)
                counter += 1
            
            # 复制文件
            shutil.copy2(file_path, dest_path)
            
            # 记录错误信息到日志文件
            log_path = os.path.join(error_dir, "error_log.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
                f.write(f"文件: {file_path}\n")
                f.write(f"错误: {error_msg}\n")
                f.write("-" * 50 + "\n")
                
        except Exception as export_error:
            print(f"导出错误文件失败: {str(export_error)}")
