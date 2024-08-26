import pygame
import yamlServer

# 播放音频
def play(file_name):
    pygame.mixer.init()
    pygame.mixer.music.load(file_name)
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play()


# def saveFile(TEXT, file_name):
#     yamlServer.config