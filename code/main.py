"""
小红书/微博爬虫 + 情绪分析主程序
功能：爬取帖子 → 保存文本/图片 → 情绪分析 → 带标签存储
"""

from login_utils import create_chrome_driver, login_xiaohongshu, login_weibo
from crawler_utils import crawl_xiaohongshu, crawl_weibo
from save_utils import save_text_data, save_analyzed_data, save_statistics
from emotion_analyzer import batch_analyze_texts, get_emotion_statistics
from config import CRAWL_CONFIG, EMOTION_CONFIG
import time
import argparse

def main(target_texts=None, target_images=None, analyze_emotion=True, platforms=None):
    """
    主程序入口
    :param target_texts: 目标文本条数（None则使用配置文件默认值）
    :param target_images: 目标图片数量
    :param analyze_emotion: 是否进行情绪分析
    :param platforms: 要爬取的平台列表 ["xiaohongshu", "weibo"]
    """
    
    target_texts = target_texts or CRAWL_CONFIG["target_texts"]
    target_images = target_images or CRAWL_CONFIG["target_images"]
    platforms = platforms or ["xiaohongshu", "weibo"]
    
    print("=" * 60)
    print("🚀 社交媒体爬虫 + 情绪分析系统启动")
    print("=" * 60)
    print(f"目标文本数量：{target_texts} 条")
    print(f"目标图片数量：{target_images} 张")
    print(f"情绪分析：{'开启' if analyze_emotion else '关闭'}")
    print(f"目标平台：{', '.join(platforms)}")
    print("=" * 60)
    
    driver = create_chrome_driver()
    driver.implicitly_wait(10)
    print("✅ 浏览器驱动创建成功")
    
    all_text_data = []
    all_image_data = []
    
    try:
        if "xiaohongshu" in platforms:
            print("\n" + "=" * 60)
            print("📱 开始小红书流程（登录→爬取）")
            print("=" * 60)
            
            login_success = login_xiaohongshu(driver)
            if login_success:
                print("🚀 小红书登录完成，开始爬取...")
                xhs_text_data, xhs_image_data = crawl_xiaohongshu(driver, target_count=target_texts)
                
                save_text_data("xiaohongshu", xhs_text_data)
                all_text_data.extend(xhs_text_data)
                all_image_data.extend(xhs_image_data)
                
                print(f"✅ 小红书爬取完成！文本 {len(xhs_text_data)} 条，图片 {len(xhs_image_data)} 张")
            else:
                print("❌ 小红书登录失败，跳过")
        
        if "weibo" in platforms:
            print("\n" + "=" * 60)
            print("📱 开始微博流程（打开标签页→登录→爬取）")
            print("=" * 60)
            
            if "xiaohongshu" in platforms:
                print("🔄 打开微博专属标签页...")
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(1)
            
            weibo_login_success = login_weibo(driver)
            if weibo_login_success:
                print("🚀 微博登录完成，开始爬取...")
                weibo_text_data, weibo_image_data = crawl_weibo(driver, target_count=target_texts)
                
                save_text_data("weibo", weibo_text_data)
                all_text_data.extend(weibo_text_data)
                all_image_data.extend(weibo_image_data)
                
                print(f"✅ 微博爬取完成！文本 {len(weibo_text_data)} 条，图片 {len(weibo_image_data)} 张")
            else:
                print("❌ 微博登录失败，跳过")
        
        print("\n" + "=" * 60)
        print("📊 爬取汇总")
        print("=" * 60)
        print(f"总计文本：{len(all_text_data)} 条")
        print(f"总计图片：{len(all_image_data)} 张")
        
        if analyze_emotion and EMOTION_CONFIG["analyze_text"] and all_text_data:
            print("\n" + "=" * 60)
            print("🧠 开始文本情绪分析...")
            print("=" * 60)
            
            analyzed_texts = batch_analyze_texts(all_text_data, show_progress=True)
            
            save_analyzed_data(analyzed_texts, "texts_with_emotion")
            
            stats = get_emotion_statistics(analyzed_texts)
            save_statistics(stats, "text")
            
            print("\n📊 情绪分布统计：")
            for emotion, count in stats["emotion_counts"].items():
                pct = stats["emotion_percentages"][emotion]
                print(f"  {emotion}: {count} 条 ({pct}%)")
        
        print("\n" + "=" * 60)
        print("🎉 所有流程执行完成！")
        print("=" * 60)
        print("数据保存位置：")
        print("  - 原始文本：./data/texts/")
        print("  - 原始图片：./data/images/")
        print("  - 分析结果：./data/analyzed/")
        print("=" * 60)
        
        if EMOTION_CONFIG["analyze_image"]:
            print("\n💡 提示：图片情绪分析需要在本地运行")
            print("   请将代码同步到本地后运行：")
            print("   python analyze_images_local.py")
        
    except Exception as e:
        print(f"\n❌ 程序执行异常：{str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        input("\n按回车键关闭浏览器...")
        driver.quit()


def run_text_analysis_only():
    """仅运行文本情绪分析（不启动爬虫）"""
    import os
    import json
    
    print("=" * 60)
    print("🧠 文本情绪分析模式（分析已有数据）")
    print("=" * 60)
    
    text_dir = "./data/texts"
    all_texts = []
    
    for platform in ["xiaohongshu", "weibo"]:
        platform_dir = os.path.join(text_dir, platform)
        if not os.path.exists(platform_dir):
            continue
        
        for filename in os.listdir(platform_dir):
            if filename.endswith(".json") and "带情绪标签" not in filename:
                filepath = os.path.join(platform_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    all_texts.extend(data)
    
    if not all_texts:
        print("❌ 未找到待分析的文本数据")
        return
    
    print(f"找到 {len(all_texts)} 条待分析文本")
    
    analyzed_texts = batch_analyze_texts(all_texts, show_progress=True)
    save_analyzed_data(analyzed_texts, "texts_with_emotion")
    
    stats = get_emotion_statistics(analyzed_texts)
    save_statistics(stats, "text")
    
    print("\n📊 情绪分布统计：")
    for emotion, count in stats["emotion_counts"].items():
        pct = stats["emotion_percentages"][emotion]
        print(f"  {emotion}: {count} 条 ({pct}%)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="社交媒体爬虫 + 情绪分析")
    parser.add_argument("--texts", type=int, default=None, help="目标文本条数")
    parser.add_argument("--images", type=int, default=None, help="目标图片数量")
    parser.add_argument("--no-emotion", action="store_true", help="不进行情绪分析")
    parser.add_argument("--weibo-only", action="store_true", help="只爬取微博")
    parser.add_argument("--xhs-only", action="store_true", help="只爬取小红书")
    parser.add_argument("--analyze-only", action="store_true", help="仅分析已有数据")
    
    args = parser.parse_args()
    
    if args.analyze_only:
        run_text_analysis_only()
    else:
        platforms = None
        if args.weibo_only:
            platforms = ["weibo"]
        elif args.xhs_only:
            platforms = ["xiaohongshu"]
        
        main(
            target_texts=args.texts,
            target_images=args.images,
            analyze_emotion=not args.no_emotion,
            platforms=platforms
        )
