from server import serverMain

import pvporcupine
import pyaudio
import numpy as np

# if __name__ == "__main__":
#     serverMain.app.run(host='0.0.0.0', port=2888, debug=True)

# 配置 Porcupine
keyword_path = "./static/huanx_zh_mac_v3_0_0.ppn"  # 预训练的唤醒词模型路径
access_key = "KLtEYTJi1zHgUyzuZD0t0juvn1SpFEIYz4DSblInl/kFSeLKOAcuqg=="  # 你的 Picovoice 访问密钥

# 初始化 Porcupine
porcupine = pvporcupine.create(keywords=[keyword_path], access_key=access_key)

# 初始化 PyAudio
p = pyaudio.PyAudio()
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=porcupine.sample_rate,
    input=True,
    frames_per_buffer=porcupine.frame_length
)

print("Listening for wake word...")

try:
    while True:
        # 读取音频数据
        audio_data = stream.read(porcupine.frame_length)
        audio_data = np.frombuffer(audio_data, dtype=np.int16)

        # 处理音频数据
        keyword_index = porcupine.process(audio_data)

        # 检测唤醒词
        if keyword_index >= 0:
            print(f"Detected keyword: {keyword_index}")

except KeyboardInterrupt:
    print("Interrupted")

finally:
    # 清理资源
    stream.stop_stream()
    stream.close()
    p.terminate()
    porcupine.delete()