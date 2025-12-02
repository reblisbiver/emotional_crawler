from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from config import XHS_CONFIG, WEIBO_CONFIG, SAVE_CONFIG
from save_utils import save_image_data

def crawl_xiaohongshu(driver):
    """
    爬取小红书包含关键词的帖子（文本+图片）- 修复定位问题
    :param driver: 已登录的浏览器驱动
    :return: 文本数据列表
    """
    print("开始爬取小红书数据...")
    text_data = []
    keyword = SAVE_CONFIG["keyword"]
    
    try:
        # 构造搜索URL并访问（简化URL，避免多余参数干扰）
        search_url = f"{XHS_CONFIG['search_url']}?keyword={keyword}"
        driver.get(search_url)
        time.sleep(5)
        
        # 滚动页面加载更多内容（2次滚动，确保帖子加载完整）
        for i in range(2):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(driver, 5).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(1)  # 额外等待动态内容加载
        
        # 问题1修复：根据你提供的帖子XPATH，提取精准定位规则
        # 你的帖子XPATH：/html/body/div[2]/div[1]/div[2]/div[2]/div/div/div[3]/div[1]/section[1]
        # 提取特征：div[3]/div[1]下的section（帖子容器），避免定位到非帖子元素
        print("正在查找小红书帖子...")
        post_cards = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, 
                "//div[contains(@class, 'search-result')]/div[3]/div[1]/section | "  # 匹配你提供的XPATH层级
                "//div[2]/div[1]/div[2]/div[2]/div/div/div[3]/div[1]/section"  # 完全匹配你的帖子父级路径
            ))
        )
        print(f"找到{len(post_cards)}条小红书帖子（已精准匹配帖子容器）")
        
        for idx, card in enumerate(post_cards, 1):
            try:
                print(f"\n正在处理第{idx}条小红书帖子...")
                # 确保帖子卡片可点击后再点击（避免动态加载未完成）
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable(card))
                driver.execute_script("arguments[0].click();", card)  # 用JS点击，避免遮挡
                time.sleep(4)  # 等待详情页完全渲染（小红书详情页加载较慢）
                
                # 问题1补充：关闭可能弹出的广告/弹窗（避免干扰操作）
                try:
                    close_btn = driver.find_element(By.XPATH, "//button[contains(text(), '关闭') or @class='close']")
                    close_btn.click()
                except:
                    pass
                
                # 调整iframe逻辑：先判断是否有iframe，无则直接操作（根据你的详情页XPath，可能无iframe）
                try:
                    iframe = driver.find_element(By.XPATH, "//iframe[contains(@src, 'note')]")
                    driver.switch_to.frame(iframe)
                    print("→ 详情页存在iframe，已切换")
                except:
                    print("→ 详情页无iframe，直接提取内容")
                
                # 提取帖子ID（从详情页URL获取，确保唯一）
                current_url = driver.current_url
                post_id = current_url.split("/")[-1].split("?")[0] if "note" in current_url else f"xhs_{idx}_{int(time.time())}"
                print(f"→ 帖子ID：{post_id}")
                
                # 问题3修复：根据你提供的文本XPATH提取内容
                # 你的文本XPATH：/html/body/div[5]/div[1]/div[4]/div[2]/div[1]/div[1]/span/span
                # 提取特征：div[5]/div[1]/div[4]下的span嵌套（精准层级匹配）
                try:
                    content = WebDriverWait(driver, 8).until(
                        EC.presence_of_element_located((By.XPATH, 
                            "//div/div[1]/div[4]/div[2]/div[1]/div[1]/span/span | "  # 相对层级（适配不同div索引）
                            "/html/body/div[5]/div[1]/div[4]/div[2]/div[1]/div[1]/span/span"  # 绝对路径兜底
                        ))
                    ).text.strip()
                    print(f"→ 文本内容：{content[:50]}...")  # 打印前50字预览
                except Exception as e:
                    content = "无文本内容"
                    print(f"→ 提取文本失败：{str(e)}")
                
                # 问题2修复：根据你提供的图片XPATH提取图片
                # 你的图片XPATH：/html/body/div[5]/div[1]/div[2]/div/div/div[2]/div/div[2]/div/div/img
                # 提取特征：div[2]/div/div[2]/div/div[2]/div/div/img（精准层级匹配）
                try:
                    img_elements = WebDriverWait(driver, 5).until(
                        EC.presence_of_all_elements_located((By.XPATH, 
                            "//div/div[1]/div[2]/div/div/div[2]/div/div[2]/div/div/img | "  # 相对层级
                            "/html/body/div[5]/div[1]/div[2]/div/div/div[2]/div/div[2]/div/div/img"  # 绝对路径兜底
                        ))
                    )
                    img_urls = [img.get_attribute("src") for img in img_elements if img.get_attribute("src")]
                    print(f"→ 找到{len(img_urls)}张图片")
                except Exception as e:
                    img_urls = []
                    print(f"→ 提取图片失败：{str(e)}")
                
                # 保存图片
                if img_urls:
                    save_image_data("xiaohongshu", img_urls, post_id)
                else:
                    print("→ 无图片可保存")
                
                # 构造文本数据
                post_data = {
                    "platform": "xiaohongshu",
                    "post_id": post_id,
                    "url": current_url,
                    "content": content,
                    "image_count": len(img_urls),
                    "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                }
                text_data.append(post_data)
                
                # 关闭详情页，返回列表页（优先点击关闭按钮，兜底用返回）
                try:
                    close_btn = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '关闭') or @class='close-btn']"))
                    )
                    close_btn.click()
                except:
                    driver.execute_script("window.history.back();")
                driver.switch_to.default_content()  # 确保退出iframe（无论之前是否切换）
                time.sleep(2)
                
            except Exception as e:
                print(f"处理第{idx}条小红书帖子失败：{str(e)}")
                driver.switch_to.default_content()
                time.sleep(1)
                continue
        
        print(f"\n小红书爬取完成，共获取{len(text_data)}条有效数据")
        return text_data
    
    except Exception as e:
        print(f"小红书爬取主流程失败：{str(e)}")
        return text_data

def crawl_weibo(driver):
    """
    爬取微博包含关键词的帖子（文本+图片）- 修复图片定位问题
    :param driver: 已登录的浏览器驱动
    :return: 文本数据列表
    """
    print("开始爬取微博数据...")
    text_data = []
    keyword = SAVE_CONFIG["keyword"]
    
    try:
        # 构造搜索URL并访问（按综合排序，确保结果完整）
        search_url = f"{WEIBO_CONFIG['search_url']}?q={keyword}&typeall=1&suball=1&timescope=all&Refer=g"
        driver.get(search_url)
        time.sleep(5)
        
        # 滚动页面加载更多内容（2次滚动）
        for i in range(2):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(driver, 3).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(1)
        
        # 获取所有微博卡片（保留原有稳定定位）
        weibo_cards = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'card-wrap') and not(contains(@class, 'ad'))]"))
        )
        print(f"找到{len(weibo_cards)}条微博（已过滤广告）")
        
        for idx, card in enumerate(weibo_cards, 1):
            try:
                print(f"\n正在处理第{idx}条微博...")
                # 提取帖子ID（保留原有逻辑）
                try:
                    # 找到用户名称对应的a标签（根据你提供的HTML结构）
                    user_a_tag = card.find_element(By.XPATH, ".//a[contains(@class, 'name') and @nick-name]")
                    # 提取nick-name属性（用户昵称）
                    nick_name = user_a_tag.get_attribute("nick-name").strip()
                    # 提取主页链接（href属性，补全http:协议）
                    user_homepage = user_a_tag.get_attribute("href").strip() if user_a_tag.get_attribute("href") else "无"
                    # 提取用户ID（从主页链接中截取：weibo.com/后面到?之前的部分）
                    user_id = user_homepage.split("weibo.com/")[-1].split("?")[0] if "weibo.com/" in user_homepage else "无"
                    print(f"→ 用户昵称：{nick_name} | 用户ID：{user_id} | 主页链接：{user_homepage}")
                except Exception as e:
                    nick_name = "无"
                    user_id = "无"
                    user_homepage = "无"
                    print(f"→ 提取用户信息失败：{str(e)}")
                # 2. 文本提取（原有正确逻辑，完全保留）
                try:
                    content_element = card.find_element(By.XPATH, ".//p[contains(@class, 'txt') or contains(@class, 'weibo-content')]")
                    content = content_element.text.strip()
                    print(f"→ 文本内容：{content[:50]}...")  # 预览前50字
                except Exception as e:
                    content = "无文本内容"
                    print(f"→ 提取文本失败：{str(e)}")

                # 问题4修复：根据你提供的图片XPATH提取图片
                # 你的图片XPATH：/html/body/div[1]/div[2]/div/div[2]/div[1]/div[1]/div[2]/div/div[1]/div[2]/div[3]/div/ul/li[1]/img
                # 提取特征：div[3]/div/ul/li//img（微博图片统一层级：内容区第3个div下的ul/li/img）
                try:
                    # 从当前卡片内精准定位图片（避免跨卡片匹配）
                    img_elements = card.find_elements(By.XPATH, 
                        ".//img[contains(@src, 'sinaimg.cn') and contains(@src, 'wx')]"
                    )
                    img_urls = [img.get_attribute("src") for img in img_elements if img.get_attribute("src")]
                    print(f"→ 找到{len(img_urls)}张图片")
                except Exception as e:
                    img_urls = []
                    print(f"→ 提取图片失败：{str(e)}")

                # 链接提取
                try:
                    match_str = user_id + '/'
                    post_link_elem = card.find_element(By.XPATH, f".//a[contains(@href, '{match_str}')]")
                    post_link = post_link_elem.get_attribute("href").strip()
                    print(f"→ 帖子链接：{post_link}")
                except Exception as e:
                    post_link = ""
                    print(f"→ 提取帖子链接失败：{str(e)}")

                               
                # 保存图片
                if img_urls:
                    save_image_data("weibo", img_urls, user_id)
                else:
                    print("→ 无图片可保存")
                
                # 构造文本数据
                post_data = {
                    "platform": "weibo",
                    "user_id": user_id,  # 新增：用户ID
                    "nick_name": nick_name,  # 新增：用户昵称
                    "user_homepage": user_homepage,  # 新增：用户主页链接
                    "url": post_link,  # 使用提取的帖子链接
                    "content": content,
                    "image_count": len(img_urls),
                    "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                }
                text_data.append(post_data)
                
            except Exception as e:
                print(f"处理第{idx}条微博失败：{str(e)}")
                continue
        
        print(f"\n微博爬取完成，共获取{len(text_data)}条有效数据")
        return text_data
    
    except Exception as e:
        print(f"微博爬取主流程失败：{str(e)}")
        return text_data