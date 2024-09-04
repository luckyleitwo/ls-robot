from io import BytesIO
from urllib.request import urlopen
from transformers import BertForSequenceClassification, AutoProcessor

# 初始化处理器和模型
processor = AutoProcessor.from_pretrained("Qwen/Qwen2-Audio-7B-Instruct")
model = BertForSequenceClassification.from_pretrained("Qwen/Qwen2-Audio-7B-Instruct")


textzz = """"
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

# 准备包含音频和文本的对话内容
conversation = [
    {'role': 'system', 'content':
        {"type": "text", "text": textzz},
     },
    {"role": "user", "content": [
        {"type": "text", "text": "播放陶喆的找自己"},
    ]}
]

text = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)

print(text)

# # 执行模型推理
# inputs = processor(text=text, audios=audios, return_tensors="pt", padding=True)
# inputs.input_ids = inputs.input_ids.to("cuda")
#
# generate_ids = model.generate(**inputs, max_length=256)
# generate_ids = generate_ids[:, inputs.input_ids.size(1):]
#
# response = processor.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
# # 输出模型的响应
# print(response)
