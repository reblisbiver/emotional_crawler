import os
from dotenv import load_dotenv

load_dotenv()

WEIBO_CONFIG = {
    "hot_url": "https://weibo.com/hot/search",
    "home_url": "https://weibo.com",
}

XHS_CONFIG = {
    "explore_url": "https://www.xiaohongshu.com/explore",
    "home_url": "https://www.xiaohongshu.com",
}

SAVE_CONFIG = {
    "text_path": os.getenv("SAVE_TEXT_PATH", "./data/texts"),
    "image_path": os.getenv("SAVE_IMAGE_PATH", "./data/images"),
}

CRAWL_CONFIG = {
    "target_texts": int(os.getenv("TARGET_TEXTS", "100")),
    "target_images": int(os.getenv("TARGET_IMAGES", "100")),
    "max_pages": int(os.getenv("MAX_PAGES", "100")),
    "scroll_pause": 2,
    "page_load_wait": 5,
}

_deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
if not _deepseek_key:
    print("⚠️ 警告：未设置 DEEPSEEK_API_KEY 环境变量，文本情绪分析将不可用")

EMOTION_CONFIG = {
    "emotions": ["喜", "怒", "哀", "惧", "惊", "厌", "中性"],
    "emotions_en": ["happy", "angry", "sad", "fear", "surprise", "disgust", "neutral"],
    "target_emotions": ["喜", "怒", "哀", "惧", "惊", "厌"],
    "min_score": 0.3,
    "deepseek_api_key": _deepseek_key,
    "deepseek_api_url": "https://api.deepseek.com/v1/chat/completions",
}

for path in [SAVE_CONFIG["text_path"], SAVE_CONFIG["image_path"]]:
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, "xiaohongshu"), exist_ok=True)
    os.makedirs(os.path.join(path, "weibo"), exist_ok=True)

print("✅ config.py 加载成功！")
