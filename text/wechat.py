import requests

import lib.itchat as itchat

from lib.itchat.content import *


@itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING])
def text_reply(msg):
    print("22222")
    url = 'https://s1.v100.vip:9674/api/v1/user/login'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'username': 'admin',
        'password': 'lei.comse'
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()  # 检查请求是否成功
        print(response.status_code)
        print(response.json())
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    msg.user.send('%s: %s' % (msg.type, msg.text))


@itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO])
def download_files(msg):
    print("111111")
    msg.download(msg.fileName)

    typeSymbol = {

        PICTURE: 'img',

        VIDEO: 'vid', }.get(msg.type, 'fil')

    return '@%s@%s' % (typeSymbol, msg.fileName)


@itchat.msg_register(FRIENDS)
def add_friend(msg):
    print("=====")
    msg.user.verify()

    msg.user.send('Nice to meet you!')


@itchat.msg_register(TEXT, isGroupChat=True)
def text_reply(msg):
    print("----")
    if msg.isAt:

        msg.user.send(u'@%s\u2005I received: %s' % (

            msg.actualNickName, msg.text))



itchat.auto_login(True)

itchat.run(True)