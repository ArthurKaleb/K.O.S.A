import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame

pygame.mixer.init()
pygame.mixer.music.load("bemvindo4.mp3")
pygame.mixer.music.play()

while pygame.mixer.music.get_busy():
    pass