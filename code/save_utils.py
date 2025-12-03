import os
import json
import requests
from PIL import Image
from io import BytesIO
import time
from config import SAVE_CONFIG

def save_text_data(platform, data_list, with_emotion=False):
    """保存文本数据到JSON文件"""
    if not data_list:
        print(f"{platform}暂无文本数据可保存")
        return None
    
    save_path = os.path.join(SAVE_CONFIG["text_path"], platform)
    os.makedirs(save_path, exist_ok=True)
    
    suffix = "_带情绪标签" if with_emotion else ""
    file_name = f"{platform}_关键词_{SAVE_CONFIG['keyword']}_文本{suffix}_{int(time.time())}.json"
    file_path = os.path.join(save_path, file_name)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {platform}文本已保存：{file_path}")
    return file_path


def save_image_data(platform, image_urls, post_id):
    """下载并保存图片"""
    if not image_urls:
        print(f"⚠️ 帖子{post_id}无图片可保存")
        return []
    
    save_path = os.path.join(SAVE_CONFIG["image_path"], platform, SAVE_CONFIG['keyword'], post_id)
    os.makedirs(save_path, exist_ok=True)
    
    saved_paths = []
    
    for idx, img_url in enumerate(image_urls, start=1):
        try:
            if platform == "xiaohongshu":
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://www.xiaohongshu.com/",
                    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                }
            else:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://weibo.com/"
                }
            
            response = requests.get(
                img_url, 
                headers=headers, 
                timeout=15, 
                stream=True,
                verify=False
            )
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            if 'webp' in content_type:
                img_format = 'webp'
            elif 'png' in content_type:
                img_format = 'png'
            elif 'gif' in content_type:
                img_format = 'gif'
            else:
                img_format = 'jpeg'
            
            with Image.open(BytesIO(response.content)) as img:
                if img.format:
                    img_format = img.format.lower()
                img_name = f"图片_{idx}.{img_format}"
                img_save_path = os.path.join(save_path, img_name)
                
                if img.mode in ('RGBA', 'P') and img_format == 'jpeg':
                    img = img.convert('RGB')
                
                img.save(img_save_path)
                saved_paths.append(img_save_path)
            
            print(f"📷 下载成功：{img_save_path}")
        
        except Exception as e:
            print(f"❌ 下载图片失败（URL：{img_url[:50]}...）：{str(e)[:50]}")
    
    return saved_paths


def save_analyzed_data(data_list, filename_prefix="analyzed"):
    """保存带情绪分析结果的数据"""
    if not data_list:
        print("暂无分析数据可保存")
        return None
    
    save_path = "./data/analyzed"
    os.makedirs(save_path, exist_ok=True)
    
    file_name = f"{filename_prefix}_{SAVE_CONFIG['keyword']}_{int(time.time())}.json"
    file_path = os.path.join(save_path, file_name)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 分析数据已保存：{file_path}")
    return file_path


def save_statistics(stats, platform="all"):
    """保存情绪统计数据"""
    save_path = "./data/analyzed"
    os.makedirs(save_path, exist_ok=True)
    
    file_name = f"stats_{platform}_{SAVE_CONFIG['keyword']}_{int(time.time())}.json"
    file_path = os.path.join(save_path, file_name)
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 统计数据已保存：{file_path}")
    return file_path


def get_all_saved_images(platform=None):
    """获取所有已保存的图片路径"""
    base_path = os.path.join(SAVE_CONFIG["image_path"])
    image_paths = []
    
    if platform:
        search_path = os.path.join(base_path, platform)
    else:
        search_path = base_path
    
    if not os.path.exists(search_path):
        return image_paths
    
    for root, dirs, files in os.walk(search_path):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                image_paths.append(os.path.join(root, file))
    
    return image_paths


if __name__ == "__main__":
    print("✅ save_utils.py 加载成功！")
    print("✅ 函数列表：", [func for func in dir() if callable(globals().get(func)) and not func.startswith("_")])
