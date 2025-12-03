"""
社交媒体爬虫 + 情绪筛选系统
流程：爬取内容 → 情绪分析 → 符合条件才存储
"""

from login_utils import create_chrome_driver, login_xiaohongshu, login_weibo
from crawler_utils import crawl_xiaohongshu, crawl_weibo
from config import CRAWL_CONFIG, EMOTION_CONFIG
import argparse
import time


def main(target_texts=None, target_images=None, platforms=None):
    """
    主程序入口
    """
    target_texts = target_texts or CRAWL_CONFIG["target_texts"]
    target_images = target_images or CRAWL_CONFIG["target_images"]
    platforms = platforms or ["weibo"]
    
    print("=" * 60)
    print("🚀 社交媒体爬虫 + 情绪筛选系统")
    print("=" * 60)
    print(f"目标文本：{target_texts} 条（带情绪标签）")
    print(f"目标图片：{target_images} 张（待本地分析）")
    print(f"目标平台：{', '.join(platforms)}")
    print(f"筛选情绪：{', '.join(EMOTION_CONFIG['target_emotions'])}")
    print(f"最低分数：{EMOTION_CONFIG['min_score']}")
    print("=" * 60)
    
    driver = create_chrome_driver()
    driver.implicitly_wait(10)
    print("✅ 浏览器启动成功")
    
    total_stats = {"total_checked": 0, "texts_saved": 0, "images_downloaded": 0}
    
    try:
        if "xiaohongshu" in platforms:
            print("\n" + "=" * 60)
            print("📱 小红书流程")
            print("=" * 60)
            
            if login_xiaohongshu(driver):
                stats = crawl_xiaohongshu(driver, target_texts, target_images)
                for k, v in stats.items():
                    total_stats[k] += v
            else:
                print("❌ 小红书登录失败")
        
        if "weibo" in platforms:
            print("\n" + "=" * 60)
            print("📱 微博流程")
            print("=" * 60)
            
            if len(platforms) > 1:
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[-1])
            
            if login_weibo(driver):
                stats = crawl_weibo(driver, target_texts, target_images)
                for k, v in stats.items():
                    total_stats[k] += v
            else:
                print("❌ 微博登录失败")
        
        print("\n" + "=" * 60)
        print("📊 最终统计")
        print("=" * 60)
        print(f"检查总数：{total_stats['total_checked']} 条")
        print(f"保存文本：{total_stats['texts_saved']} 条（已完成情绪分析）")
        print(f"下载图片：{total_stats['images_downloaded']} 张（待本地分析）")
        print("=" * 60)
        print("数据位置：")
        print("  - 筛选文本：./data/texts/<平台>/filtered_*.json")
        print("  - 待分析图片：./data/images/<平台>/pending/")
        print("=" * 60)
        
        if total_stats["images_downloaded"] > 0:
            print("\n💡 图片情绪筛选需要在本地运行：")
            print("   python filter_images_local.py")
        
    except Exception as e:
        print(f"\n❌ 异常：{str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        input("\n按回车键关闭浏览器...")
        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="社交媒体爬虫 + 情绪筛选")
    parser.add_argument("--texts", type=int, default=None, help="目标文本条数")
    parser.add_argument("--images", type=int, default=None, help="目标图片数量")
    parser.add_argument("--weibo-only", action="store_true", help="只爬取微博")
    parser.add_argument("--xhs-only", action="store_true", help="只爬取小红书")
    
    args = parser.parse_args()
    
    platforms = None
    if args.weibo_only:
        platforms = ["weibo"]
    elif args.xhs_only:
        platforms = ["xiaohongshu"]
    
    main(
        target_texts=args.texts,
        target_images=args.images,
        platforms=platforms
    )
