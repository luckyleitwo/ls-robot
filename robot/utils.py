import time
import wave

from robot import config


def getPunctuations():
    return [",", "，", ".", "。", "?", "？", "!", "！", "\n"]

def setRecordable(value):
    """设置是否可以开始录制语音"""
    global is_recordable
    is_recordable = value

def is_proper_time():
    """是否合适时间"""
    global do_not_bother
    if do_not_bother == True:
        return False
    if not config.has("do_not_bother"):
        return True
    bother_profile = config.get("do_not_bother")
    if not bother_profile["enable"]:
        return True
    if "since" not in bother_profile or "till" not in bother_profile:
        return True
    since = bother_profile["since"]
    till = bother_profile["till"]
    current = time.localtime(time.time()).tm_hour
    if till > since:
        return current not in range(since, till)
    else:
        return not (current in range(since, 25) or current in range(-1, till))


def get_pcm_from_wav(wav_path):
    """
    从 wav 文件中读取 pcm

    :param wav_path: wav 文件路径
    :returns: pcm 数据
    """
    wav = wave.open(wav_path, "rb")
    return wav.readframes(wav.getnframes())