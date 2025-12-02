from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import os
import warnings

# 忽略无关警告
warnings.filterwarnings("ignore")

# ===== 1. 核心配置（本地模型+缓存权限）=====
# 本地模型路径（替换为你的本地模型文件夹绝对路径！）
LOCAL_MODEL_PATH = r"D:\Python\Code Collection\.emotional_crawler\emotion_model"
# 缓存目录（项目内，仅用于模型加载临时文件，不下载远程内容）
CACHE_DIR = os.path.join(os.path.dirname(__file__), "huggingface_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# 设备自动选择（GPU优先，无则CPU）
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"当前使用设备: {device}")
print(f"本地模型路径: {LOCAL_MODEL_PATH}")

# ===== 2. 情绪标签映射 =====
label_mapping = {
    0: "中立",
    1: "关切",
    2: "开心",
    3: "愤怒",
    4: "悲伤",
    5: "疑惑",
    6: "惊奇",
    7: "厌恶"
}

# ===== 3. 本地模型文件校验（避免文件缺失）=====
REQUIRED_MODEL_FILES = [
    "config.json",          # 模型配置
    "pytorch_model.bin",    # 模型权重（或 model.safetensors）
    "tokenizer.json",       # 分词器核心文件
    "tokenizer_config.json",# 分词器配置
    "special_tokens_map.json"  # 特殊token映射
]

def check_local_model_files():
    """校验本地模型文件是否完整"""
    missing_files = []
    for file in REQUIRED_MODEL_FILES:
        file_path = os.path.join(LOCAL_MODEL_PATH, file)
        # 兼容 model.safetensors（部分模型用这个替代 pytorch_model.bin）
        if file == "pytorch_model.bin" and not os.path.exists(file_path):
            if os.path.exists(os.path.join(LOCAL_MODEL_PATH, "model.safetensors")):
                continue  # 存在 safetensors 版本则跳过
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 本地模型文件缺失：{', '.join(missing_files)}")
        print(f"请检查 {LOCAL_MODEL_PATH} 文件夹，确保包含所有必要文件")
        raise FileNotFoundError(f"缺失模型文件：{', '.join(missing_files)}")
    print("✅ 本地模型文件完整")

# ===== 4. 全局加载本地模型（只加载1次）=====
tokenizer = None
model = None

def init_local_model():
    """初始化本地模型和分词器（仅加载本地文件，不访问远程）"""
    global tokenizer, model
    try:
        # 先校验文件完整性
        check_local_model_files()
        
        print("正在加载本地模型...")
        # 加载分词器（强制本地加载，禁用fast分词器兼容版本）
        tokenizer = AutoTokenizer.from_pretrained(
            LOCAL_MODEL_PATH,
            cache_dir=CACHE_DIR,
            local_files_only=True,  # 关键：仅加载本地文件
            use_fast=False,         # 关键：适配transformers 4.38.2
            trust_remote_code=False # 禁用远程代码，更安全
        )
        # 加载模型（强制本地加载）
        model = AutoModelForSequenceClassification.from_pretrained(
            LOCAL_MODEL_PATH,
            cache_dir=CACHE_DIR,
            local_files_only=True,  # 仅加载本地文件
            trust_remote_code=False,
            ignore_mismatched_sizes=True  # 忽略小版本兼容问题
        ).to(device)
        model.eval()  # 切换到评估模式（预测专用）
        print("✅ 本地模型加载成功！\n")
    except Exception as e:
        print(f"❌ 本地模型加载失败：{str(e)}")
        raise SystemExit(1)  # 加载失败则退出

# 初始化本地模型（程序启动时执行1次）
init_local_model()

# ===== 5. 情绪预测核心函数 =====
def predict_emotion(text):
    """输入文本，返回预测的情绪标签"""
    # 输入验证
    if not isinstance(text, str) or text.strip() == "":
        return "❌ 输入文本不能为空"
    
    try:
        # 文本编码（适配模型输入格式）
        inputs = tokenizer(
            text.strip(),
            return_tensors="pt",  # 返回PyTorch张量
            truncation=True,      # 超长文本截断
            padding=True,         # 不足长度填充
            max_length=512        # 最大文本长度（避免内存溢出）
        ).to(device)  # 移到GPU/CPU设备
        
        # 预测（关闭梯度计算，提升速度+减少内存占用）
        with torch.no_grad():
            outputs = model(**inputs)
        
        # 解析结果（取概率最大的标签）
        predicted_class = torch.argmax(outputs.logits, dim=1).item()
        return label_mapping.get(predicted_class, "❌ 未知情绪")
    
    except Exception as e:
        return f"❌ 预测失败：{str(e)[:50]}..."  # 截取错误信息，避免过长

# ===== 6. 测试运行 =====
if __name__ == "__main__":
    test_texts = [
    # 0-中立（平淡陈述日常，无强烈情绪）
    "今天下班顺路买了点水果，回家洗干净就能吃了。",
    # 1-关切（关心他人状况，语气温暖）
    "你昨天发烧还没好吗？记得多喝温水，别硬扛着呀。",
    # 2-开心（分享喜悦，情绪明朗）
    "抽奖居然中了电影票！还是我最想看的那部，太惊喜啦～",
    # 3-愤怒（遭遇不公/冒犯，带不满情绪）
    "隔壁邻居大半夜还在装修，电钻声吵得根本没法睡觉，太过分了！",
    # 4-悲伤（失落/难过，流露负面情绪）
    "养了三年的小猫走了，现在看到它的玩具，心里还是空落落的。",
    # 5-疑惑（对事情不理解，有疑问）
    "我明明记得把文件存在桌面了，怎么刷新半天都找不到？",
    # 6-惊奇（意外发现/突发情况，语气惊讶）
    "刚才在超市居然碰到小学同学了！好几年没见，他居然还记得我的名字。",
    # 7-厌恶（对人/事反感，带排斥情绪）
    "公共场合总有人大声外放视频，声音又吵又刺耳，真的很让人反感。"
]

    # 批量预测并格式化输出
    for idx, text in enumerate(test_texts, 1):
        emotion = predict_emotion(text)
        print(f"📄 测试文本 {idx}")
        print(f"原文：{text}")
        print(f"预测情绪：{emotion}\n" + "-"*80 + "\n")