# -*- coding: utf -8-*-
import os
import subprocess
import uuid

import asyncio
import edge_tts
import nest_asyncio
from robot import logging, utils, config, constants
from abc import ABCMeta, abstractmethod
from robot.sdk import VITSClient

logger = logging.getLogger(__name__)
nest_asyncio.apply()


class AbstractTTS(object):
    """
    Generic parent class for all TTS engines
    """

    __metaclass__ = ABCMeta

    @classmethod
    def get_config(cls):
        return {}

    @classmethod
    def get_instance(cls):
        profile = cls.get_config()
        instance = cls(**profile)
        return instance

    @abstractmethod
    def get_speech(self, phrase):
        pass


class EdgeTTS(AbstractTTS):
    """
    edge-tts 引擎
    voice: 发音人，默认是 zh-CN-XiaoxiaoNeural
        全部发音人列表：命令行执行 edge-tts --list-voices 可以打印所有语音
    """

    SLUG = "edge-tts"

    def __init__(self, voice="zh-CN-YunxiNeural", **args):
        super(self.__class__, self).__init__()
        self.voice = voice

    @classmethod
    def get_config(cls):
        # Try to get ali_yuyin config from config
        return config.get("edge-tts", {})

    async def async_get_speech(self, phrase):
        try:
            tmpfile = os.path.join(constants.TEMP_PATH, uuid.uuid4().hex + ".mp3")
            tts = edge_tts.Communicate(text=phrase, voice=self.voice, rate='-4%', volume='+0%')
            await tts.save(tmpfile)
            logger.info(f"{self.SLUG} 语音合成成功，合成路径：{tmpfile}")
            return tmpfile
        except Exception as e:
            logger.critical(f"{self.SLUG} 合成失败：{str(e)}！", stack_info=True)
            return None

    def get_speech(self, phrase):
        event_loop = asyncio.new_event_loop()
        tmpfile = event_loop.run_until_complete(self.async_get_speech(phrase))
        event_loop.close()
        return tmpfile


class MacTTS(AbstractTTS):
    """
    macOS 系统自带的TTS
    voice: 发音人，默认是 Tingting
        全部发音人列表：命令行执行 say -v '?' 可以打印所有语音
        中文推荐 Tingting（普通话）或者 Sinji（粤语）
    """

    SLUG = "mac-tts"

    def __init__(self, voice="Tingting", **args):
        super(self.__class__, self).__init__()
        self.voice = voice

    @classmethod
    def get_config(cls):
        # Try to get ali_yuyin config from config
        return config.get("mac-tts", {})

    def get_speech(self, phrase):
        tmpfile = os.path.join(constants.TEMP_PATH, uuid.uuid4().hex + ".asiff")
        res = subprocess.run(
            ["say", "-v", self.voice, "-o", tmpfile, str(phrase)],
            shell=False,
            universal_newlines=True,
        )
        if res.returncode == 0:
            logger.info(f"{self.SLUG} 语音合成成功，合成路径：{tmpfile}")
            return tmpfile
        else:
            logger.critical(f"{self.SLUG} 合成失败！", stack_info=True)


class VITS(AbstractTTS):
    """
    VITS 语音合成
    需要自行搭建vits-simple-api服务器：https://github.com/Artrajz/vits-simple-api
    server_url : 服务器url，如http://127.0.0.1:23456
    api_key : 若服务器配置了API Key，在此填入
    speaker_id : 说话人ID，由所使用的模型决定
    length : 调节语音长度，相当于调节语速，该数值越大语速越慢。
    noise : 噪声
    noisew : 噪声偏差
    max : 分段阈值，按标点符号分段，加起来大于max时为一段文本。max<=0表示不分段。
    timeout: 响应超时时间，根据vits-simple-api服务器性能不同配置合理的超时时间。
    """

    SLUG = "VITS"

    def __init__(self, server_url, api_key, speaker_id, length, noise, noisew, max, timeout, **args):
        super(self.__class__, self).__init__()
        self.server_url, self.api_key, self.speaker_id, self.length, self.noise, self.noisew, self.max, self.timeout = (
            server_url, api_key, speaker_id, length, noise, noisew, max, timeout)

    @classmethod
    def get_config(cls):
        return config.get("VITS", {})

    def get_speech(self, phrase):
        result = VITSClient.tts(phrase, self.server_url, self.api_key, self.speaker_id, self.length, self.noise,
                                self.noisew, self.max, self.timeout)
        tmpfile = utils.write_temp_file(result, ".wav")
        logger.info(f"{self.SLUG} 语音合成成功，合成路径：{tmpfile}")
        return tmpfile


def get_engine_by_slug(slug=None):
    """
    Returns:
        A TTS Engine implementation available on the current platform

    Raises:
        ValueError if no speaker implementation is supported on this platform
    """

    if not slug or type(slug) is not str:
        raise TypeError("无效的 TTS slug '%s'", slug)

    selected_engines = list(
        filter(
            lambda engine: hasattr(engine, "SLUG") and engine.SLUG == slug,
            get_engines(),
        )
    )

    if len(selected_engines) == 0:
        raise ValueError(f"错误：找不到名为 {slug} 的 TTS 引擎")
    else:
        if len(selected_engines) > 1:
            logger.warning(f"注意: 有多个 TTS 名称与指定的引擎名 {slug} 匹配")
        engine = selected_engines[0]
        logger.info(f"使用 {engine.SLUG} TTS 引擎")
        return engine.get_instance()


def get_engines():
    def get_subclasses(cls):
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_subclasses(subclass))
        return subclasses

    return [
        engine
        for engine in list(get_subclasses(AbstractTTS))
        if hasattr(engine, "SLUG") and engine.SLUG
    ]
