import requests
import json
from typing import Optional, Dict, Any, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DEFAULT_OLLAMA_URL, DEFAULT_OLLAMA_MODEL, CATEGORIES, DEFAULT_PROMPT


class OllamaClient:
    def __init__(
        self, 
        url: str = DEFAULT_OLLAMA_URL, 
        model: str = DEFAULT_OLLAMA_MODEL,
        categories: List[str] = None,
        prompt_template: str = None
    ):
        self.url = url.rstrip('/')
        self.model = model
        self.categories = categories or CATEGORIES
        self.prompt_template = prompt_template or DEFAULT_PROMPT

    def set_model(self, model: str) -> None:
        self.model = model

    def set_prompt_template(self, template: str) -> None:
        self.prompt_template = template

    def set_categories(self, categories: List[str]) -> None:
        self.categories = categories

    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def get_available_models(self) -> List[str]:
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = []
                for model in data.get("models", []):
                    models.append(model.get("name", ""))
                return models
        except Exception:
            pass
        return []

    def _build_prompt(self) -> str:
        categories_str = "、".join(self.categories)
        return self.prompt_template.format(categories=categories_str)

    def analyze_image(self, base64_image: str) -> Optional[Dict[str, Any]]:
        try:
            payload = {
                "model": self.model,
                "prompt": self._build_prompt(),
                "images": [base64_image],
                "stream": False,
                "options": {
                    "temperature": 0.3
                }
            }

            response = requests.post(
                f"{self.url}/api/generate",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "").strip()
                category = self._extract_category(ai_response)
                return {
                    "success": True,
                    "category": category,
                    "raw_response": ai_response
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
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
