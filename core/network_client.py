import requests
import json
import time
from typing import Optional, Dict, Any, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    DEFAULT_NETWORK_API_URL, 
    DEFAULT_NETWORK_API_MODEL, 
    CATEGORIES, 
    DEFAULT_PROMPT,
    DEFAULT_VIDEO_PROMPT,
    DEFAULT_RETRY_ENABLED,
    DEFAULT_RETRY_COUNT,
    DEFAULT_RETRY_DELAY,
    DEFAULT_REQUEST_TIMEOUT
)


class NetworkClient:
    def __init__(
        self, 
        url: str = DEFAULT_NETWORK_API_URL, 
        api_key: str = "",
        model: str = DEFAULT_NETWORK_API_MODEL,
        models: List[str] = None,
        categories: List[str] = None,
        prompt_template: str = None,
        video_prompt_template: str = None,
        # Retry settings
        retry_enabled: bool = DEFAULT_RETRY_ENABLED,
        retry_count: int = DEFAULT_RETRY_COUNT,
        retry_delay: int = DEFAULT_RETRY_DELAY,
        request_timeout: int = DEFAULT_REQUEST_TIMEOUT,
        # Round robin settings
        round_robin: bool = True,
        # Model concurrency settings
        model_max_concurrent: int = 2
    ):
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.models = models or [model]  # 多个模型列表
        self.current_model_index = 0  # 当前模型索引
        self.round_robin = round_robin  # 是否启用轮询
        self.categories = categories or CATEGORIES
        self.prompt_template = prompt_template or DEFAULT_PROMPT
        self.video_prompt_template = video_prompt_template or DEFAULT_VIDEO_PROMPT
        # Retry settings
        self.retry_enabled = retry_enabled
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.request_timeout = request_timeout
        # Model concurrency settings
        self.model_max_concurrent = model_max_concurrent  # 每个模型最大并发数
        # 模型活跃请求计数
        self.model_active_requests = {model: 0 for model in self.models}
        # 总请求计数
        self.total_request_count = 0
        # 线程锁，确保轮询时的线程安全
        import threading
        self.lock = threading.Lock()

    def set_model(self, model: str) -> None:
        self.model = model

    def set_prompt_template(self, template: str) -> None:
        self.prompt_template = template

    def set_categories(self, categories: List[str]) -> None:
        self.categories = categories

    def set_api_key(self, api_key: str) -> None:
        self.api_key = api_key

    def set_models(self, models: List[str]) -> None:
        """设置模型列表"""
        self.models = models or [self.model]
        self.current_model_index = 0
        # 更新模型活跃请求计数
        new_active_requests = {model: 0 for model in self.models}
        # 保留现有模型的计数
        for model in new_active_requests:
            if model in self.model_active_requests:
                new_active_requests[model] = self.model_active_requests[model]
        self.model_active_requests = new_active_requests

    def get_next_model(self) -> str:
        """获取下一个模型（轮询+随机+负载均衡）"""
        import random
        import time
        if not self.round_robin or len(self.models) <= 1:
            return self.model
        
        max_wait_attempts = 5
        wait_time = 1
        
        for attempt in range(max_wait_attempts):
            with self.lock:
                # 首先尝试选择活跃请求数低于最大值的模型
                available_models = [
                    model for model in self.models 
                    if self.model_active_requests.get(model, 0) < self.model_max_concurrent
                ]
                
                if available_models:
                    # 优先选择活跃请求数最少的模型
                    available_models.sort(key=lambda m: self.model_active_requests.get(m, 0))
                    return available_models[0]
            
            # 如果所有模型都达到最大并发，等待一段时间再重试
            if attempt < max_wait_attempts - 1:
                print(f"所有模型都达到最大并发数 ({self.model_max_concurrent})，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                wait_time *= 2  # 指数退避
        
        # 如果等待后仍然没有可用模型，使用轮询选择
        with self.lock:
            model = self.models[self.current_model_index]
            self.current_model_index = (self.current_model_index + 1) % len(self.models)
            return model

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        
        try:
            # 简单的API调用测试
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "你是一个有用的助手"},
                    {"role": "user", "content": "测试连接"}
                ],
                "max_tokens": 10
            }
            
            response = requests.post(self.url, json=payload, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"网络连接失败: {str(e)}")
            return False

    def _build_prompt(self, is_video: bool = False, structured_output_prompt: str = "", rename_prompt: str = None) -> str:
        categories_str = "、".join(self.categories)
        
        if is_video:
            template = self.video_prompt_template
        else:
            template = self.prompt_template
        
        prompt = template.replace("{categories}", categories_str)
        
        if rename_prompt:
            prompt = prompt + "\n\n" + rename_prompt
            
        return prompt + f"\n\n{structured_output_prompt}"

    def analyze_image(self, base64_image: str, is_video: bool = False, structured_output_prompt: str = "", rename_prompt: str = None) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return {
                "success": False,
                "error": "API Key 未设置"
            }
        
        max_attempts = self.retry_count + 1 if self.retry_enabled else 1
        
        # 获取轮询模型
        current_model = self.get_next_model()
        
        # 增加总请求计数和模型活跃请求计数
        with self.lock:
            self.total_request_count += 1
            self.model_active_requests[current_model] = self.model_active_requests.get(current_model, 0) + 1
        
        print(f"网络API请求 (总次数: {self.total_request_count}) 使用模型: {current_model}")
        
        try:
            for attempt in range(max_attempts):
                try:
                    prompt = self._build_prompt(is_video, structured_output_prompt, rename_prompt)
                    
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    }
                    
                    payload = {
                        "model": current_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": prompt
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64_image}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "max_tokens": 4096,
                        "temperature": 0.3
                    }

                    response = requests.post(
                        self.url,
                        json=payload,
                        headers=headers,
                        timeout=self.request_timeout
                    )

                    if response.status_code == 200:
                        result = response.json()
                        ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                        
                        # 打印AI返回的原始响应（用于调试）
                        print(f"AI返回结果 (模型: {current_model}):")
                        print(f"  原始响应: {ai_response[:200]}..." if len(ai_response) > 200 else f"  原始响应: {ai_response}")
                        
                        category = self._extract_category(ai_response)
                        return {
                            "success": True,
                            "category": category,
                            "raw_response": ai_response
                        }
                    else:
                        # 网络错误，可能需要重试
                        error_msg = f"HTTP {response.status_code}: {response.text}"
                        if attempt < max_attempts - 1:
                            print(f"尝试 {attempt + 1}/{max_attempts} 失败: {error_msg}")
                            print(f"等待 {self.retry_delay} 秒后重试...")
                            time.sleep(self.retry_delay)
                            continue
                        return {
                            "success": False,
                            "error": error_msg
                        }
                except Exception as e:
                    error_msg = str(e)
                    if attempt < max_attempts - 1:
                        print(f"尝试 {attempt + 1}/{max_attempts} 失败: {error_msg}")
                        print(f"等待 {self.retry_delay} 秒后重试...")
                        time.sleep(self.retry_delay)
                        continue
                    return {
                        "success": False,
                        "error": error_msg
                    }
        finally:
            # 减少模型活跃请求计数（请求完全结束后减少）
            with self.lock:
                if current_model in self.model_active_requests:
                    self.model_active_requests[current_model] = max(0, self.model_active_requests[current_model] - 1)

    def _extract_category(self, ai_response: str) -> str:
        response_lower = ai_response.lower()
        
        for category in self.categories:
            if category in ai_response:
                return category
        
        for category in self.categories:
            category_lower = category.lower()
            if category_lower in response_lower:
                return category
        
        return self.categories[-1]
