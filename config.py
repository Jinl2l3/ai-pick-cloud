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
DEFAULT_NETWORK_API_MODEL_MAX_CONCURRENT = 2  # 每个模型最大并发数
DEFAULT_NETWORK_API_MODELS = [
    "Qwen/Qwen3-VL-8B-Instruct",
    "Pro/zai-org/GLM-4.7",
    "deepseek-ai/DeepSeek-V3.2",
    "gemini-3-pro-low"
]
DEFAULT_NETWORK_API_ROUND_ROBIN = True  # 启用模型轮询

# Rename configuration
DEFAULT_RENAME_ENABLED = False
DEFAULT_RENAME_PROMPT = "请为这张图片生成一个简短的自然语言描述，不超过20个字符，描述图片的主要内容和特征。"
DEFAULT_VIDEO_RENAME_PROMPT = "请为这张视频的多个关键帧拼合而成的图像生成一个简短的自然语言描述，不超过20个字符，描述图片的主要内容。无需描述拼接。"
DEFAULT_RENAME_INCLUDE_ORIGINAL_NAME = False
DEFAULT_RENAME_DATE_TYPE = "none"  # Options: none, create, modify, access
DEFAULT_RENAME_DATE_FORMAT = "%Y%m%d"

# Network retry configuration
DEFAULT_RETRY_ENABLED = True
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 2  # seconds
DEFAULT_REQUEST_TIMEOUT = 180  # seconds - 网络请求超时时间
DEFAULT_ERROR_EXPORT_ENABLED = True
DEFAULT_ERROR_EXPORT_FOLDER = "error_files"

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

DEFAULT_VIDEO_PROMPT = """请分析这张图片，将其归类到以下类别之一：{categories}。
执行逻辑（按顺序检查）：
注意：这是一个视频的多个关键帧拼合而成的图像，请综合分析所有帧的内容来确定视频的主要类别。
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
DEFAULT_OPERATION_MODE = "copy"
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
        "network_api_model_max_concurrent": DEFAULT_NETWORK_API_MODEL_MAX_CONCURRENT,
        "available_network_models": DEFAULT_NETWORK_API_MODELS.copy(),
        "network_api_round_robin": DEFAULT_NETWORK_API_ROUND_ROBIN,
        "categories": CATEGORIES.copy(),
        "prompt": DEFAULT_PROMPT,
        "video_prompt": DEFAULT_VIDEO_PROMPT,
        "max_concurrent": DEFAULT_MAX_CONCURRENT,
        "video_frame_count": DEFAULT_VIDEO_FRAME_COUNT,
        "video_frame_mode": DEFAULT_VIDEO_FRAME_MODE,
        "operation_mode": DEFAULT_OPERATION_MODE,
        "process_images": True,
        "process_videos": True,
        "image_ai_enabled": True,
        "video_ai_enabled": True,
        "time_source": DEFAULT_TIME_SOURCE,
        "folder_structure": DEFAULT_FOLDER_STRUCTURE,
        # Rename settings
        "rename_enabled": DEFAULT_RENAME_ENABLED,
        "rename_prompt": DEFAULT_RENAME_PROMPT,
        "video_rename_prompt": DEFAULT_VIDEO_RENAME_PROMPT,
        "rename_include_original_name": DEFAULT_RENAME_INCLUDE_ORIGINAL_NAME,
        "rename_date_type": DEFAULT_RENAME_DATE_TYPE,
        "rename_date_format": DEFAULT_RENAME_DATE_FORMAT,
        # Network retry settings
        "retry_enabled": DEFAULT_RETRY_ENABLED,
        "retry_count": DEFAULT_RETRY_COUNT,
        "retry_delay": DEFAULT_RETRY_DELAY,
        "request_timeout": DEFAULT_REQUEST_TIMEOUT,
        "error_export_enabled": DEFAULT_ERROR_EXPORT_ENABLED,
        "error_export_folder": DEFAULT_ERROR_EXPORT_FOLDER
    }
