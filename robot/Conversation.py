import threading
import traceback
import uuid
from robot import utils, logging, Player, ASR, config, statistic,constants
from robot.LifeCycleHandler import LifeCycleHandler
from robot.Scheduler import Scheduler
from robot.sdk import History
import pvporcupine
import pyaudio
import time
import struct



logger = logging.getLogger(__name__)

class Conversation(object):
    def __init__(self, profiling=False):
        self.brain, self.asr, self.ai, self.tts, self.nlu = None, None, None, None, None
        self.reInit()
        self.scheduler = Scheduler(self)
        # 历史会话消息
        self.history = History.History()
        # 沉浸模式，处于这个模式下，被打断后将自动恢复这个技能
        self.matchPlugin = None
        self.immersiveMode = None
        self.isRecording = False
        self.profiling = profiling
        self.onSay = None
        self.onStream = None
        self.hasPardon = False
        self.player = Player.SoxPlayer()
        self.lifeCycleHandler = LifeCycleHandler(self)
        self.tts_count = 0
        self.tts_index = 0
        self.tts_lock = threading.Lock()
        self.play_lock = threading.Lock()

    def reInit(self):
        """重新初始化"""
        try:
            self.asr = ASR.get_engine_by_slug(config.get("asr_engine", "fun-asr"))
            # self.ai = AI.get_robot_by_slug(config.get("robot", "tuling"))
            # self.tts = TTS.get_engine_by_slug(config.get("tts_engine", "baidu-tts"))
            # self.nlu = NLU.get_engine_by_slug(config.get("nlu_engine", "unit"))
            self.player = Player.SoxPlayer()
            # self.brain = Brain(self)
            # self.brain.printPlugins()
        except Exception as e:
            logger.critical(f"对话初始化失败：{e}", stack_info=True)

    def _ttsAction(self, msg, cache, index, onCompleted=None):
        if msg:
            voice = ""
            if utils.getCache(msg):
                logger.info(f"第{index}段TTS命中缓存，播放缓存语音")
                voice = utils.getCache(msg)
                while index != self.tts_index:
                    # 阻塞直到轮到这个音频播放
                    continue
                with self.play_lock:
                    self.player.play(
                        voice,
                        not cache,
                        onCompleted=lambda: self._lastCompleted(index, onCompleted),
                    )
                    self.tts_index += 1
                return voice
            else:
                try:
                    voice = self.tts.get_speech(msg)
                    logger.info(f"第{index}段TTS合成成功。msg: {msg}")
                    while index != self.tts_index:
                        # 阻塞直到轮到这个音频播放
                        continue
                    with self.play_lock:
                        logger.info(f"即将播放第{index}段TTS。msg: {msg}")
                        self.player.play(
                            voice,
                            not cache,
                            onCompleted=lambda: self._lastCompleted(index, onCompleted),
                        )
                        self.tts_index += 1
                    return voice
                except Exception as e:
                    logger.error(f"语音合成失败：{e}", stack_info=True)
                    self.tts_index += 1
                    traceback.print_exc()
                    return None

    def stream_say(self, stream, cache=False, onCompleted=None):
        """
        从流中逐字逐句生成语音
        :param stream: 文字流，可迭代对象
        :param cache: 是否缓存 TTS 结果
        :param onCompleted: 声音播报完成后的回调
        """
        lines = []
        line = ""
        resp_uuid = str(uuid.uuid1())
        audios = []
        if onCompleted is None:
            onCompleted = lambda: self._onCompleted(msg)
        self.tts_index = 0
        self.tts_count = 0
        index = 0
        skip_tts = False
        for data in stream():
            if self.onStream:
                self.onStream(data, resp_uuid)
            line += data
            if any(char in data for char in utils.getPunctuations()):
                if "```" in line.strip():
                    skip_tts = True
                if not skip_tts:
                    audio = self._tts_line(line.strip(), cache, index, onCompleted)
                    if audio:
                        self.tts_count += 1
                        audios.append(audio)
                        index += 1
                else:
                    logger.info(f"{line} 属于代码段，跳过朗读")
                lines.append(line)
                line = ""
        if line.strip():
            lines.append(line)
        if skip_tts:
            self._tts_line("内容包含代码，我就不念了", True, index, onCompleted)
        msg = "".join(lines)
        self.appendHistory(1, msg, UUID=resp_uuid, plugin="")
        self._after_play(msg, audios, "")

    def activeListen(self, silent=False):
        """
        主动问一个问题(适用于多轮对话)
        :param silent: 是否不触发唤醒表现（主要用于极客模式）
        :param
        """
        if self.immersiveMode:
            self.player.stop()
        elif self.player.is_playing():
            self.player.join()  # 确保所有音频都播完
        logger.info("进入主动聆听...")
        try:
            if not silent:
                self.lifeCycleHandler.onWakeup()
            
            voice = utils.listen_for_hotword()
            if not silent:
                self.lifeCycleHandler.onThink()
            if voice:
                query = self.asr.transcribe(voice)
                utils.check_and_delete(voice)
                return query
            return ""
        except Exception as e:
            logger.error(f"主动聆听失败：{e}", stack_info=True)
            traceback.print_exc()
            return ""

    def interrupt(self):
        if self.player and self.player.is_playing():
            self.player.stop()
        if self.immersiveMode:
            self.brain.pause()
        if self.player and self.player.is_playing():
            self.player.stop()
        if self.immersiveMode:
            self.brain.pause()


    def doResponse(self, query, UUID="", onSay=None, onStream=None):
        """
        响应指令

        :param query: 指令
        :UUID: 指令的UUID
        :onSay: 朗读时的回调
        :onStream: 流式输出时的回调
        """
        statistic.report(1)
        self.interrupt()
        self.appendHistory(0, query, UUID)

        if onSay:
            self.onSay = onSay

        if onStream:
            self.onStream = onStream

        if query.strip() == "":
            self.pardon()
            return

        lastImmersiveMode = self.immersiveMode

        parsed = self.doParse(query)
        if self._InGossip(query) or not self.brain.query(query, parsed):
            # 进入闲聊
            if self.nlu.hasIntent(parsed, "PAUSE") or "闭嘴" in query:
                # 停止说话
                self.player.stop()
            else:
                # 没命中技能，使用机器人回复
                if self.ai.SLUG == "openai":
                    stream = self.ai.stream_chat(query)
                    self.stream_say(stream, True, onCompleted=self.checkRestore)
                else:
                    msg = self.ai.chat(query, parsed)
                    self.say(msg, True, onCompleted=self.checkRestore)
        else:
            # 命中技能
            if lastImmersiveMode and lastImmersiveMode != self.matchPlugin:
                if self.player:
                    if self.player.is_playing():
                        logger.debug("等说完再checkRestore")
                        self.player.appendOnCompleted(lambda: self.checkRestore())
                else:
                    logger.debug("checkRestore")
                    self.checkRestore()
