from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import re
from config import XHS_CONFIG, WEIBO_CONFIG, SAVE_CONFIG, CRAWL_CONFIG
from save_utils import save_image_data

def crawl_xiaohongshu(driver, target_count=None):
    """
    爬取小红书帖子，支持多页滚动直到达到目标条数
    """
    print("=" * 60)
    print("开始爬取小红书数据...")
    print("=" * 60)
    
    text_data = []
    image_data = []
    keyword = SAVE_CONFIG["keyword"]
    target = target_count or CRAWL_CONFIG["target_texts"]
    processed_ids = set()
    
    try:
        search_url = f"{XHS_CONFIG['search_url']}?keyword={keyword}"
        print(f"→ 访问搜索页面：{search_url}")
        driver.get(search_url)
        time.sleep(CRAWL_CONFIG["page_load_wait"])
        
        print(f"→ 当前页面URL：{driver.current_url}")
        print(f"→ 页面标题：{driver.title}")
        
        if "login" in driver.current_url.lower() or "passport" in driver.current_url.lower():
            print("⚠️ 检测到登录页面，可能需要重新登录...")
            driver.save_screenshot("./code/xhs_need_login.png")
            return text_data, image_data
        
        scroll_count = 0
        max_scrolls = CRAWL_CONFIG["max_pages"] * 5
        no_new_count = 0
        
        while len(text_data) < target and scroll_count < max_scrolls:
            scroll_count += 1
            print(f"\n--- 第 {scroll_count} 次滚动 | 已采集 {len(text_data)}/{target} 条 ---")
            
            post_cards = []
            selectors = [
                "//section[contains(@class, 'note-item')]",
                "//div[contains(@class, 'note-item')]",
                "//a[contains(@href, '/explore/') and contains(@class, 'cover')]",
                "//div[contains(@class, 'feeds-page')]//section",
                "//div[@class='note-item']//a",
            ]
            
            for selector in selectors:
                try:
                    post_cards = driver.find_elements(By.XPATH, selector)
                    if post_cards:
                        break
                except:
                    continue
            
            if not post_cards:
                print("⚠️ 未找到帖子元素")
                driver.save_screenshot("./code/xhs_debug.png")
                break
            
            new_posts_this_scroll = 0
            
            for card in post_cards:
                if len(text_data) >= target:
                    break
                    
                try:
                    card_href = card.get_attribute("href") or ""
                    post_id_match = re.search(r'/explore/([a-zA-Z0-9]+)', card_href)
                    if not post_id_match:
                        post_id_match = re.search(r'/discovery/item/([a-zA-Z0-9]+)', card_href)
                    
                    if post_id_match:
                        post_id = post_id_match.group(1)
                    else:
                        continue
                    
                    if post_id in processed_ids:
                        continue
                    
                    processed_ids.add(post_id)
                    new_posts_this_scroll += 1
                    
                    print(f"\n正在处理帖子 [{len(text_data)+1}/{target}] ID: {post_id}")
                    
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", card)
                    time.sleep(3)
                    
                    try:
                        close_btn = driver.find_element(By.XPATH, "//div[contains(@class, 'close') or contains(@class, 'mask')]")
                    except:
                        pass
                    
                    current_url = driver.current_url
                    
                    content = ""
                    content_selectors = [
                        "//div[contains(@class, 'note-text')]//span",
                        "//div[contains(@class, 'desc')]//span",
                        "//div[@id='detail-desc']//span",
                        "//div[contains(@class, 'content')]//span/span",
                    ]
                    
                    for sel in content_selectors:
                        try:
                            content_elem = WebDriverWait(driver, 3).until(
                                EC.presence_of_element_located((By.XPATH, sel))
                            )
                            content = content_elem.text.strip()
                            if content and len(content) > 5:
                                break
                        except:
                            continue
                    
                    if content:
                        print(f"→ 文本内容：{content[:50]}...")
                    else:
                        content = "无文本内容"
                        print("→ 未获取到文本内容")
                    
                    img_urls = []
                    img_selectors = [
                        "//div[contains(@class, 'swiper')]//img[@src]",
                        "//div[contains(@class, 'carousel')]//img[@src]",
                        "//div[contains(@class, 'note-slider')]//img[@src]",
                        "//img[contains(@class, 'note-image')]",
                    ]
                    
                    for sel in img_selectors:
                        try:
                            img_elements = driver.find_elements(By.XPATH, sel)
                            for img in img_elements:
                                src = img.get_attribute("src")
                                if src and "xhscdn" in src and src not in img_urls:
                                    if "avatar" not in src.lower():
                                        img_urls.append(src)
                            if img_urls:
                                break
                        except:
                            continue
                    
                    if img_urls:
                        print(f"→ 找到 {len(img_urls)} 张图片")
                        save_image_data("xiaohongshu", img_urls, post_id)
                        for url in img_urls:
                            image_data.append({
                                "platform": "xiaohongshu",
                                "post_id": post_id,
                                "image_url": url,
                                "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S")
                            })
                    else:
                        print("→ 未找到图片")
                    
                    post_data = {
                        "platform": "xiaohongshu",
                        "post_id": post_id,
                        "url": current_url,
                        "content": content,
                        "image_count": len(img_urls),
                        "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    text_data.append(post_data)
                    
                    try:
                        close_btn = driver.find_element(By.XPATH, 
                            "//div[contains(@class, 'close')]//span | //button[contains(@class, 'close')]")
                        close_btn.click()
                    except:
                        driver.execute_script("window.history.back();")
                    
                    time.sleep(1)
                    driver.switch_to.default_content()
                    
                except Exception as e:
                    print(f"处理帖子失败：{str(e)[:80]}")
                    driver.switch_to.default_content()
                    continue
            
            if new_posts_this_scroll == 0:
                no_new_count += 1
                if no_new_count >= 3:
                    print("连续3次未发现新帖子，停止滚动")
                    break
            else:
                no_new_count = 0
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(CRAWL_CONFIG["scroll_pause"])
        
        print(f"\n{'='*60}")
        print(f"小红书爬取完成！共获取 {len(text_data)} 条文本，{len(image_data)} 张图片")
        print(f"{'='*60}")
        return text_data, image_data
    
    except Exception as e:
        print(f"小红书爬取主流程失败：{str(e)}")
        return text_data, image_data


def crawl_weibo(driver, target_count=None):
    """
    爬取微博帖子，支持多页翻页直到达到目标条数
    """
    print("=" * 60)
    print("开始爬取微博数据...")
    print("=" * 60)
    
    text_data = []
    image_data = []
    keyword = SAVE_CONFIG["keyword"]
    target = target_count or CRAWL_CONFIG["target_texts"]
    processed_ids = set()
    
    try:
        page = 1
        
        while len(text_data) < target and page <= CRAWL_CONFIG["max_pages"]:
            print(f"\n--- 第 {page} 页 | 已采集 {len(text_data)}/{target} 条 ---")
            
            search_url = f"{WEIBO_CONFIG['search_url']}?q={keyword}&typeall=1&suball=1&timescope=all&Refer=g&page={page}"
            driver.get(search_url)
            time.sleep(CRAWL_CONFIG["page_load_wait"])
            
            for i in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
            
            try:
                weibo_cards = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, 
                        "//div[contains(@class, 'card-wrap') and not(contains(@class, 'ad'))]"))
                )
            except:
                print(f"第 {page} 页未找到微博卡片，可能已到最后一页")
                break
            
            print(f"本页找到 {len(weibo_cards)} 条微博")
            
            new_posts_this_page = 0
            
            for idx, card in enumerate(weibo_cards, 1):
                if len(text_data) >= target:
                    break
                    
                try:
                    try:
                        user_a_tag = card.find_element(By.XPATH, ".//a[contains(@class, 'name') and @nick-name]")
                        nick_name = user_a_tag.get_attribute("nick-name").strip()
                        user_homepage = user_a_tag.get_attribute("href").strip() or "无"
                        user_id = user_homepage.split("weibo.com/")[-1].split("?")[0] if "weibo.com/" in user_homepage else f"user_{idx}"
                    except:
                        nick_name = "无"
                        user_id = f"user_{page}_{idx}"
                        user_homepage = "无"
                    
                    mid = card.get_attribute("mid") or f"{user_id}_{int(time.time())}"
                    
                    if mid in processed_ids:
                        continue
                    
                    processed_ids.add(mid)
                    new_posts_this_page += 1
                    
                    print(f"\n正在处理微博 [{len(text_data)+1}/{target}] 用户: {nick_name}")
                    
                    try:
                        content_element = card.find_element(By.XPATH, 
                            ".//p[contains(@class, 'txt') or contains(@class, 'weibo-content')]")
                        content = content_element.text.strip()
                        print(f"→ 文本内容：{content[:50]}...")
                    except:
                        content = "无文本内容"
                        print("→ 未获取到文本内容")
                    
                    img_urls = []
                    try:
                        img_elements = card.find_elements(By.XPATH, 
                            ".//img[contains(@src, 'sinaimg.cn')]")
                        for img in img_elements:
                            src = img.get_attribute("src")
                            if src and "orj360" in src:
                                large_src = src.replace("orj360", "large")
                                img_urls.append(large_src)
                            elif src and ("mw690" in src or "thumb" in src):
                                large_src = re.sub(r'(orj\d+|mw\d+|thumb\d+)', 'large', src)
                                img_urls.append(large_src)
                            elif src:
                                img_urls.append(src)
                    except:
                        pass
                    
                    if img_urls:
                        print(f"→ 找到 {len(img_urls)} 张图片")
                        save_image_data("weibo", img_urls, user_id)
                        for url in img_urls:
                            image_data.append({
                                "platform": "weibo",
                                "user_id": user_id,
                                "nick_name": nick_name,
                                "image_url": url,
                                "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S")
                            })
                    else:
                        print("→ 无图片")
                    
                    try:
                        post_link_elem = card.find_element(By.XPATH, f".//a[contains(@href, '{user_id}/')]")
                        post_link = post_link_elem.get_attribute("href").strip()
                    except:
                        post_link = ""
                    
                    post_data = {
                        "platform": "weibo",
                        "mid": mid,
                        "user_id": user_id,
                        "nick_name": nick_name,
                        "user_homepage": user_homepage,
                        "url": post_link,
                        "content": content,
                        "image_count": len(img_urls),
                        "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    text_data.append(post_data)
                    
                except Exception as e:
                    print(f"处理微博失败：{str(e)[:80]}")
                    continue
            
            if new_posts_this_page == 0:
                print("本页无新内容，可能已到最后一页")
                break
            
            page += 1
        
        print(f"\n{'='*60}")
        print(f"微博爬取完成！共获取 {len(text_data)} 条文本，{len(image_data)} 张图片")
        print(f"{'='*60}")
        return text_data, image_data
    
    except Exception as e:
        print(f"微博爬取主流程失败：{str(e)}")
        return text_data, image_data
