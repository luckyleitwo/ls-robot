import threading

import pyaudio
from pydub import AudioSegment
from threading import Thread
import time


class AudioPlayer:
    def __init__(self, chunk_size=1024):
        self.chunk_size = chunk_size
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.playing = False
        self.audio_queue = []
        self.lock = threading.Lock()

    def start_stream(self):
        self.stream = self.audio.open(format=pyaudio.paInt16,
                                      channels=2,
                                      rate=44100,
                                      output=True,
                                      frames_per_buffer=self.chunk_size)
        self.playing = True
        Thread(target=self._play_audio).start()

    def stop_stream(self):
        self.playing = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()

    def _play_audio(self):
        while self.playing:
            if self.audio_queue:
                audio_data = self.audio_queue.pop(0)
                self.stream.write(audio_data)
            else:
                time.sleep(0.1)

    def append_audio(self, audio_segment):
        audio_data = audio_segment.raw_data
        with self.lock:
            self.audio_queue.append(audio_data)


def load_audio(filename):
    audio = AudioSegment.from_file(filename)
    audio = audio.set_frame_rate(44100).set_channels(2).set_sample_width(2)
    return audio

# Example usage
player = AudioPlayer()

# Start playback stream
player.start_stream()

# Load and append initial audio
initial_audio = load_audio('/Users/shenglei/ls/ls-robot/temp/d649879cc44b4a0a9dc7b885fd1097e1.mp3')
player.append_audio(initial_audio)

# Simulate appending new audio while playing
# time.sleep(5)  # Play for 5 seconds

new_audio = load_audio('/Users/shenglei/ls/ls-robot/temp/9c83f4e5e55140dc803043f36212b64a.mp3')
player.append_audio(new_audio)

new_audios = load_audio('/Users/shenglei/ls/ls-robot/temp/e1ff844ed0874de19ceedb3d78c884c1.mp3')
player.append_audio(new_audios)

# Keep playing for a while longer
# time.sleep(10)

# Stop playback
player.stop_stream()