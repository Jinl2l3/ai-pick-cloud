import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'settings.json')
DB_PATH = os.path.join(os.path.dirname(__file__), 'file_index.db')
MAX_IMAGE_SIZE = 1920

IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
    '.webp', '.ico', '.svg', '.raw', '.heic', '.heif'
}

VIDEO_EXTENSIONS = {
    '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm',
    '.m4v', '.mpeg', '.mpg', '.3gp', '.ogv'
}

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llava:7b"
DEFAULT_MODELS = ["llava:7b", "llava:13b", "bakllava:7b"]

# Network API configuration
DEFAULT_API_TYPE = "ollama"  # Options: ollama, network
DEFAULT_NETWORK_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
DEFAULT_NETWORK_API_KEY = ""
DEFAULT_NETWORK_API_MODEL = "Qwen/Qwen3-VL-8B-Instruct"
DEFAULT_NETWORK_API_MAX_CONCURRENT = 2
DEFAULT_NETWORK_API_MODELS = [
    "Qwen/Qwen3-VL-8B-Instruct",
    "Pro/zai-org/GLM-4.7",
    "deepseek-ai/DeepSeek-V3.2",
    "gemini-3-pro-low"
]

CATEGORIES = [
    "人物",
    "宠物",
    "美食",
    "风景",
    "文档",
    "截图",
    "二次元",
    "影视明星",
    "广告资讯",
    "表情包",
    "其他"
]

DEFAULT_PROMPT = """请分析这张图片，将其归类到以下类别之一：{categories}。
执行逻辑（按顺序检查）：
1. 视觉特征检查：
   - 画面带文字/UI/气泡吗？ -> 【截图】或【表情包】。
   - 画面是动漫/游戏/插画吗？ -> 【二次元】。
   - 画面是明星/剧照/海报吗？ -> 【影视明星】。
   - 画面是排版好的广告或新闻吗？ -> 【广告资讯】。
2. 真实性校验：
   - 只有实拍的人、动物、食物、美景，才能进入对应的核心分类。
   - 若不确定是否为实拍，或者画面内容无意义，统一归类为：【其他】。

要求：
- 只返回一个类别词，不要带任何标点符号。
- 必须且只能从指定列表中选择。"""

DEFAULT_MAX_CONCURRENT = 2
DEFAULT_VIDEO_FRAME_COUNT = 1
DEFAULT_VIDEO_FRAME_MODE = "middle"
DEFAULT_OPERATION_MODE = "move"
DEFAULT_TIME_SOURCE = "earliest"
DEFAULT_FOLDER_STRUCTURE = "category_time"


def load_settings():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return get_default_settings()


def save_settings(settings):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def get_default_settings():
    return {
        "api_type": DEFAULT_API_TYPE,
        "ollama_url": DEFAULT_OLLAMA_URL,
        "ollama_model": DEFAULT_OLLAMA_MODEL,
        "available_models": DEFAULT_MODELS.copy(),
        "network_api_url": DEFAULT_NETWORK_API_URL,
        "network_api_key": DEFAULT_NETWORK_API_KEY,
        "network_api_model": DEFAULT_NETWORK_API_MODEL,
        "network_api_max_concurrent": DEFAULT_NETWORK_API_MAX_CONCURRENT,
        "available_network_models": DEFAULT_NETWORK_API_MODELS.copy(),
        "categories": CATEGORIES.copy(),
        "prompt": DEFAULT_PROMPT,
        "max_concurrent": DEFAULT_MAX_CONCURRENT,
        "video_frame_count": DEFAULT_VIDEO_FRAME_COUNT,
        "video_frame_mode": DEFAULT_VIDEO_FRAME_MODE,
        "operation_mode": DEFAULT_OPERATION_MODE,
        "process_images": True,
        "process_videos": True,
        "time_source": DEFAULT_TIME_SOURCE,
        "folder_structure": DEFAULT_FOLDER_STRUCTURE
    }
