from fer.fer import FER
import cv2

# 初始化检测器
detector = FER()

# 加载图片
image = cv2.imread(r"D:\HuaweiMoveData\Users\HUAWEI\Desktop\1.jpg")

# 检测所有细分情绪（返回人脸区域+各情绪置信度）
emotion_results = detector.detect_emotions(image)
print("细分情绪结果：", emotion_results)

# 提取单个人脸的细分情绪
if emotion_results:
    face_emotions = emotion_results[0]["emotions"]
    print("喜（happy）：{:.2f}".format(face_emotions["happy"]))
    print("怒（angry）：{:.2f}".format(face_emotions["angry"]))
    print("哀（sad）：{:.2f}".format(face_emotions["sad"]))
    print("惧（fear）：{:.2f}".format(face_emotions["fear"]))
    print("惊（surprise）：{:.2f}".format(face_emotions["surprise"]))
    print("厌（disgust）：{:.2f}".format(face_emotions["disgust"]))
    print("中性（neutral）：{:.2f}".format(face_emotions["neutral"]))