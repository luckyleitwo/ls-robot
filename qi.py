import signal

from robot import detector, logger, utils
from robot.Conversation import Conversation
from robot.LifeCycleHandler import LifeCycleHandler
from server import serverMain

# # 配置 Porcupine
# keyword_path = "static/huanx_zh_mac_v3_0_0.ppn"  # 预训练的唤醒词模型路径
# access_key = "KLtEYTJi1zHgUyzuZD0t0juvn1SpFEIYz4DSblInl/kFSeLKOAcuqg=="  # 你的 Picovoice 访问密钥

class ls(object):
    _profiling = False

    def __init__(self):
        self.conversation = None
        self.lifeCycleHandler = None

    def init(self):
        self.detector = None
        print(
            """
********************************************************
*          ls-robot - 中文语音对话机器人           *
*          (c) 小雷的 机器人            *
********************************************************

            后台管理端：http://{}:{}
            如需退出，可以按 Ctrl-4 组合键

"""
        )
        self.conversation = Conversation(self._profiling)
        self.lifeCycleHandler = LifeCycleHandler(self.conversation)
        self.lifeCycleHandler.onInit()

    def _signal_handler(self, signal, frame):
        self._interrupted = True
        utils.clean()
        self.lifeCycleHandler.onKilled()

    def _detected_callback(self, is_snowboy=True):
        def _start_record():
            logger.info("开始录音")
            self.conversation.isRecording = True
            utils.setRecordable(True)

        if not utils.is_proper_time():
            logger.warning("勿扰模式开启中")
            return
        if self.conversation.isRecording:
            logger.warning("正在录音中，跳过")
            return
        if is_snowboy:
            self.conversation.interrupt()
            utils.setRecordable(False)
            self.lifeCycleHandler.onWakeup()
        if is_snowboy:
            _start_record()
    def run(self):
        self.init()
        signal.signal(signal.SIGINT, self._signal_handler)
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
