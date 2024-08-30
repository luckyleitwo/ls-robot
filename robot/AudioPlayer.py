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
