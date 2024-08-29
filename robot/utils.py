import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import time
import wave
import _thread as thread
import numpy as np
import pvporcupine
import pyaudio

from robot import config, constants, logging

is_recordable = True
do_not_bother = False

logger = logging.getLogger(__name__)


def getPunctuations():
    return [".", "。", "?", "？", "!", "！", "\n"]


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
        # keywords=keywords  # 默认关键词也可以用
    )

    audio = pyaudio.PyAudio()
    info = audio.get_host_api_info_by_index(0)
    logger.info(info)
    # 打开麦克风流
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=porcupine.sample_rate,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )
    voice_data = []
    frames = []
    flag = False  # 开始录音节点
    stat = True  # 判断是否继续录音
    stat2 = False  # 判断声音小了
    mindb = 2000  # 最小声音，大于则开始录音，否则结束
    delayTime = 2  # 小声1.3秒后自动终止
    tempnum = 0  # tempnum、tempnum2、tempnum3为时间
    tempnum2 = 0
    while stat:
        data = stream.read(porcupine.frame_length, exception_on_overflow=False)
        audio_data = np.frombuffer(data, dtype=np.short)
        frames.append(audio_data)
        temp = np.max(audio_data)
        if temp > mindb and flag == False:
            flag = True
            print("开始录音")
            tempnum2 = tempnum

        if flag:

            if (temp < mindb and stat2 == False):
                stat2 = True
                tempnum2 = tempnum
                print("声音小，且之前是是大的或刚开始，记录当前点")
            if (temp > mindb):
                stat2 = False
                tempnum2 = tempnum
                # 刷新

            if (tempnum > tempnum2 + delayTime * 15 and stat2 == True):
                print("间隔%.2lfs后开始检测是否还是小声" % delayTime)
                if (stat2 and temp < mindb):
                    stat = False
                    # 还是小声，则stat=True
                    print("小声！")
                else:
                    stat2 = False
                    print("大声！")

        print(str(temp) + "      " + str(tempnum))
        tempnum = tempnum + 1
        if tempnum > 150:  # 超时直接退出
            stat = False

    # 关闭流和清理
    stream.stop_stream()
    stream.close()
    audio.terminate()
    porcupine.delete()

    # 返回录音数据（例如，可以将其保存到文件或进一步处理）
    # logger.info(frames)
    if frames:
        return frames
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


def stripPunctuation(s):
    """
    移除字符串末尾的标点
    """
    punctuations = [',', '，', '.', '。', '?']
    if any(s.endswith(p) for p in punctuations):
        s = s[:-1]
    return s


def getCache(msg):
    """ 获取缓存的语音 """
    md5 = hashlib.md5(msg.encode('utf-8')).hexdigest()
    mp3_cache = os.path.join(constants.TEMP_PATH, md5 + '.mp3')
    wav_cache = os.path.join(constants.TEMP_PATH, md5 + '.wav')
    if os.path.exists(mp3_cache):
        return mp3_cache
    elif os.path.exists(wav_cache):
        return wav_cache
    return None


def saveCache(voice, msg):
    """ 获取缓存的语音 """
    foo, ext = os.path.splitext(voice)
    md5 = hashlib.md5(msg.encode('utf-8')).hexdigest()
    target = os.path.join(constants.TEMP_PATH, md5 + ext)
    shutil.copyfile(voice, target)
    return target


def lruCache():
    """ 清理最近未使用的缓存 """

    def run(*args):
        if config.get('/lru_cache/enable', True):
            days = config.get('/lru_cache/days', 7)
            subprocess.run('find . -name "*.mp3" -atime +%d -exec rm {} \;' % days, cwd=constants.TEMP_PATH, shell=True)

    thread.start_new_thread(run, ())


def write_temp_file(data, suffix, mode='w+b'):
    """
    写入临时文件

    :param data: 数据
    :param suffix: 后缀名
    :param mode: 写入模式，默认为 w+b
    :returns: 文件保存后的路径
    """
    with tempfile.NamedTemporaryFile(mode=mode, suffix=suffix, delete=False) as f:
        f.write(data)
        tmpfile = f.name
    return tmpfile
