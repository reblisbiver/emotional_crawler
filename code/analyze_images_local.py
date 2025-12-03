"""
本地图片情绪分析脚本
需要安装: pip install fer opencv-python tensorflow

使用方法：
python analyze_images_local.py
"""

import os
import json
import sys
import time

try:
    from fer import FER
    import cv2
except ImportError:
    print("=" * 60)
    print("缺少必要依赖，请安装：")
    print("pip install fer opencv-python tensorflow")
    print("=" * 60)
    sys.exit(1)

from config import SAVE_CONFIG, EMOTION_CONFIG


def analyze_single_image(image_path, detector):
    """分析单张图片的情绪"""
    
    if not os.path.exists(image_path):
        return {"error": f"图片不存在: {image_path}"}
    
    image = cv2.imread(image_path)
    if image is None:
        return {"error": "无法读取图片"}
    
    results = detector.detect_emotions(image)
    
    if not results:
        return {"face_count": 0, "faces": [], "main_emotion": None}
    
    emotions_cn = {
        "happy": "喜",
        "angry": "怒",
        "sad": "哀",
        "fear": "惧",
        "surprise": "惊",
        "disgust": "厌",
        "neutral": "中性"
    }
    
    all_faces = []
    for idx, face in enumerate(results):
        face_emotions = face["emotions"]
        emotions_cn_scores = {
            emotions_cn[k]: int(v * 100) for k, v in face_emotions.items()
        }
        main_emotion = emotions_cn[max(face_emotions, key=face_emotions.get)]
        
        all_faces.append({
            "face_id": idx + 1,
            "box": face["box"],
            "emotions": emotions_cn_scores,
            "main_emotion": main_emotion
        })
    
    return {
        "face_count": len(results),
        "faces": all_faces,
        "main_emotion": all_faces[0]["main_emotion"] if all_faces else None
    }


def get_all_images(base_path="./data/images"):
    """获取所有已保存的图片路径"""
    image_paths = []
    
    if not os.path.exists(base_path):
        return image_paths
    
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                image_paths.append(os.path.join(root, file))
    
    return image_paths


def batch_analyze_images(image_paths, show_progress=True):
    """批量分析图片情绪"""
    
    print("正在初始化FER检测器...")
    detector = FER(mtcnn=True)
    
    results = []
    total = len(image_paths)
    face_found = 0
    
    for idx, path in enumerate(image_paths, 1):
        if show_progress and idx % 10 == 0:
            print(f"分析进度: {idx}/{total} ({idx*100//total}%)")
        
        analysis = analyze_single_image(path, detector)
        
        if analysis.get("face_count", 0) > 0:
            face_found += 1
        
        results.append({
            "image_path": path,
            "emotion_analysis": analysis
        })
    
    print(f"\n分析完成：{total} 张图片，{face_found} 张检测到人脸")
    return results


def get_emotion_statistics(analyzed_data):
    """统计情绪分布"""
    emotion_counts = {e: 0 for e in EMOTION_CONFIG["emotions"]}
    total_faces = 0
    
    for item in analyzed_data:
        analysis = item.get("emotion_analysis", {})
        faces = analysis.get("faces", [])
        
        for face in faces:
            main_emotion = face.get("main_emotion")
            if main_emotion and main_emotion in emotion_counts:
                emotion_counts[main_emotion] += 1
                total_faces += 1
    
    stats = {
        "total_images": len(analyzed_data),
        "total_faces": total_faces,
        "emotion_counts": emotion_counts,
        "emotion_percentages": {
            e: round(c / total_faces * 100, 2) if total_faces > 0 else 0
            for e, c in emotion_counts.items()
        }
    }
    
    return stats


def save_results(results, stats, output_dir="./data/analyzed"):
    """保存分析结果"""
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = int(time.time())
    
    results_file = os.path.join(output_dir, f"images_with_emotion_{timestamp}.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"✅ 分析结果已保存：{results_file}")
    
    stats_file = os.path.join(output_dir, f"image_stats_{timestamp}.json")
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"✅ 统计数据已保存：{stats_file}")
    
    return results_file, stats_file


def main():
    print("=" * 60)
    print("🖼️ 本地图片情绪分析程序")
    print("=" * 60)
    
    image_paths = get_all_images()
    
    if not image_paths:
        print("❌ 未找到待分析的图片")
        print("请确保 ./data/images/ 目录下有图片文件")
        return
    
    print(f"找到 {len(image_paths)} 张图片")
    
    results = batch_analyze_images(image_paths, show_progress=True)
    
    stats = get_emotion_statistics(results)
    
    print("\n" + "=" * 60)
    print("📊 情绪分布统计")
    print("=" * 60)
    print(f"总图片数：{stats['total_images']}")
    print(f"检测到人脸：{stats['total_faces']} 个")
    print("\n情绪分布：")
    for emotion, count in stats["emotion_counts"].items():
        pct = stats["emotion_percentages"][emotion]
        bar = "█" * int(pct / 5) if pct > 0 else ""
        print(f"  {emotion}: {count:4d} ({pct:5.1f}%) {bar}")
    
    save_results(results, stats)
    
    print("\n" + "=" * 60)
    print("🎉 图片情绪分析完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
