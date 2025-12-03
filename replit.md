# 小红书/微博爬虫 + 情绪分析项目

## 项目目标
在小红书和微博平台采集约1万张图片及1万条文本，进行情绪识别（喜怒哀惧惊厌及中性）并打上标签存储。

## 项目结构
```
code/
├── main.py               # 主程序入口（支持命令行参数）
├── config.py             # 配置文件（目标条数、情绪类别等）
├── login_utils.py        # 登录工具（二维码扫码登录）
├── crawler_utils.py      # 爬虫核心逻辑（多页爬取）
├── save_utils.py         # 数据保存工具（带情绪标签）
├── emotion_analyzer.py   # 情绪分析模块
├── analyze_images_local.py  # 本地图片情绪分析脚本
├── test_deep.py          # DeepSeek文本情绪测试
└── tese_opencv.py        # FER人脸表情识别测试
```

## 核心功能
1. **多页爬取**：以目标条数为结束标志，自动翻页/滚动
2. **文本情绪分析**：使用DeepSeek API，实时分析爬取文本
3. **图片情绪分析**：使用FER库（需本地运行）
4. **带标签存储**：JSON格式，包含7种情绪评分

## 命令行参数
```bash
python main.py --texts 100        # 设置目标文本条数
python main.py --images 100       # 设置目标图片数量
python main.py --weibo-only       # 只爬取微博
python main.py --xhs-only         # 只爬取小红书
python main.py --no-emotion       # 不进行情绪分析
python main.py --analyze-only     # 仅分析已有数据
```

## 配置说明（config.py）
```python
CRAWL_CONFIG = {
    "target_texts": 20,    # 目标文本条数
    "target_images": 20,   # 目标图片数量
    "max_pages": 50,       # 最大页数
}

EMOTION_CONFIG = {
    "emotions": ["喜", "怒", "哀", "惧", "惊", "厌", "中性"],
    "analyze_text": True,  # 是否分析文本
    "analyze_image": True, # 是否分析图片
}
```

## 数据存储结构
```
data/
├── texts/              # 原始文本数据
│   ├── xiaohongshu/
│   └── weibo/
├── images/             # 原始图片
│   ├── xiaohongshu/
│   └── weibo/
└── analyzed/           # 带情绪标签的分析结果
    ├── texts_with_emotion_*.json
    ├── images_with_emotion_*.json
    └── stats_*.json    # 情绪统计
```

## 本地运行指南

### 1. 安装依赖
```bash
pip install selenium requests python-dotenv pillow tenacity
pip install fer opencv-python tensorflow  # 图片情绪识别
```

### 2. 运行完整流程
```bash
cd code
python main.py --texts 1000 --images 1000
```

### 3. 单独分析已有图片
```bash
python analyze_images_local.py
```

## 环境限制
- Replit IP在海外，小红书触发反爬
- Replit存储限制2GB，无法安装TensorFlow
- 建议：Replit开发代码 → 本地运行爬虫

## 最近更新
- 2024-12: 支持多页爬取，以目标条数为结束标志
- 2024-12: 集成DeepSeek文本情绪分析
- 2024-12: 添加本地图片情绪分析脚本
- 2024-12: 优化数据存储格式（带情绪标签）
