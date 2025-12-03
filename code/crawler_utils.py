"""
爬虫核心逻辑
- 爬取文本 → 情绪筛选 → 符合条件才存储
- 爬取图片 → 人体检测 → 情绪筛选 → 符合条件才存储
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import os
import requests
from config import XHS_CONFIG, WEIBO_CONFIG, SAVE_CONFIG, CRAWL_CONFIG
from emotion_filter import filter_text


def save_filtered_text(platform, text_data, emotion_data):
    """保存通过筛选的文本"""
    import json
    from datetime import datetime
    
    save_dir = os.path.join(SAVE_CONFIG["text_path"], platform)
    os.makedirs(save_dir, exist_ok=True)
    
    filename = f"filtered_{datetime.now().strftime('%Y%m%d')}.json"
    filepath = os.path.join(save_dir, filename)
    
    existing_data = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
    
    save_item = {
        **text_data,
        "emotion_analysis": emotion_data
    }
    existing_data.append(save_item)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)
    
    return True


def save_image_for_local_analysis(platform, image_url, post_id, index):
    """
    下载图片用于本地分析
    图片情绪筛选需要在本地运行
    """
    save_dir = os.path.join(SAVE_CONFIG["image_path"], platform, "pending")
    os.makedirs(save_dir, exist_ok=True)
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://weibo.com/" if platform == "weibo" else "https://www.xiaohongshu.com/"
        }
        resp = requests.get(image_url, headers=headers, timeout=15)
        
        if resp.status_code == 200:
            filename = f"{post_id}_{index}.jpg"
            filepath = os.path.join(save_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(resp.content)
            
            return filepath
    except Exception as e:
        print(f"  图片下载失败: {str(e)[:30]}")
    
    return None


def crawl_xiaohongshu(driver, target_texts=None, target_images=None):
    """
    爬取小红书
    逻辑：爬取 → 情绪筛选 → 符合条件才存储
    """
    print("=" * 60)
    print("开始爬取小红书数据...")
    print("=" * 60)
    
    saved_texts = 0
    saved_images = 0
    target_texts = target_texts or CRAWL_CONFIG["target_texts"]
    target_images = target_images or CRAWL_CONFIG["target_images"]
    processed_ids = set()
    
    stats = {"total_checked": 0, "texts_saved": 0, "images_downloaded": 0}
    
    try:
        print(f"→ 访问探索页面：{XHS_CONFIG['explore_url']}")
        driver.get(XHS_CONFIG["explore_url"])
        time.sleep(CRAWL_CONFIG["page_load_wait"])
        
        if "login" in driver.current_url.lower():
            print("⚠️ 需要登录，请先完成登录")
            return stats
        
        scroll_count = 0
        max_scrolls = CRAWL_CONFIG["max_pages"] * 5
        
        while (saved_texts < target_texts or saved_images < target_images) and scroll_count < max_scrolls:
            scroll_count += 1
            print(f"\n--- 滚动 {scroll_count} | 文本 {saved_texts}/{target_texts} | 图片 {saved_images}/{target_images} ---")
            
            post_cards = []
            selectors = [
                "//section[contains(@class, 'note-item')]",
                "//div[contains(@class, 'note-item')]",
                "//a[contains(@href, '/explore/')]",
            ]
            
            for selector in selectors:
                try:
                    post_cards = driver.find_elements(By.XPATH, selector)
                    if post_cards:
                        break
                except:
                    continue
            
            if not post_cards:
                print("⚠️ 未找到帖子")
                break
            
            for card in post_cards:
                if saved_texts >= target_texts and saved_images >= target_images:
                    break
                
                try:
                    card_href = card.get_attribute("href") or ""
                    post_id_match = re.search(r'/explore/([a-zA-Z0-9]+)', card_href)
                    if not post_id_match:
                        continue
                    
                    post_id = post_id_match.group(1)
                    if post_id in processed_ids:
                        continue
                    
                    processed_ids.add(post_id)
                    stats["total_checked"] += 1
                    
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", card)
                    time.sleep(2)
                    
                    content = ""
                    content_selectors = [
                        "//div[contains(@class, 'note-text')]//span",
                        "//div[contains(@class, 'desc')]//span",
                    ]
                    
                    for sel in content_selectors:
                        try:
                            elem = WebDriverWait(driver, 3).until(
                                EC.presence_of_element_located((By.XPATH, sel))
                            )
                            content = elem.text.strip()
                            if content and len(content) > 10:
                                break
                        except:
                            continue
                    
                    if content and saved_texts < target_texts:
                        should_save, emotion_data = filter_text(content, post_id)
                        
                        if should_save:
                            text_data = {
                                "platform": "xiaohongshu",
                                "post_id": post_id,
                                "content": content,
                                "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S")
                            }
                            save_filtered_text("xiaohongshu", text_data, emotion_data)
                            saved_texts += 1
                            stats["texts_saved"] += 1
                            dominant = emotion_data.get("dominant", "?")
                            print(f"  ✓ 文本已保存 [{saved_texts}/{target_texts}] 主情绪: {dominant}")
                        else:
                            print(f"  ✗ 文本不符合情绪条件，跳过")
                    
                    if saved_images < target_images:
                        img_urls = []
                        try:
                            img_elements = driver.find_elements(By.XPATH, 
                                "//div[contains(@class, 'swiper')]//img[@src]")
                            for img in img_elements:
                                src = img.get_attribute("src")
                                if src and "xhscdn" in src and "avatar" not in src.lower():
                                    img_urls.append(src)
                        except:
                            pass
                        
                        for idx, url in enumerate(img_urls[:3]):
                            if saved_images >= target_images:
                                break
                            filepath = save_image_for_local_analysis("xiaohongshu", url, post_id, idx)
                            if filepath:
                                saved_images += 1
                                stats["images_downloaded"] += 1
                                print(f"  ✓ 图片已下载 [{saved_images}/{target_images}]")
                    
                    try:
                        close_btn = driver.find_element(By.XPATH, "//div[contains(@class, 'close')]")
                        close_btn.click()
                    except:
                        driver.execute_script("window.history.back();")
                    
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"  处理失败: {str(e)[:50]}")
                    continue
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(CRAWL_CONFIG["scroll_pause"])
        
        print(f"\n{'='*60}")
        print(f"小红书爬取完成！")
        print(f"检查总数: {stats['total_checked']} | 保存文本: {stats['texts_saved']} | 下载图片: {stats['images_downloaded']}")
        print(f"{'='*60}")
        
        return stats
    
    except Exception as e:
        print(f"小红书爬取失败：{str(e)}")
        return stats


def crawl_weibo(driver, target_texts=None, target_images=None):
    """
    爬取微博热门
    逻辑：爬取 → 情绪筛选 → 符合条件才存储
    """
    print("=" * 60)
    print("开始爬取微博数据...")
    print("=" * 60)
    
    saved_texts = 0
    saved_images = 0
    target_texts = target_texts or CRAWL_CONFIG["target_texts"]
    target_images = target_images or CRAWL_CONFIG["target_images"]
    processed_ids = set()
    
    stats = {"total_checked": 0, "texts_saved": 0, "images_downloaded": 0}
    
    try:
        page = 1
        
        while (saved_texts < target_texts or saved_images < target_images) and page <= CRAWL_CONFIG["max_pages"]:
            print(f"\n--- 第 {page} 页 | 文本 {saved_texts}/{target_texts} | 图片 {saved_images}/{target_images} ---")
            
            url = f"{WEIBO_CONFIG['home_url']}?page={page}"
            driver.get(url)
            time.sleep(CRAWL_CONFIG["page_load_wait"])
            
            for i in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
            
            try:
                weibo_cards = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, 
                        "//div[contains(@class, 'card-wrap') and not(contains(@class, 'ad'))] | //article[contains(@class, 'Feed')]"))
                )
            except:
                print(f"第 {page} 页未找到微博")
                break
            
            print(f"本页找到 {len(weibo_cards)} 条微博")
            
            for card in weibo_cards:
                if saved_texts >= target_texts and saved_images >= target_images:
                    break
                
                try:
                    mid = card.get_attribute("mid") or card.get_attribute("data-mid") or f"weibo_{page}_{len(processed_ids)}"
                    
                    if mid in processed_ids:
                        continue
                    
                    processed_ids.add(mid)
                    stats["total_checked"] += 1
                    
                    content = ""
                    try:
                        content_elem = card.find_element(By.XPATH, 
                            ".//p[contains(@class, 'txt')] | .//div[contains(@class, 'detail_wbtext')]")
                        content = content_elem.text.strip()
                    except:
                        pass
                    
                    if content and len(content) > 10 and saved_texts < target_texts:
                        should_save, emotion_data = filter_text(content, mid)
                        
                        if should_save:
                            try:
                                user_elem = card.find_element(By.XPATH, ".//a[contains(@class, 'name') or @nick-name]")
                                nick_name = user_elem.get_attribute("nick-name") or user_elem.text.strip()
                            except:
                                nick_name = "未知"
                            
                            text_data = {
                                "platform": "weibo",
                                "mid": mid,
                                "nick_name": nick_name,
                                "content": content,
                                "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S")
                            }
                            save_filtered_text("weibo", text_data, emotion_data)
                            saved_texts += 1
                            stats["texts_saved"] += 1
                            dominant = emotion_data.get("dominant", "?")
                            print(f"  ✓ 文本已保存 [{saved_texts}/{target_texts}] 主情绪: {dominant} | {nick_name}")
                        else:
                            pass
                    
                    if saved_images < target_images:
                        img_urls = []
                        try:
                            img_elements = card.find_elements(By.XPATH, ".//img[contains(@src, 'sinaimg.cn')]")
                            for img in img_elements:
                                src = img.get_attribute("src")
                                if src:
                                    large_src = re.sub(r'(orj\d+|mw\d+|thumb\d+)', 'large', src)
                                    img_urls.append(large_src)
                        except:
                            pass
                        
                        for idx, url in enumerate(img_urls[:3]):
                            if saved_images >= target_images:
                                break
                            filepath = save_image_for_local_analysis("weibo", url, mid, idx)
                            if filepath:
                                saved_images += 1
                                stats["images_downloaded"] += 1
                                print(f"  ✓ 图片已下载 [{saved_images}/{target_images}]")
                    
                except Exception as e:
                    continue
            
            page += 1
        
        print(f"\n{'='*60}")
        print(f"微博爬取完成！")
        print(f"检查总数: {stats['total_checked']} | 保存文本: {stats['texts_saved']} | 下载图片: {stats['images_downloaded']}")
        print(f"{'='*60}")
        
        return stats
    
    except Exception as e:
        print(f"微博爬取失败：{str(e)}")
        return stats
