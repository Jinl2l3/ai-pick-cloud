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
    DEFAULT_RETRY_ENABLED,
    DEFAULT_RETRY_COUNT,
    DEFAULT_RETRY_DELAY
)


class NetworkClient:
    def __init__(
        self, 
        url: str = DEFAULT_NETWORK_API_URL, 
        api_key: str = "",
        model: str = DEFAULT_NETWORK_API_MODEL,
        categories: List[str] = None,
        prompt_template: str = None,
        # Retry settings
        retry_enabled: bool = DEFAULT_RETRY_ENABLED,
        retry_count: int = DEFAULT_RETRY_COUNT,
        retry_delay: int = DEFAULT_RETRY_DELAY
    ):
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.categories = categories or CATEGORIES
        self.prompt_template = prompt_template or DEFAULT_PROMPT
        # Retry settings
        self.retry_enabled = retry_enabled
        self.retry_count = retry_count
        self.retry_delay = retry_delay

    def set_model(self, model: str) -> None:
        self.model = model

    def set_prompt_template(self, template: str) -> None:
        self.prompt_template = template

    def set_categories(self, categories: List[str]) -> None:
        self.categories = categories

    def set_api_key(self, api_key: str) -> None:
        self.api_key = api_key

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

    def _build_prompt(self) -> str:
        categories_str = "、".join(self.categories)
        return self.prompt_template.format(categories=categories_str)

    def analyze_image(self, base64_image: str) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return {
                "success": False,
                "error": "API Key 未设置"
            }
        
        max_attempts = self.retry_count + 1 if self.retry_enabled else 1
        
        for attempt in range(max_attempts):
            try:
                prompt = self._build_prompt()
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                payload = {
                    "model": self.model,
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
                    timeout=120
                )

                if response.status_code == 200:
                    result = response.json()
                    ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
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
