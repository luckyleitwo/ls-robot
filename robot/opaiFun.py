import openai

from robot import logging

logger = logging.getLogger(__name__)

text = """"
 你是一个语意义识别助手 你可以匹配以下技能
1.发微信
2.播放音乐

匹配技能返回结构个是
微信: {"type": "wechat","data": ["发送微信人名称如果没有就空字符串","发送内容"]}
音乐: {"type": "music","data": ["歌手名称如果没有就空字符串","歌曲名称"]}

\n如用户说 发消息 你回答 {"type": "微信","data": [这里是你根据 用户发的消息匹配的内容(如用户说发你好给冰棒 里面的内容就是 ["冰棒","你好"] 且如果用户发送的是 发消息没有具体发给谁 data里面只需要[] )]}

如果是音乐 有歌曲名称需要对歌曲名称和唱歌人进行分词处理

\n没有匹配的技能就返回 {"type": 404}\n
"""

def open_chat(model,context,stream,msg,type):
    openai.api_key = 'sk-ZRD4wE1uJUhTm0xh7d5152D55f994b78961540665a50Ff00'
    openai.base_url = "https://free.gpt.ge/v1/"
    openai.default_headers = {"x-foo": "true"}
    logger.info(context)
    constz = context if type == 1 else [{"role": "system", "content": text},{"role": "user", "content": msg}]
    logger.info(constz)
    response =  openai.chat.completions.create(
        model=model,
        messages=constz,
        stream=stream,
        temperature=0.6,
        top_p=1,
        frequency_penalty=0
    )

    return response

