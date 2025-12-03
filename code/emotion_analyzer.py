"""
情绪分析模块
- 文本情绪分析：使用DeepSeek API
- 图片情绪分析：使用FER库（需本地运行）
"""

import requests
import json
import re
import os
from tenacity import retry, stop_after_attempt, wait_exponential
from config import EMOTION_CONFIG

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def analyze_text_emotion(text):
    """
    使用DeepSeek API分析文本情绪
    返回: {"emotions": {...}, "main_emotion": "...", "secondary_emotion": "..."}
    """
    if not text or text == "无文本内容":
        return None
    
    text = re.sub(r'\s+', ' ', text).strip()
    text = text[:2000]
    
    headers = {
        "Authorization": f"Bearer {EMOTION_CONFIG['deepseek_api_key']}",
        "Content-Type": "application/json"
    }

    messages = [
        {
            "role": "system",
            "content": (
                "你是专业的文本情绪分析专家，需精准识别文本中的七种情绪：喜、怒、哀、惧、惊、厌、中性。\n"
                "要求：\n"
                "1. 识别反讽、讽刺、含蓄表达的真实情绪；\n"
                "2. 对混合情绪需区分主次，评分反映情绪强度（0-100整数）；\n"
                "3. 严格按JSON返回，无额外内容：\n"
                "{\"emotions\": {\"喜\": 评分, \"怒\": 评分, \"哀\": 评分, \"惧\": 评分, \"惊\": 评分, \"厌\": 评分, \"中性\": 评分}, \"main_emotion\": \"主情绪\", \"secondary_emotion\": \"次要情绪\"}\n"
                "4. 次要情绪为评分第二高的情绪（若有并列，选最贴合的）。"
            )
        },
        {
            "role": "user",
            "content": f"分析文本的情绪（含反讽/含蓄/混合情绪）：{text}"
        }
    ]

    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 300
    }

    try:
        response = requests.post(
            EMOTION_CONFIG["deepseek_api_url"],
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()
        
        if not content.startswith("{") or not content.endswith("}"):
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group()
            else:
                raise ValueError("返回内容非JSON格式")
        
        emotion_data = json.loads(content)
        return emotion_data
    except Exception as e:
        print(f"文本情绪分析失败：{str(e)[:50]}")
        raise e


def analyze_image_emotion_local(image_path):
    """
    使用FER库分析图片中人脸的情绪（需要本地运行，需安装fer和tensorflow）
    返回: {"emotions": {...}, "main_emotion": "..."}
    """
    try:
        from fer import FER
        import cv2
    except ImportError:
        return {
            "error": "需要安装fer和tensorflow库",
            "install_cmd": "pip install fer opencv-python tensorflow",
            "run_local": True
        }
    
    if not os.path.exists(image_path):
        return {"error": f"图片不存在: {image_path}"}
    
    detector = FER(mtcnn=True)
    image = cv2.imread(image_path)
    
    if image is None:
        return {"error": "无法读取图片"}
    
    results = detector.detect_emotions(image)
    
    if not results:
        return {"error": "未检测到人脸", "face_count": 0}
    
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


def batch_analyze_texts(text_list, show_progress=True):
    """
    批量分析文本情绪
    """
    results = []
    total = len(text_list)
    
    for idx, item in enumerate(text_list, 1):
        if show_progress:
            print(f"分析文本进度: {idx}/{total}")
        
        text = item.get("content", "") if isinstance(item, dict) else item
        
        try:
            emotion_result = analyze_text_emotion(text)
            if isinstance(item, dict):
                item["emotion_analysis"] = emotion_result
                results.append(item)
            else:
                results.append({
                    "text": text,
                    "emotion_analysis": emotion_result
                })
        except Exception as e:
            if isinstance(item, dict):
                item["emotion_analysis"] = {"error": str(e)}
                results.append(item)
            else:
                results.append({
                    "text": text,
                    "emotion_analysis": {"error": str(e)}
                })
    
    return results


def batch_analyze_images(image_paths, show_progress=True):
    """
    批量分析图片情绪（需本地运行）
    """
    results = []
    total = len(image_paths)
    
    for idx, path in enumerate(image_paths, 1):
        if show_progress:
            print(f"分析图片进度: {idx}/{total}")
        
        emotion_result = analyze_image_emotion_local(path)
        results.append({
            "image_path": path,
            "emotion_analysis": emotion_result
        })
    
    return results


def get_emotion_statistics(analyzed_data):
    """
    统计情绪分布
    """
    emotion_counts = {e: 0 for e in EMOTION_CONFIG["emotions"]}
    total = 0
    
    for item in analyzed_data:
        analysis = item.get("emotion_analysis", {})
        main_emotion = analysis.get("main_emotion")
        if main_emotion and main_emotion in emotion_counts:
            emotion_counts[main_emotion] += 1
            total += 1
    
    stats = {
        "total_analyzed": total,
        "emotion_counts": emotion_counts,
        "emotion_percentages": {
            e: round(c / total * 100, 2) if total > 0 else 0 
            for e, c in emotion_counts.items()
        }
    }
    
    return stats


if __name__ == "__main__":
    print("=== 情绪分析模块测试 ===\n")
    
    test_texts = [
        "今天天气真好，心情很愉快！",
        "这个服务太差了，让人很生气",
        "想念去世的奶奶，眼泪止不住地流",
    ]
    
    print("测试文本情绪分析...")
    for text in test_texts:
        print(f"\n文本: {text}")
        try:
            result = analyze_text_emotion(text)
            print(f"主情绪: {result['main_emotion']}")
            print(f"情绪评分: {result['emotions']}")
        except Exception as e:
            print(f"分析失败: {e}")
