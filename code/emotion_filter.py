"""
情绪筛选模块
- 文本：分析情绪 → 判断是否包含目标情绪
- 图片：检测人脸/身体 → 分析情绪 → 判断是否包含目标情绪
"""

import requests
import json
import re
from config import EMOTION_CONFIG

def analyze_text_emotion(text):
    """
    分析单条文本的情绪
    返回: {"emotions": {...}, "dominant": "喜", "should_save": True/False}
    """
    if not text or len(text.strip()) < 5:
        return None
    
    api_key = EMOTION_CONFIG["deepseek_api_key"]
    if not api_key:
        print("⚠️ DeepSeek API未配置，跳过情绪分析")
        return None
    
    emotions = EMOTION_CONFIG["emotions"]
    prompt = f"""分析以下文本的情绪，返回JSON格式的情绪评分（0-1之间）。
情绪类别：{', '.join(emotions)}

文本：{text[:500]}

请直接返回JSON，格式如下：
{{"喜": 0.1, "怒": 0.0, "哀": 0.0, "惧": 0.0, "惊": 0.0, "厌": 0.0, "中性": 0.9}}"""

    try:
        response = requests.post(
            EMOTION_CONFIG["deepseek_api_url"],
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 200
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            json_match = re.search(r'\{[^{}]+\}', content)
            if json_match:
                emotion_scores = json.loads(json_match.group())
                
                dominant = max(emotion_scores, key=emotion_scores.get)
                max_score = emotion_scores[dominant]
                
                target_emotions = EMOTION_CONFIG["target_emotions"]
                min_score = EMOTION_CONFIG["min_score"]
                
                should_save = False
                for emotion in target_emotions:
                    if emotion in emotion_scores and emotion_scores[emotion] >= min_score:
                        should_save = True
                        break
                
                return {
                    "emotions": emotion_scores,
                    "dominant": dominant,
                    "max_score": max_score,
                    "should_save": should_save
                }
        
        return None
        
    except Exception as e:
        print(f"文本情绪分析失败: {str(e)[:50]}")
        return None


def check_has_person(image_path_or_url):
    """
    检测图片中是否有人脸或人体
    注意：此函数需要在本地运行（需要opencv和fer库）
    在Replit上返回None，表示无法检测
    """
    try:
        import cv2
        import numpy as np
        
        if image_path_or_url.startswith("http"):
            resp = requests.get(image_path_or_url, timeout=10)
            img_array = np.frombuffer(resp.content, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        else:
            img = cv2.imread(image_path_or_url)
        
        if img is None:
            return False
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            return True
        
        body_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_fullbody.xml'
        )
        bodies = body_cascade.detectMultiScale(gray, 1.1, 4)
        
        return len(bodies) > 0
        
    except ImportError:
        return None
    except Exception as e:
        print(f"人体检测失败: {str(e)[:30]}")
        return None


def analyze_image_emotion(image_path_or_url):
    """
    分析图片中人脸的情绪
    注意：此函数需要在本地运行（需要fer库）
    返回: {"emotions": {...}, "dominant": "happy", "should_save": True/False}
    """
    try:
        from fer import FER
        import cv2
        import numpy as np
        
        if image_path_or_url.startswith("http"):
            resp = requests.get(image_path_or_url, timeout=10)
            img_array = np.frombuffer(resp.content, np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        else:
            img = cv2.imread(image_path_or_url)
        
        if img is None:
            return None
        
        detector = FER(mtcnn=True)
        result = detector.detect_emotions(img)
        
        if not result:
            return None
        
        emotions = result[0]["emotions"]
        dominant = max(emotions, key=emotions.get)
        max_score = emotions[dominant]
        
        emotion_map = {
            "happy": "喜",
            "angry": "怒",
            "sad": "哀",
            "fear": "惧",
            "surprise": "惊",
            "disgust": "厌",
            "neutral": "中性"
        }
        
        target_emotions = EMOTION_CONFIG["target_emotions"]
        min_score = EMOTION_CONFIG["min_score"]
        
        should_save = False
        for en_emotion, cn_emotion in emotion_map.items():
            if cn_emotion in target_emotions and emotions.get(en_emotion, 0) >= min_score:
                should_save = True
                break
        
        return {
            "emotions": emotions,
            "dominant": dominant,
            "dominant_cn": emotion_map.get(dominant, dominant),
            "max_score": max_score,
            "should_save": should_save
        }
        
    except ImportError:
        return None
    except Exception as e:
        print(f"图片情绪分析失败: {str(e)[:30]}")
        return None


def filter_text(text, content_id=None):
    """
    筛选文本：分析情绪，判断是否需要保存
    返回: (should_save, emotion_data) 或 (False, None)
    """
    result = analyze_text_emotion(text)
    
    if result is None:
        return False, None
    
    if result["should_save"]:
        return True, result
    
    return False, result


def filter_image(image_path_or_url):
    """
    筛选图片：检测人体 → 分析情绪 → 判断是否需要保存
    返回: (should_save, emotion_data) 或 (False, None)
    注意：此函数需要在本地运行
    """
    has_person = check_has_person(image_path_or_url)
    
    if has_person is None:
        return None, {"status": "需要本地运行"}
    
    if not has_person:
        return False, {"status": "无人脸/人体"}
    
    result = analyze_image_emotion(image_path_or_url)
    
    if result is None:
        return False, {"status": "情绪分析失败"}
    
    if result["should_save"]:
        return True, result
    
    return False, result
