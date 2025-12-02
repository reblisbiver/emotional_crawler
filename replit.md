# 小红书/微博爬虫 + 情绪分析项目

## 项目概述
基于Selenium的社交媒体爬虫，支持小红书和微博平台的内容爬取，配合AI情绪分析功能。

## 项目结构
```
code/
├── main.py           # 主程序入口
├── config.py         # 配置文件（关键词、超时等）
├── login_utils.py    # 登录工具（二维码扫码登录）
├── crawler_utils.py  # 爬虫核心逻辑
├── save_utils.py     # 数据保存工具
├── test_deep.py      # DeepSeek文本情绪分析测试 ✅
└── tese_opencv.py    # FER人脸表情识别测试 ⚠️需本地运行
```

## 功能状态

### 爬虫功能
| 平台 | 状态 | 说明 |
|------|------|------|
| 微博 | ✅ 正常 | 海外IP可用 |
| 小红书 | ⚠️ 受限 | 海外IP触发反爬，需国内IP |

### 情绪分析
| 模块 | 状态 | 依赖 |
|------|------|------|
| test_deep.py | ✅ 可用 | DeepSeek API |
| tese_opencv.py | ⚠️ 本地运行 | TensorFlow (~900MB) |

## 本地运行指南

### 1. 安装依赖
```bash
pip install selenium requests python-dotenv pillow tenacity
pip install fer opencv-python tensorflow  # 表情识别（仅本地）
```

### 2. 配置ChromeDriver
- Windows: 下载对应版本chromedriver放入项目目录
- Linux/Mac: 安装chromium-chromedriver

### 3. 运行爬虫
```bash
cd code
python main.py
```

### 4. 测试情绪分析
```bash
python test_deep.py                    # 文本情绪分析
python tese_opencv.py <图片路径>        # 人脸表情识别
```

## 环境限制说明
- Replit服务器IP位于海外（孟买），小红书会触发反爬
- Replit Starter计划存储限制2GB，无法安装TensorFlow
- 建议：Replit开发 + 本地运行

## 用户偏好
- 使用二维码扫码登录（自动检测登录状态）
- 超时时间：180秒
- 需要VNC桌面显示浏览器界面

## 最近更新
- 2024-12: 修复中文字体显示问题
- 2024-12: 改进小红书爬取逻辑，增加调试信息
- 2024-12: 优化test_deep.py和tese_opencv.py代码
