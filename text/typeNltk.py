import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab')
# 定义技能函数
def play_music():
    response = "播放网易云音乐。"
    print(response)
    # 这里可以集成实际的音乐播放代码

def send_wechat_message(message):
    response = f"发送微信消息: {message}。"
    print(response)
    # 这里可以集成实际的微信消息发送代码

def check_weather():
    response = "今天天气晴朗。"
    print(response)
    # 这里可以集成实际的天气查询代码


def recognize_speech(command):
    print(f"你说了: {command}")
    return command

def process_command(command):
    if not command:
        return "我没听清楚，请再说一遍。"

    # 将命令转换为小写并进行分词和停用词过滤
    command = command.lower()
    tokens = word_tokenize(command)
    print(tokens)
    filtered_tokens = [word for word in tokens if word.isalnum() and word not in stopwords.words('chinese')]
    print(filtered_tokens)
    # 处理技能匹配
    if "播放" in filtered_tokens and "网易云音乐" in filtered_tokens:
        play_music()
    elif "用" in filtered_tokens and "微信" in filtered_tokens or ("消息" in filtered_tokens):
        # 提取微信消息
        message_match = re.search(r'用微信(.+)', command)
        if message_match:
            message = message_match.group(1).strip()
            send_wechat_message(message)
        else:
            print("请告诉我你想发送的微信消息内容。")
    elif "天气" in filtered_tokens and ("咋样" in filtered_tokens or "如何" in filtered_tokens):
        check_weather()
    else:
        print("对不起，我无法处理这个请求。")

def main():
    # while True:
        command = recognize_speech('定一个去北京的机票')
        process_command(command)

if __name__ == "__main__":
    main()