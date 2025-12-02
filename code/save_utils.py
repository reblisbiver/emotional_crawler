import os
import json
import requests
from PIL import Image
from io import BytesIO
import time  # 确保导入time模块（之前可能遗漏）
from config import SAVE_CONFIG  # 导入保存路径配置

def save_text_data(platform, data_list):
    """保存文本数据到JSON文件（被main.py调用）"""
    if not data_list:
        print(f"{platform}暂无文本数据可保存")
        return
    
    # 构建保存路径（兼容之前的配置）
    save_path = os.path.join(SAVE_CONFIG["text_path"], platform)
    os.makedirs(save_path, exist_ok=True)  # 确保目录存在
    
    # 生成带时间戳的文件名，避免重复
    file_name = f"{platform}_关键词_{SAVE_CONFIG['keyword']}_文本_{int(time.time())}.json"
    file_path = os.path.join(save_path, file_name)
    
    # 保存JSON（确保中文正常显示）
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {platform}文本已保存：{file_path}")

def save_image_data(platform, image_urls, post_id):
    """下载并保存图片（被crawler_utils.py调用，核心函数）"""
    if not image_urls:
        print(f"⚠️  帖子{post_id}无图片可保存")
        return
    
    # 构建图片保存路径（按平台+帖子ID分类）
    save_path = os.path.join(SAVE_CONFIG["image_path"], platform, SAVE_CONFIG['keyword'], post_id)
    os.makedirs(save_path, exist_ok=True)  # 自动创建目录
    
    # 批量下载图片
    for idx, img_url in enumerate(image_urls, start=1):
        try:
            # 添加请求头，避免被平台反爬
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Referer": "https://www.xiaohongshu.com/" if platform == "xiaohongshu" else "https://weibo.com/"
            }
            
            # 发送请求下载图片（超时15秒，防止卡住）
            response = requests.get(
                img_url, 
                headers=headers, 
                timeout=15, 
                stream=True,
                verify=False  # 忽略SSL证书错误（部分图片URL可能有问题）
            )
            response.raise_for_status()  # 若HTTP状态码错误（如404），直接抛出异常
            
            # 用Pillow打开图片并保存
            with Image.open(BytesIO(response.content)) as img:
                # 自动识别图片格式（jpg/png等）
                img_format = img.format.lower() if img.format else "png"
                img_name = f"图片_{idx}.{img_format}"
                img_save_path = os.path.join(save_path, img_name)
                img.save(img_save_path)
            
            print(f"📷 下载成功：{img_save_path}")
        
        except Exception as e:
            print(f"❌ 下载图片失败（URL：{img_url}）：{str(e)[:50]}...")  # 只显示前50个字符，避免输出过长

# 测试代码：运行save_utils.py时，验证函数是否能正常加载
if __name__ == "__main__":
    print("✅ save_utils.py 加载成功！")
    print("✅ 函数列表：", [func for func in dir() if callable(globals()[func]) and not func.startswith("_")])