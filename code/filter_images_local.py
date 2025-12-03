"""
本地图片情绪筛选脚本
流程：检测人脸/身体 → 分析情绪 → 符合条件才移动到filtered目录

运行方式：python filter_images_local.py
需要安装：pip install fer opencv-python tensorflow
"""

import os
import json
import shutil
from datetime import datetime

try:
    import cv2
    from fer import FER
    import numpy as np
except ImportError:
    print("❌ 请先安装依赖：pip install fer opencv-python tensorflow")
    exit(1)


EMOTIONS_CN = {
    "happy": "喜",
    "angry": "怒", 
    "sad": "哀",
    "fear": "惧",
    "surprise": "惊",
    "disgust": "厌",
    "neutral": "中性"
}

TARGET_EMOTIONS = ["喜", "怒", "哀", "惧", "惊", "厌"]
MIN_SCORE = 0.3


def check_has_person(img):
    """检测图片中是否有人脸或人体"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    if len(faces) > 0:
        return True, "face"
    
    body_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_fullbody.xml'
    )
    bodies = body_cascade.detectMultiScale(gray, 1.1, 4)
    
    if len(bodies) > 0:
        return True, "body"
    
    return False, None


def analyze_emotion(img, detector):
    """分析图片中人脸的情绪"""
    result = detector.detect_emotions(img)
    
    if not result:
        return None
    
    emotions = result[0]["emotions"]
    dominant = max(emotions, key=emotions.get)
    max_score = emotions[dominant]
    
    should_save = False
    for en_emotion, cn_emotion in EMOTIONS_CN.items():
        if cn_emotion in TARGET_EMOTIONS and emotions.get(en_emotion, 0) >= MIN_SCORE:
            should_save = True
            break
    
    return {
        "emotions": emotions,
        "dominant": dominant,
        "dominant_cn": EMOTIONS_CN.get(dominant, dominant),
        "max_score": max_score,
        "should_save": should_save
    }


def filter_images(platform):
    """筛选指定平台的待处理图片"""
    pending_dir = f"./data/images/{platform}/pending"
    filtered_dir = f"./data/images/{platform}/filtered"
    rejected_dir = f"./data/images/{platform}/rejected"
    
    if not os.path.exists(pending_dir):
        print(f"⚠️ 未找到待处理目录: {pending_dir}")
        return
    
    os.makedirs(filtered_dir, exist_ok=True)
    os.makedirs(rejected_dir, exist_ok=True)
    
    image_files = [f for f in os.listdir(pending_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print(f"⚠️ {platform} 无待处理图片")
        return
    
    print(f"\n处理 {platform} 图片：共 {len(image_files)} 张")
    print("-" * 40)
    
    detector = FER(mtcnn=True)
    
    stats = {
        "total": len(image_files),
        "has_person": 0,
        "filtered": 0,
        "rejected_no_person": 0,
        "rejected_no_emotion": 0,
        "failed": 0
    }
    
    results = []
    
    for i, filename in enumerate(image_files, 1):
        filepath = os.path.join(pending_dir, filename)
        print(f"[{i}/{len(image_files)}] {filename}...", end=" ")
        
        try:
            img = cv2.imread(filepath)
            if img is None:
                print("读取失败")
                stats["failed"] += 1
                continue
            
            has_person, person_type = check_has_person(img)
            
            if not has_person:
                print("无人脸/人体 → 跳过")
                shutil.move(filepath, os.path.join(rejected_dir, filename))
                stats["rejected_no_person"] += 1
                continue
            
            stats["has_person"] += 1
            
            emotion_data = analyze_emotion(img, detector)
            
            if emotion_data is None:
                print("情绪分析失败 → 跳过")
                shutil.move(filepath, os.path.join(rejected_dir, filename))
                stats["rejected_no_emotion"] += 1
                continue
            
            if emotion_data["should_save"]:
                print(f"✓ {emotion_data['dominant_cn']}({emotion_data['max_score']:.2f}) → 保存")
                shutil.move(filepath, os.path.join(filtered_dir, filename))
                stats["filtered"] += 1
                
                results.append({
                    "filename": filename,
                    "emotion": emotion_data["dominant_cn"],
                    "score": emotion_data["max_score"],
                    "all_emotions": {EMOTIONS_CN.get(k, k): v for k, v in emotion_data["emotions"].items()}
                })
            else:
                print(f"✗ {emotion_data['dominant_cn']}({emotion_data['max_score']:.2f}) → 不符合")
                shutil.move(filepath, os.path.join(rejected_dir, filename))
                stats["rejected_no_emotion"] += 1
                
        except Exception as e:
            print(f"错误: {str(e)[:30]}")
            stats["failed"] += 1
    
    print("\n" + "=" * 40)
    print(f"{platform} 处理完成！")
    print(f"  总计：{stats['total']}")
    print(f"  有人脸/人体：{stats['has_person']}")
    print(f"  通过筛选：{stats['filtered']}")
    print(f"  无人脸/人体：{stats['rejected_no_person']}")
    print(f"  情绪不符：{stats['rejected_no_emotion']}")
    print(f"  处理失败：{stats['failed']}")
    
    if results:
        result_file = os.path.join(filtered_dir, f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n分析结果已保存: {result_file}")
    
    return stats


def main():
    print("=" * 60)
    print("🖼️ 本地图片情绪筛选")
    print("=" * 60)
    print(f"目标情绪：{', '.join(TARGET_EMOTIONS)}")
    print(f"最低分数：{MIN_SCORE}")
    print("=" * 60)
    
    all_stats = {}
    
    for platform in ["xiaohongshu", "weibo"]:
        stats = filter_images(platform)
        if stats:
            all_stats[platform] = stats
    
    print("\n" + "=" * 60)
    print("📊 总计")
    print("=" * 60)
    total_filtered = sum(s.get("filtered", 0) for s in all_stats.values())
    total_checked = sum(s.get("total", 0) for s in all_stats.values())
    print(f"检查图片：{total_checked} 张")
    print(f"通过筛选：{total_filtered} 张")
    print("=" * 60)


if __name__ == "__main__":
    main()
