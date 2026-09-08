import os

import pygame

from config import BG, BLACK, GROUND, SCREEN_WIDTH


def file_count(path):
    if not os.path.isdir(path):
        return 0
    return sum(1 for file in os.listdir(path) if os.path.isfile(os.path.join(path, file)))


def draw_background(screen):
    screen.fill(BG)
    pygame.draw.line(screen, BLACK, (0, GROUND), (SCREEN_WIDTH, GROUND))
