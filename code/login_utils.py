from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time
import os
import subprocess
import threading
from config import XHS_CONFIG, WEIBO_CONFIG

def create_chrome_driver():
    """创建Chrome浏览器驱动（适配Linux环境）"""
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.cookies": 1,
        "profile.default_content_setting_values.images": 1,
        "profile.user_agent_overrides": {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        }
    })
    options.add_argument("--disable-gpu")
    options.add_argument("--incognito")
    options.add_argument("--lang=zh-CN")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    
    try:
        chromedriver_path = subprocess.check_output(["which", "chromedriver"]).decode().strip()
    except subprocess.CalledProcessError:
        raise FileNotFoundError("\n找不到ChromeDriver！请确认已安装chromedriver")
    
    try:
        chromium_path = subprocess.check_output(["which", "chromium"]).decode().strip()
        options.binary_location = chromium_path
    except subprocess.CalledProcessError:
        pass
    
    driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
        """
    })
    driver.implicitly_wait(5)
    return driver

def wait_for_login_success(driver, platform, timeout=120):
    """
    自动检测扫码登录是否成功（通过页面跳转/元素变化判断）
    :param driver: 浏览器驱动
    :param platform: 平台名称 ("xiaohongshu" 或 "weibo")
    :param timeout: 超时时间（秒），默认120秒
    :return: True=登录成功, False=超时失败
    """
    print(f"⏳ 等待扫码登录（{timeout}秒超时）...")
    start_time = time.time()
    check_interval = 2
    
    while time.time() - start_time < timeout:
        try:
            current_url = driver.current_url
            
            if platform == "xiaohongshu":
                login_indicators = [
                    (By.XPATH, "//div[contains(@class, 'user') or contains(@class, 'avatar')]//img"),
                    (By.XPATH, "//a[contains(@href, '/user/profile')]"),
                    (By.XPATH, "//div[contains(@class, 'sidebar')]//img[contains(@class, 'avatar')]"),
                    (By.XPATH, "//*[contains(@class, 'reds-icon-user')]"),
                ]
                if "passport" not in current_url and "login" not in current_url.lower():
                    for locator in login_indicators:
                        try:
                            element = driver.find_element(*locator)
                            if element:
                                print(f"✅ 检测到登录成功标志！当前URL：{current_url[:50]}...")
                                return True
                        except:
                            continue
                    if "xiaohongshu.com" in current_url and "explore" in current_url:
                        print(f"✅ 检测到已跳转至首页！登录成功")
                        return True
                        
            elif platform == "weibo":
                if "passport" not in current_url and "login" not in current_url.lower():
                    login_indicators = [
                        (By.XPATH, "//a[contains(@class, 'gn_name')]"),
                        (By.XPATH, "//div[contains(@class, 'gn_header')]//img"),
                        (By.XPATH, "//a[contains(@href, '/profile')]"),
                        (By.XPATH, "//span[contains(@class, 'gn_name')]"),
                        (By.XPATH, "//div[contains(@class, 'WB_miniblog')]"),
                    ]
                    for locator in login_indicators:
                        try:
                            element = driver.find_element(*locator)
                            if element:
                                print(f"✅ 检测到登录成功标志！当前URL：{current_url[:50]}...")
                                return True
                        except:
                            continue
                    if "weibo.com" in current_url and ("home" in current_url or current_url.endswith("weibo.com/")):
                        print(f"✅ 检测到已跳转至首页！登录成功")
                        return True
            
            elapsed = int(time.time() - start_time)
            if elapsed % 10 == 0:
                print(f"⏳ 已等待 {elapsed} 秒，继续检测中...")
                
        except Exception as e:
            print(f"⚠️ 检测过程出错：{str(e)[:50]}...")
        
        time.sleep(check_interval)
    
    return False

def login_xiaohongshu(driver):
    """小红书登录：扫码登录自动检测"""
    try:
        print("\n" + "="*60)
        print("📱 小红书扫码登录流程（自动检测模式）")
        print("="*60)
        print("1. 操作步骤：打开小红书APP → 扫描二维码 → 确认登录")
        print("2. 系统会自动检测登录状态，无需手动确认")
        print("3. 超时时间：180秒")
        print("="*60)
        
        driver.set_window_size(1280, 900)
        driver.get("https://www.xiaohongshu.com/explore")
        print("→ 正在加载小红书页面...")
        time.sleep(5)
        
        try:
            login_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '登录')]"))
            )
            driver.execute_script("arguments[0].click();", login_btn)
            print("→ 已自动点击登录按钮")
            time.sleep(3)
        except:
            print("→ 未找到登录按钮，尝试直接访问登录页...")
            driver.get("https://www.xiaohongshu.com/")
            time.sleep(5)
        
        try:
            qr_tab = driver.find_element(By.XPATH, "//*[contains(text(), '扫码登录') or contains(text(), '二维码') or contains(text(), 'APP扫码')]")
            driver.execute_script("arguments[0].click();", qr_tab)
            print("→ 已切换到扫码登录")
            time.sleep(2)
        except:
            print("→ 扫码登录页面已就绪")
        
        driver.execute_script("document.body.style.zoom='90%'")
        driver.execute_script("window.scrollTo(0, 0);")
        
        print("\n📱 请使用小红书APP扫描屏幕上的二维码...")
        print("="*60)
        
        if wait_for_login_success(driver, "xiaohongshu", timeout=180):
            print("✅ 小红书登录成功！即将开始爬取")
            print("="*60 + "\n")
            return True
        else:
            print("\n❌ 登录超时（180秒），未检测到登录成功")
            driver.save_screenshot("./code/xhs_login_error.png")
            print("→ 错误截图已保存：xhs_login_error.png")
            return False
    
    except Exception as e:
        print(f"\n❌ 小红书登录流程异常：{str(e)[:100]}...")
        driver.save_screenshot("./code/xhs_login_error.png")
        print("→ 错误截图已保存：xhs_login_error.png")
        return False

def login_weibo(driver):
    """微博登录：扫码登录自动检测"""
    try:
        print("\n" + "="*60)
        print("📱 微博扫码登录流程（自动检测模式）")
        print("="*60)
        print("1. 操作步骤：打开微博APP → 扫描二维码 → 确认登录")
        print("2. 系统会自动检测登录状态，无需手动确认")
        print("3. 超时时间：180秒")
        print("="*60)
        
        driver.set_window_size(1280, 900)
        driver.get("https://passport.weibo.com/sso/signin?entry=miniblog")
        print("→ 正在加载微博登录页面...")
        time.sleep(5)
        
        try:
            qr_tab = driver.find_element(By.XPATH, "//*[contains(text(), '扫码登录') or contains(@class, 'qr')]")
            driver.execute_script("arguments[0].click();", qr_tab)
            print("→ 已切换到扫码登录")
            time.sleep(2)
        except:
            print("→ 扫码登录页面已就绪")
        
        driver.execute_script("document.body.style.zoom='80%'")
        driver.execute_script("window.scrollTo(0, 0);")
        
        try:
            qr_element = driver.find_element(By.XPATH, "//img[contains(@class, 'qr') or contains(@alt, '二维码') or contains(@src, 'qr')]")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", qr_element)
            print("→ 已定位到二维码位置")
        except:
            print("→ 二维码应已在可视区域")
        
        print("\n📱 请使用微博APP扫描屏幕上的二维码...")
        print("="*60)
        
        if wait_for_login_success(driver, "weibo", timeout=180):
            print("✅ 微博登录成功！即将开始爬取")
            print("="*60 + "\n")
            return True
        else:
            print("\n❌ 登录超时（180秒），未检测到登录成功")
            driver.save_screenshot("./code/weibo_login_error.png")
            print("→ 错误截图已保存：weibo_login_error.png")
            return False
    
    except Exception as e:
        print(f"\n❌ 微博登录流程异常：{str(e)[:100]}...")
        driver.save_screenshot("./code/weibo_login_error.png")
        print("→ 错误截图已保存：weibo_login_error.png")
        return False

# 自测试功能
if __name__ == "__main__":
    print("="*50)
    print("📌 login_utils.py 自测试启动（扫码登录自动检测模式）")
    print("="*50)
    print("⚠️  测试说明：扫码登录后系统会自动检测，无需手动确认")
    print("="*50)
    
    driver = None
    test_results = []
    try:
        driver = create_chrome_driver()
        print("\n1. 测试驱动启动...✅")
        test_results.append(("驱动启动", "成功"))
        
        print("\n2. 测试小红书登录流程...")
        xhs_result = login_xiaohongshu(driver)
        test_results.append(("小红书登录流程", "成功" if xhs_result else "超时/失败"))
        
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        
        print("\n3. 测试微博登录流程...")
        weibo_result = login_weibo(driver)
        test_results.append(("微博登录流程", "成功" if weibo_result else "超时/失败"))
        
    except Exception as e:
        print(f"\n❌ 自测试全局异常：{str(e)}")
        test_results.append(("全局测试", "失败"))
    finally:
        print("\n" + "="*50)
        print("📊 自测试结果总结")
        print("="*50)
        for item, status in test_results:
            print(f"→ {item}：{status}")
        if driver:
            driver.quit()
        print("\n✅ 自测试结束！")