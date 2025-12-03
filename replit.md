# 小红书/微博爬虫 + 情绪筛选项目

## 项目目标
采集小红书和微博的文本+图片，**先分析情绪，符合条件才存储**。

## 核心逻辑

### 文本处理流程
```
爬取文本 → 情绪分析(DeepSeek) → 包含目标情绪? → 是: 存储 / 否: 跳过
```

### 图片处理流程
```
爬取图片 → 检测人脸/身体 → 有人? → 是: 情绪分析(FER) → 包含目标情绪? → 是: 存储
                              ↓ 否
                           跳过
```

## 项目结构
```
code/
├── main.py               # 主程序入口
├── config.py             # 配置（目标情绪、最低分数等）
├── login_utils.py        # 扫码登录
├── crawler_utils.py      # 爬虫+文本情绪筛选
├── emotion_filter.py     # 情绪分析模块
└── filter_images_local.py # 本地图片筛选脚本
```

## 配置说明（config.py）
```python
EMOTION_CONFIG = {
    "target_emotions": ["喜", "怒", "哀", "惧", "惊", "厌"],  # 目标情绪
    "min_score": 0.3,  # 最低情绪分数阈值
}
```

## 命令行使用
```bash
python main.py --texts 100 --images 100   # 爬取100条文本和图片
python main.py --weibo-only               # 只爬微博
python main.py --xhs-only                 # 只爬小红书
```

## 数据存储
```
data/
├── texts/
│   ├── weibo/filtered_20241203.json      # 通过筛选的文本（带情绪标签）
│   └── xiaohongshu/filtered_20241203.json
└── images/
    ├── weibo/
    │   ├── pending/    # 待本地分析的图片
    │   ├── filtered/   # 通过筛选的图片
    │   └── rejected/   # 未通过筛选的图片
    └── xiaohongshu/
        └── ...
```

## 本地运行指南

### 1. 文本爬取（Replit或本地）
```bash
cd code
python main.py --texts 1000 --weibo-only
```

### 2. 图片情绪筛选（仅本地）
```bash
pip install fer opencv-python tensorflow
python filter_images_local.py
```

## 环境限制
- Replit IP在海外，小红书触发反爬
- Replit存储限制2GB，无法安装TensorFlow
- 图片情绪分析必须在本地运行

## 最近更新
- 2024-12: 重构为"边爬边筛选"逻辑
- 2024-12: 删除关键词搜索，改为热门/推荐页爬取
- 2024-12: 图片先检测人体，再分析情绪
- 2024-12: 清理冗余代码
