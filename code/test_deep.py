import requests
import json
import re
from tenacity import retry, stop_after_attempt, wait_exponential

DEEPSEEK_API_KEY = "sk-a4890b6f726f4b2591902f5b3ea7c313"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
EMOTIONS = ["喜", "怒", "哀", "惧", "惊", "厌", "中性"]

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def analyze_text_emotion(text):
    # 文本预处理：清理特殊字符+截断
    text = re.sub(r'\s+', ' ', text).strip()
    text = text[:2000]  # 限制输入长度
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
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
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()
        # 额外校验返回内容是否为JSON
        if not content.startswith("{") or not content.endswith("}"):
            raise ValueError("返回内容非JSON格式")
        emotion_data = json.loads(content)
        return emotion_data
    except Exception as e:
        raise e  # 抛出异常让重试机制处理

def batch_analyze_emotions(text_list):
    print("=== 复杂文本情绪识别批量测试 ===\n")
    for idx, text in enumerate(text_list, 1):
        print(f"【测试文本{idx}】：{text}")
        try:
            emotion_result = analyze_text_emotion(text)
            if emotion_result:
                print("情绪评分：")
                for emo, score in emotion_result["emotions"].items():
                    print(f"  {emo}: {score}分", end=" | ")
                print(f"\n主情绪：{emotion_result['main_emotion']} | 次要情绪：{emotion_result['secondary_emotion']}\n")
            else:
                print("分析结果为空！\n")
        except Exception as e:
            print(f"分析失败：{str(e)[:100]} | 文本：{text[:20]}...\n")

if __name__ == "__main__":
    complex_texts = [
        "加班到凌晨走小巷回家，总感觉身后有脚步声跟着，回头却没人，拐进拐角时瞥见一个黑影贴墙站着，呼吸瞬间停了，攥紧手机的手全是汗——他是不是要跟过来？",
        "住进乡下老宅的第一晚，半夜被楼上‘咚、咚’的脚步声吵醒，可老宅明明只有一层；想开灯却发现停电了，窗外的树影晃得像人，连大气都不敢喘。",
        "整理旧物翻出小时候被锁过的黑木箱，刚打开一条缝，突然想起被关在里面整整一下午的窒息感，手脚瞬间冰凉，连碰都不敢碰，转身跑出了房间。",
        "下班坐电梯时突然断电，轿厢猛地一沉卡在10楼和11楼之间，手机没信号，四周黑得伸手不见五指，心跳快得像要炸开，总觉得墙壁在往中间挤。",
        "凌晨三点起夜，路过客厅时瞥见镜子里的自己身后站着个模糊的人影，眨眨眼再看却没了；回到卧室总感觉枕头边有人呼吸，蒙着被子不敢睁眼。",
        "坐在沙发上突然感觉地板在晃，杯子里的水洒了一地，吊灯晃得厉害，楼上传来家具倒地的声音——是地震？！脑子一片空白，连躲到桌子下都忘了。",
        "站在几百人的会场演讲，突然忘词了，台下的目光像针一样扎过来，有人开始窃笑，腿抖得站不稳，只想立刻钻进地缝里，甚至觉得喘不过气。",
        "拿到体检报告看到‘疑似恶性病变’几个字，手开始抖，连报告都捏不住，脑子里反复想‘要是真的怎么办？爸妈怎么办？’，越想越怕，连医生的话都听不清了。",
        "爬山时拨开草丛，突然看到一条绿蛇吐着信子盯着我，距离不到一米，瞬间僵在原地，腿软得迈不动步，生怕它扑过来咬一口。",
        "露营时跟队友走散，手机没电，天完全黑了，四周全是虫鸣和不知名的兽叫，风吹过树林的声音像有人在哭，越走越怕，干脆蹲在原地不敢动。"
    ]
    batch_analyze_emotions(complex_texts)