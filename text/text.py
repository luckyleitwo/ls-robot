# import json
#
# from openai import OpenAI
# from robot import logging, config
#
# logger = logging.getLogger(__name__)
#
# def open_chat(msg):
#     access_key = config.get("/llmApi/prompt")
#     context = f"{access_key} \n\n接下来我的输入是：{{{{{msg}}}}}"
#     print(context)
#     client = OpenAI(
#         api_key=config.get("/llmApi/api_key"),
#         base_url=config.get("/llmApi/base_url"),  # 指向讯飞星火的请求地址
#         default_headers={"x-foo": "true"}
#     )
#     print(client)
#     logger.info("开始")
#     response = client.chat.completions.create(
#         model="general",
#         messages=[{"role": "user", "content": context}],
#         stream=False,
#         temperature=0.1,
#         top_p=1,
#         frequency_penalty=0,
#         max_tokens=100
#     )
#     logger.info("结束")
#     print(response.choices[0].message.content)
#     return response
#
#
# open_chat(msg="帮我定一个机票")
import asyncio

from robot.Conversation import Conversation

conversationz = Conversation(False)


asyncio.run(conversationz.doResponse(query="讲一个笑话"))

