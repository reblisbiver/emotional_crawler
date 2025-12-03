import os
from dotenv import load_dotenv

load_dotenv()

XHS_CONFIG = {
    "phone": os.getenv("XHS_PHONE", "17350575312"),
    "search_url": "https://www.xiaohongshu.com/search_result"
}

WEIBO_CONFIG = {
    "phone": os.getenv("WEIBO_PHONE", "17350575312"),
    "search_url": "https://s.weibo.com/weibo"
}

SAVE_CONFIG = {
    "text_path": os.getenv("SAVE_TEXT_PATH", "./data/texts"),
    "image_path": os.getenv("SAVE_IMAGE_PATH", "./data/images"),
    "keyword": "牢大"
}

CRAWL_CONFIG = {
    "target_texts": int(os.getenv("TARGET_TEXTS", "20")),
    "target_images": int(os.getenv("TARGET_IMAGES", "20")),
    "max_pages": int(os.getenv("MAX_PAGES", "50")),
    "scroll_pause": 2,
    "page_load_wait": 5,
}

EMOTION_CONFIG = {
    "emotions": ["喜", "怒", "哀", "惧", "惊", "厌", "中性"],
    "emotions_en": ["happy", "angry", "sad", "fear", "surprise", "disgust", "neutral"],
    "deepseek_api_key": os.getenv("DEEPSEEK_API_KEY", "sk-a4890b6f726f4b2591902f5b3ea7c313"),
    "deepseek_api_url": "https://api.deepseek.com/v1/chat/completions",
    "analyze_text": True,
    "analyze_image": True,
}

for path in [SAVE_CONFIG["text_path"], SAVE_CONFIG["image_path"]]:
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, "xiaohongshu"), exist_ok=True)
    os.makedirs(os.path.join(path, "weibo"), exist_ok=True)

os.makedirs("./data/analyzed", exist_ok=True)

print("✅ config.py 加载成功！")
