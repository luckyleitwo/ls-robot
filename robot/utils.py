import os
import re
import shutil
import time
import wave
import _thread as thread

import numpy as np
import pvporcupine
import pyaudio

from robot import config, constants

is_recordable = True
do_not_bother = False


def getPunctuations():
    return [",", "，", ".", "。", "?", "？", "!", "！", "\n"]


def setRecordable(value):
    """设置是否可以开始录制语音"""
    global is_recordable
    is_recordable = value


def is_proper_time():
    """是否合适时间"""
    global do_not_bother
    if do_not_bother:
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


def clean():
    """清理垃圾数据"""
    temp = constants.TEMP_PATH
    temp_files = os.listdir(temp)
    for f in temp_files:
        if os.path.isfile(os.path.join(temp, f)) and re.match(
                r"output[\d]*\.wav", os.path.basename(f)
        ):
            os.remove(os.path.join(temp, f))


# 替换原有的 snowboydecoder 监听逻辑
def listen_for_hotword():
    # 读取配置文件或其他来源的参数
    recording_timeout = config.get("recording_timeout", 5) * 4

    # 设置 Porcupine 的热词模型和其他参数
    # 从配置中读取参数
    access_key = config.get("/porcupine/access_key")
    keyword_paths = config.get("/porcupine/keyword_paths", [])  # 自定义关键词模型路径
    keywords = config.get("/porcupine/keywords", ["porcupine"])
    #  porcupine = pvporcupine.create(
    #         access_key=access_key,
    #         keyword_paths=["/Users/shenglei/ls/qil-robot/wukong/"+keyword_paths[0]],  # 自定义模型路径
    #         # keywords=keywords  # 默认关键词也可以用
    #     )
    # 初始化 Porcupine 实例
    porcupine = pvporcupine.create(
        access_key=access_key,
        keyword_paths=[constants.getConfigData(kw) for kw in keyword_paths],
        keywords=keywords  # 默认关键词也可以用
    )

    audio = pyaudio.PyAudio()

    # 打开麦克风流
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=porcupine.sample_rate,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )

    voice_data = []
    timeout = 0
    while timeout < recording_timeout:
        # 从麦克风读取数据
        pcm = np.frombuffer(stream.read(porcupine.frame_length), dtype=np.int16)
        # 使用 Porcupine 检测热词
        keyword_index = porcupine.process(pcm)
        if keyword_index >= 0:
            print("Hotword detected!")
            break

        voice_data.append(pcm)
        timeout += porcupine.frame_length / porcupine.sample_rate

    # 关闭流和清理
    stream.stop_stream()
    stream.close()
    audio.terminate()
    porcupine.delete()

    # 返回录音数据（例如，可以将其保存到文件或进一步处理）
    if voice_data:
        return np.concatenate(voice_data)
    return None


def check_and_delete(fp, wait=0):
    """
    检查并删除文件/文件夹

    :param fp: 文件路径
    """

    def run():
        if wait > 0:
            time.sleep(wait)
        if isinstance(fp, str) and os.path.exists(fp):
            if os.path.isfile(fp):
                os.remove(fp)
            else:
                shutil.rmtree(fp)

    thread.start_new_thread(run, ())
