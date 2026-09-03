import pygame

import os
from sys import exit
from enum import Enum

# Initialize pygame
pygame.init()

# Paths
folder = os.path.dirname(__file__)
img = os.path.join(folder, "img")

player_path = os.path.join(img, "player")
enemy_path = os.path.join(img, "enemy")

player_idle_path = os.path.join(player_path, "Idle")
player_run_path = os.path.join(player_path, "Run")

enemy_idle_path = os.path.join(enemy_path, "Idle")
enemy_run_path = os.path.join(enemy_path, "Run")

class State(Enum):
    IDLE = 0
    RUN = 1
    JUMP = 2
    DEATH = 3


class Soldier(pygame.sprite.Sprite):
    soldier_list = []

    def __init__(self, char_type, x, y, scale, speed):
        pygame.sprite.Sprite.__init__(self)

        self.char_type = char_type

        self.update_time = pygame.time.get_ticks()

        self.animation_list = []
        self.animation_list.append(self._load_frames(State.IDLE, scale)) # State 0
        self.animation_list.append(self._load_frames(State.RUN, scale)) # State 1

        self.frame_index = 0
        self.image = self.animation_list[State.IDLE.value][self.frame_index]

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        self.state = State.IDLE
        self.flip = False

        self.moving_right = False
        self.moving_left = False

        self.speed = speed

        Soldier.soldier_list.append(self)

    def draw(self, screen):
        ANIMATION_COOLDOWN = 100

        # If enough time has passed between last animation frame
        if pygame.time.get_ticks() - self.update_time >= ANIMATION_COOLDOWN:
            frame_count = 0
            frame_count = len(self.animation_list[self.state.value])

            # Reset frame index at end of cycle
            if self.frame_index < frame_count - 1: self.frame_index += 1
            else: self.frame_index = 0

            # Update image
            self.image = self.animation_list[self.state.value][self.frame_index]

            # Flip sprite in case of moving in opposite direction
            if self.moving_left: self.flip = True
            elif self.moving_right: self.flip = False

            self.image = pygame.transform.flip(self.image, self.flip, False)

            self.update_time = pygame.time.get_ticks()

        screen.blit(self.image, self.rect)

    def move(self):
        # Update position
        if self.moving_right: self.rect.x += self.speed
        elif self.moving_left: self.rect.x -= self.speed

        # Update state
        if self.moving_left or self.moving_right: 
            self.update_animation(State.RUN)
        elif not (self.moving_left or self.moving_right):
            self.update_animation(State.IDLE)

    def update_animation(self, new_state):
        if self.state != new_state:
            self.state = new_state
            self.frame_index = 0
            self.update = pygame.time.get_ticks()

    # Get total files in path directory
    def _file_count(self, path):
        return sum(1 for file in os.listdir(path) if os.path.isfile(os.path.join(path, file)))

    # Load files depending on state and player type
    def _load_frames(self, state, scale):
        frame_list = []
        path = ""

        # Get path
        if state == State.IDLE and self.char_type == "player": path = player_idle_path
        elif state == State.RUN and self.char_type == "player": path = player_run_path

        elif state == State.IDLE and self.char_type == "enemy": path = enemy_idle_path
        elif state == State.RUN and self.char_type == "enemy": path = enemy_run_path 

        # Get file count
        frame_count = self._file_count(path)

        # Go through each image (file) in path directory and add it to list
        for i in range(frame_count):
            frame = pygame.image.load(os.path.join(path, f"{i}.png")).convert_alpha()
            frame = pygame.transform.scale(frame, (int(frame.get_width() * scale), int(frame.get_height() * scale)))

            frame_list.append(frame)

        return frame_list


# Screen and clock info
SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(0.8 * SCREEN_WIDTH)

x = 200
y = 400

scale = 2.5

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Sidescroller")

clock = pygame.Clock()
FPS = 60

# Soldiers
SPEED = 10

Player1 = Soldier("player", x, y, scale, SPEED)
Player2 = Soldier("enemy", x + 100, y, scale, SPEED)

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        if event.type == pygame.KEYDOWN:
            if (event.key == pygame.K_d):
                Player1.moving_right = True
            if (event.key == pygame.K_a):
                Player1.moving_left = True

        if event.type == pygame.KEYUP:
            if (event.key == pygame.K_d):
                Player1.moving_right = False
            if (event.key == pygame.K_a):
                Player1.moving_left = False

    screen.fill((0, 0, 0))
    
    Player1.move()

    Player1.draw(screen)
    Player2.draw(screen)

    pygame.display.flip()

    clock.tick(FPS)