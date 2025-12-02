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
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    
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

def user_confirm(timeout=60):
    """用户手动确认函数（超时60秒，输入指定指令视为确认）"""
    confirm_result = [False]  # 用列表实现多线程修改
    
    def input_thread():
        """输入线程：等待用户输入"""
        user_input = input("\n👉 登录成功后按's'回车确认（超时自动失败）：")
        if user_input.strip().lower() == "s":
            confirm_result[0] = True
    
    # 启动输入线程
    thread = threading.Thread(target=input_thread)
    thread.daemon = True  # 主线程退出时，输入线程也退出
    thread.start()
    
    # 主线程倒计时等待
    for i in range(timeout, 0, -1):
        if confirm_result[0]:
            return True
        time.sleep(1)
    
    print("\n")
    return False

def login_xiaohongshu(driver):
    """小红书登录：用户手动反馈法（用户确认后才继续）"""
    try:
        print("\n" + "="*60)
        print("📱 小红书手动登录流程（用户确认模式）")
        print("="*60)
        print(f"1. 目标手机号：{XHS_CONFIG['phone']}（请手动输入）")
        print("2. 操作步骤：点击登录 → 输入手机号 → 滑块验证 → 验证码登录")
        print("3. 登录成功后，回到命令行输入 'success' 并回车（大小写不敏感）")
        print("4. 超时时间：60秒（未输入则视为登录失败）")
        print("="*60)
        
        # 打开小红书登录入口
        driver.get("https://www.xiaohongshu.com/")
        time.sleep(2)
        
        # 自动点击登录按钮（帮用户省一步）
        try:
            login_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '登录')]"))
            )
            driver.execute_script("arguments[0].click();", login_btn)
            print("→ 已自动点击登录按钮，跳转至登录页（请继续手动操作）")
        except:
            print("→ 未找到登录按钮，请手动点击页面上的「登录」字样")
        
        # 核心：等待用户手动确认
        print("\n📌 提示：登录成功后（页面显示个人主页/发现页），立即在命令行输入 'success' 确认")
        if user_confirm(timeout=60):
            print("✅ 收到用户确认！小红书登录成功，即将开始爬取")
            print("="*60 + "\n")
            return True
        else:
            print("\n❌ 超时未收到用户确认（60秒），视为登录失败")
            driver.save_screenshot("./xhs_login_error.png")
            print("→ 错误截图已保存：xhs_login_error.png")
            return False
    
    except Exception as e:
        print(f"\n❌ 小红书登录流程异常：{str(e)[:100]}...")
        driver.save_screenshot("./xhs_login_error.png")
        print("→ 错误截图已保存：xhs_login_error.png")
        return False

def login_weibo(driver):
    """微博登录：用户手动反馈法（用户确认后才继续）"""
    try:
        print("\n" + "="*60)
        print("📱 微博手动登录流程（用户确认模式）")
        print("="*60)
        print(f"1. 目标手机号：{WEIBO_CONFIG['phone']}（请手动输入）")
        print("2. 操作步骤：输入手机号 → 滑块验证 → 验证码登录")
        print("3. 登录成功后，回到命令行输入 'success' 并回车（大小写不敏感）")
        print("4. 超时时间：60秒（未输入则视为登录失败）")
        print("="*60)
        
        # 打开微博登录页
        driver.get("https://passport.weibo.com/sso/signin?entry=miniblog")
        time.sleep(2)
        
        # 核心：等待用户手动确认
        print("\n📌 提示：登录成功后（页面显示微博首页/个人主页），立即在命令行输入 'success' 确认")
        if user_confirm(timeout=60):
            print("✅ 收到用户确认！微博登录成功，即将开始爬取")
            print("="*60 + "\n")
            return True
        else:
            print("\n❌ 超时未收到用户确认（60秒），视为登录失败")
            driver.save_screenshot("./weibo_login_error.png")
            print("→ 错误截图已保存：weibo_login_error.png")
            return False
    
    except Exception as e:
        print(f"\n❌ 微博登录流程异常：{str(e)[:100]}...")
        driver.save_screenshot("./weibo_login_error.png")
        print("→ 错误截图已保存：weibo_login_error.png")
        return False

# 自测试功能（保持不变）
if __name__ == "__main__":
    print("="*50)
    print("📌 login_utils.py 自测试启动（用户确认模式）")
    print("="*50)
    print("⚠️  测试说明：输入 'success' 可模拟确认，等待60秒可模拟超时")
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