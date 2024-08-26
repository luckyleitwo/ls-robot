from robot import detector, logging
from server import serverMain

logger = logging.getLogger(__name__)
# # 配置 Porcupine
# keyword_path = "static/huanx_zh_mac_v3_0_0.ppn"  # 预训练的唤醒词模型路径
# access_key = "KLtEYTJi1zHgUyzuZD0t0juvn1SpFEIYz4DSblInl/kFSeLKOAcuqg=="  # 你的 Picovoice 访问密钥

class ls(object):
    def init(self):
        self.detector = None
        print(
            """
********************************************************
*          wukong-robot - 中文语音对话机器人           *
*          (c) 2019 潘伟洲 <m@hahack.com>              *
*               当前版本号:  {}                      *
*     https://github.com/wzpan/wukong-robot.git        *
********************************************************

            后台管理端：http://{}:{}
            如需退出，可以按 Ctrl-4 组合键

"""
        )

    def run(self):
        self.init()
        print(detector)
        try:
            # 初始化离线唤醒
            detector.initDetector(self)
        except AttributeError:
            logger.error("初始化离线唤醒功能失败", stack_info=True)
            pass
        serverMain.app.run(host='0.0.0.0', port=2888, debug=True)




if __name__ == "__main__":
    ls = ls()
    ls.run()
