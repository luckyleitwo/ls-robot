import asyncio
import os
import re
import tempfile
import threading
import traceback
import uuid

import pygame
from robot import chatGpt, utils, logging, Player, ASR, config, statistic, constants, TTS, NLU
from robot.LifeCycleHandler import LifeCycleHandler
from robot.Scheduler import Scheduler
from robot.sdk import History
import pvporcupine
import pyaudio
import time
import struct
import edge_tts
from pydub import AudioSegment
from pydub.playback import play

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
            self.ai = chatGpt.get_robot_by_slug(config.get("robot", "openai"))
            self.tts = TTS.get_engine_by_slug(config.get("tts_engine", "baidu-tts"))
            self.nlu = NLU.get_engine_by_slug(config.get("nlu_engine", "unit"))
            self.player = Player.SoxPlayer()
            # self.brain = Brain(self)
            # self.brain.printPlugins()
        except Exception as e:
            logger.critical(f"对话初始化失败：{e}", stack_info=True)

    def _lastCompleted(self, index, onCompleted):
        # logger.debug(f"{index}, {self.tts_index}, {self.tts_count}")
        if index >= self.tts_count - 1:
            # logger.debug(f"执行onCompleted")
            onCompleted and onCompleted()

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
                    logger.info(self.play_lock)
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

    def _tts_line(self, line, cache, index=0, onCompleted=None):
        """
        对单行字符串进行 TTS 并返回合成后的音频
        :param line: 字符串
        :param cache: 是否缓存 TTS 结果
        :param index: 合成序号
        :param onCompleted: 播放完成的操作
        """
        line = line.strip()
        pattern = r"http[s]?://.+"
        if re.match(pattern, line):
            logger.info("内容包含URL，屏蔽后续内容")
            return None
        line.replace("- ", "")
        if line:
            result = self._ttsAction(line, cache, index, onCompleted)
            return result
        return None

    def _after_play(self, msg, audios, plugin=""):
        cached_audios = [
            f"http://{config.get('/server/host')}:{config.get('/server/port')}/audio/{os.path.basename(voice)}"
            for voice in audios
        ]
        if self.onSay:
            logger.info(f"onSay: {msg}, {cached_audios}")
            self.onSay(msg, cached_audios, plugin=plugin)
            self.onSay = None
        utils.lruCache()  # 清理缓存

    def stream_say(self, stream, cache=False, onCompleted=None):
        """
        从流中逐字逐句生成语音
        :param stream: 文字流，可迭代对象
        :param cache: 是否缓存 TTS 结果
        :param onCompleted: 声音播报完成后的回调
        """
        logger.info("进入流成声语音")
        logger.info(stream)
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
                    print(line)
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
        # self.appendHistory(1, msg, UUID=resp_uuid, plugin="")
        self._after_play(msg, audios, "")

    def _onCompleted(self, msg):
        if config.get('active_mode', False) and \
                (
                        msg.endswith('?') or
                        msg.endswith(u'？') or
                        u'告诉我' in msg or u'请回答' in msg
                ):
            query = self.activeListen()
            self.doResponse(query)

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

    async def generate_speech(self, text, filename):
        logger.info(text)
        rate = '-4%'
        volume = '+0%'
        voice = 'zh-CN-YunxiNeural'
        tts = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume=volume)
        await tts.save(constants.getData(filename))

    def checkRestore(self):
        if self.immersiveMode:
            self.brain.restore()

    def doParse(self, query):
        args = {
            "service_id": config.get("/unit/service_id", "S13442"),
            "api_key": config.get("/unit/api_key", "w5v7gUV3iPGsGntcM84PtOOM"),
            "secret_key": config.get(
                "/unit/secret_key", "KffXwW6E1alcGplcabcNs63Li6GvvnfL"
            ),
        }
        return self.nlu.parse(query, **args)

    def doResponse(self, query, UUID="", onSay=None, onStream=None):
        """
        响应指令

        :param query: 指令
        :UUID: 指令的UUID
        :onSay: 朗读时的回调
        :onStream: 流式输出时的回调
        """
        logger.info("响应指令")
        statistic.report(1)
        self.interrupt()
        
        parsed = self.doParse(query=query)
        # msg = self.ai.chat(texts=query,parsed=parsed)
        # logger.info(msg)
        stream = self.ai.stream_chat(query)
        # logger.info(stream)
        # self.say(stream, True, onCompleted=self.checkRestore)
        self.stream_say(stream, False, onCompleted=self.checkRestore)
        # msg = self.ai.chat(texts=query, parsed=parsed)
        # self.say(msg, True, onCompleted=self.checkRestore)
        # logger.info('初始化openai')
        # msg = chatGpt.openChat(query)
        # logger.info("调用完成openai")
        # logger.info(msg)
        # filename = "aaa.wav"

        # Generate speech
        # asyncio.run(self.generate_speech(text=msg, filename=filename))

        # Play the generated audio
        # self.lifeCycleHandler.onHuiDa()
        # asyncio.run(self.text_to_speech(msg))
        # self.stream_say(stream=msg, onCompleted=self.checkRestore)

    def appendHistory(self, t, text, UUID='', plugin=''):
        """ 将会话历史加进历史记录 """

        if t in (0, 1) and text is not None and text != '':
            if text.endswith(',') or text.endswith('，'):
                text = text[:-1]
            if UUID == '' or UUID == None or UUID == 'null':
                UUID = str(uuid.uuid1())
            # 将图片处理成HTML
            pattern = r'https?://.+\.(?:png|jpg|jpeg|bmp|gif|JPG|PNG|JPEG|BMP|GIF)'
            url_pattern = r'^https?://.+'
            imgs = re.findall(pattern, text)
            for img in imgs:
                text = text.replace(img,
                                    '<a data-fancybox="images" href="{}"><img src={} class="img fancybox"></img></a>'.format(
                                        img, img))
            urls = re.findall(url_pattern, text)
            for url in urls:
                text = text.replace(url, '<a href={} target="_blank">{}</a>'.format(url, url))
            self.history.add_message(
                {'type': t, 'text': text, 'time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                 'uuid': UUID, 'plugin': plugin})

    def say(self, msg, cache=False, plugin='', onCompleted=None, wait=False):
        """
        说一句话
        :param msg: 内容
        :param cache: 是否缓存这句话的音频
        :param plugin: 来自哪个插件的消息（将带上插件的说明）
        :param onCompleted: 完成的回调
        :param wait: 是否要等待说完（为True将阻塞主线程直至说完这句话）
        """
        self.appendHistory(1, msg, plugin=plugin)
        pattern = r'^https?://.+'
        if re.match(pattern, msg):
            logger.info("内容包含URL，所以不读出来")
            self.onSay(msg, '', plugin=plugin)
            self.onSay = None
            return
        voice = ''
        cache_path = ''
        if utils.getCache(msg):
            logger.info("命中缓存，播放缓存语音")
            voice = utils.getCache(msg)
            cache_path = utils.getCache(msg)
        else:
            try:
                voice = self.tts.get_speech(msg)
                cache_path = utils.saveCache(voice, msg)
            except Exception as e:
                logger.error('保存缓存失败：{}'.format(e))
        if self.onSay:
            logger.info(cache)
            audio = 'http://{}:{}/audio/{}'.format(config.get('/server/host'), config.get('/server/port'),
                                                   os.path.basename(cache_path))
            logger.info('onSay: {}, {}'.format(msg, audio))
            self.onSay(msg, audio, plugin=plugin)
            self.onSay = None
        if onCompleted is None:
            onCompleted = lambda: self._onCompleted(msg)
        self.player = Player.SoxPlayer()
        self.player.play(voice, not cache, onCompleted)
        if not cache:
            utils.check_and_delete(cache_path, 60)  # 60秒后将自动清理不缓存的音频
        utils.lruCache()  # 清理缓存
