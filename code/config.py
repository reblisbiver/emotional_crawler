import os
from dotenv import load_dotenv

# 加载.env文件（如果没有.env，会用后面的默认值）
load_dotenv()

# -------------------------- 核心配置：必须正确定义 --------------------------
# 小红书配置（确保变量名是 XHS_CONFIG，全大写）
XHS_CONFIG = {
    "phone": os.getenv("XHS_PHONE", "17350575312"),  # 替换为你的手机号，默认值避免为空
    "search_url": "https://www.xiaohongshu.com/search_result"
}

# 微博配置（确保变量名是 WEIBO_CONFIG，全大写）
WEIBO_CONFIG = {
    "phone": os.getenv("WEIBO_PHONE", "17350575312"),  # 替换为你的手机号
    "search_url": "https://s.weibo.com/weibo"
}
# ----------------------------------------------------------------------------

# 保存配置（不变）
SAVE_CONFIG = {
    "text_path": os.getenv("SAVE_TEXT_PATH", "./data/texts"),
    "image_path": os.getenv("SAVE_IMAGE_PATH", "./data/images"),
    "keyword": "牢大"
}

# 创建保存目录（无语法错误）
for path in [SAVE_CONFIG["text_path"], SAVE_CONFIG["image_path"]]:
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, "xiaohongshu"), exist_ok=True)
    os.makedirs(os.path.join(path, "weibo"), exist_ok=True)

# 调试用：打印配置是否加载成功（运行后能看到手机号说明没问题）
print("✅ config.py 加载成功！")
