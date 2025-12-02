"""
人脸表情识别测试
使用FER库（基于TensorFlow/Keras）进行7种情绪识别

依赖安装（本地运行）：
pip install fer opencv-python tensorflow

使用方法：
python tese_opencv.py [图片路径]
"""

import sys
import os

try:
    from fer import FER
    import cv2
except ImportError as e:
    print("=" * 50)
    print("缺少必要依赖，请在本地安装：")
    print("pip install fer opencv-python tensorflow")
    print("=" * 50)
    print(f"详细错误：{e}")
    sys.exit(1)

def analyze_face_emotion(image_path):
    """分析图片中人脸的表情情绪"""
    
    if not os.path.exists(image_path):
        print(f"错误：图片文件不存在 - {image_path}")
        return None
    
    print(f"正在分析图片：{image_path}")
    
    detector = FER(mtcnn=True)
    
    image = cv2.imread(image_path)
    if image is None:
        print("错误：无法读取图片文件")
        return None
    
    emotion_results = detector.detect_emotions(image)
    print("细分情绪结果：", emotion_results)
    
    if emotion_results:
        for idx, face in enumerate(emotion_results):
            print(f"\n--- 人脸 {idx + 1} ---")
            face_emotions = face["emotions"]
            print("喜（happy）：{:.2f}%".format(face_emotions["happy"] * 100))
            print("怒（angry）：{:.2f}%".format(face_emotions["angry"] * 100))
            print("哀（sad）：{:.2f}%".format(face_emotions["sad"] * 100))
            print("惧（fear）：{:.2f}%".format(face_emotions["fear"] * 100))
            print("惊（surprise）：{:.2f}%".format(face_emotions["surprise"] * 100))
            print("厌（disgust）：{:.2f}%".format(face_emotions["disgust"] * 100))
            print("中性（neutral）：{:.2f}%".format(face_emotions["neutral"] * 100))
            
            dominant = max(face_emotions, key=face_emotions.get)
            print(f"→ 主导情绪：{dominant}")
    else:
        print("未检测到人脸")
    
    return emotion_results

if __name__ == "__main__":
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = "./test_face.jpg"
        print(f"未指定图片路径，使用默认路径：{image_path}")
        print("使用方法：python tese_opencv.py <图片路径>")
    
    analyze_face_emotion(image_path)