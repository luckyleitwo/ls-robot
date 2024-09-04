import json

from openai import OpenAI
from robot import logging, config

logger = logging.getLogger(__name__)

def open_chat(msg):
    access_key = config.get("/llmApi/prompt")
    context = f"{access_key} \n\n接下来我的输入是：{{{{{msg}}}}}"
    client = OpenAI(
        api_key=config.get("/llmApi/api_key"),
        base_url=config.get("/llmApi/api_key"),  # 指向讯飞星火的请求地址
        default_headers={"x-foo": "true"}
    )
    logger.info("开始")
    response = client.chat.completions.create(
        model="general",
        messages=[{"role": "user", "content": context}],
        stream=False,
        temperature=0.1,
        top_p=1,
        frequency_penalty=0,
        max_tokens=100
    )
    logger.info("结束")
    print(response.choices[0].message.content)
    # json_object = json.loads(response.choices[0].message.content)
    # if (json_object['type'] == "404"):
    #     logger.info("开始")
    #     zzz = client.chat.completions.create(
    #         model="general",
    #         messages=[{"role": "user", "content": msg}],
    #         stream=True,
    #         temperature=0.6,
    #         top_p=1,
    #         frequency_penalty=0,
    #     )
    #     logger.info("结束")
    #     # print(zzz.choices[0].message.content)
    #     for line in zzz:
    #         print(line)
    #         logger.info(line.choices[0].delta.content)
    #         # print()
    return response


open_chat(msg="播放陶喆的你爱我还是他")
