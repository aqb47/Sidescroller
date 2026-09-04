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
player_jump_path = os.path.join(player_path, "Jump")
player_death_path = os.path.join(player_path, "Death")

enemy_idle_path = os.path.join(enemy_path, "Idle")
enemy_run_path = os.path.join(enemy_path, "Run")
enemy_jump_path = os.path.join(enemy_path, "Jump")
enemy_death_path = os.path.join(enemy_path, "Death")

icon_path = os.path.join(img, "icons")

# Game variables
GRAVITY = 1
FPS = 60

BG = (144, 201, 120)
BLACK = (0, 0, 0)

# Screen and clock info
SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(0.8 * SCREEN_WIDTH)

GROUND = 400

x = 200
y = GROUND

scale = 2.5

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Sidescroller")

clock = pygame.Clock()

# Speeds
SPEED = 10
BULLET_SPEED = 5

# Groups
bullet_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()


def draw_background(screen):
    screen.fill(BG)
    pygame.draw.line(screen, BLACK, (0, GROUND), (SCREEN_WIDTH, GROUND))


class State(Enum):
    IDLE = 0
    RUN = 1
    JUMP = 2
    DEATH = 3


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, moving_right, speed):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.image.load(os.path.join(icon_path, "bullet.png")).convert_alpha()
        self.rect = self.image.get_rect()

        self.rect.center = (x, y)
        self.flip = not moving_right

        self.speed = speed

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def update(self):
        dx = 0
        dx += self.speed if not self.flip else -self.speed

        enemies_collided = pygame.sprite.spritecollide(self, enemy_group, False)

        for enemy in enemies_collided:
            if enemy.is_alive:
                self.kill()
                enemy.health -= 25

        if self.rect.left > SCREEN_WIDTH or self.rect.right < 0:
            self.kill()

        self.rect.x += dx


class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed):
        pygame.sprite.Sprite.__init__(self)

        self.is_alive = True
        self.dying = False

        self.health = 100
        self.max_health = self.health

        self.char_type = char_type

        self.update_time = pygame.time.get_ticks()
        self.shoot_time = pygame.time.get_ticks()

        self.animation_list = []
        self.animation_list.append(self._load_frames(State.IDLE, scale)) # State 0
        self.animation_list.append(self._load_frames(State.RUN, scale)) # State 1
        self.animation_list.append(self._load_frames(State.JUMP, scale)) # State 2
        self.animation_list.append(self._load_frames(State.DEATH, scale)) # State 3

        self.frame_index = 0
        self.image = self.animation_list[State.IDLE.value][self.frame_index]

        self.rect = self.image.get_rect()
        self.rect.midbottom = (x, y)

        self.state = State.IDLE
        self.flip = False

        self.moving_right = False
        self.moving_left = False
        self.moving_down = False

        self.jumping = False
        self.in_air = False

        self.speed = speed
        self.vel_y = 0

    def shoot(self):
        SHOOTING_COOLDOWN = 200

        if pygame.time.get_ticks() - self.shoot_time >= SHOOTING_COOLDOWN:
            gun_pos_x = self.rect.right + 10 if not self.flip else self.rect.left - 10

            bullet = Bullet(gun_pos_x, self.rect.centery, not self.flip, BULLET_SPEED)
            bullet_group.add(bullet)

            self.shoot_time = pygame.time.get_ticks()

    def draw(self, screen):
        ANIMATION_COOLDOWN = 100

        # If enough time has passed between last animation frame
        if pygame.time.get_ticks() - self.update_time >= ANIMATION_COOLDOWN:
            frame_count = len(self.animation_list[self.state.value])

            # Reset frame index at end of cycle
            if self.frame_index < frame_count - 1: self.frame_index += 1
            else:
                if self.dying: self.dying = False 

                if not self.is_alive and not self.dying: self.frame_index = frame_count - 1
                else: self.frame_index = 0

            # Update image
            self.image = self.animation_list[self.state.value][self.frame_index]

            self.update_time = pygame.time.get_ticks()

            # Flip sprite in case of moving in opposite direction
            if self.moving_left: self.flip = True
            elif self.moving_right: self.flip = False

            self.image = pygame.transform.flip(self.image, self.flip, False)

        screen.blit(self.image, self.rect)

    def update(self):
        if self.health <= 0 and self.is_alive: 
            self.is_alive = False
            self.dying = True

        # Update position
        dx = 0
        dy = 0

        # Left/right movement
        if self.moving_right: dx += self.speed
        elif self.moving_left: dx -= self.speed

        # Jumping movement
        if self.jumping: self.vel_y = -self.speed * 2 # Initial jumping velocity

        # Gravity
        self.vel_y += GRAVITY
        if self.moving_down: self.vel_y += 0.25 * self.speed # Sort of like a stomp

        dy += self.vel_y

        if self.rect.bottom + dy >= GROUND: # Collision with ground
            dy = GROUND - self.rect.bottom
            self.vel_y = 0
            self.in_air = False
        
        # Final change of x,y pos
        self.rect.x += dx
        self.rect.y += dy

        # Update state
        if not self.is_alive:
            self.update_animation(State.DEATH)
        else:
            if (self.moving_left or self.moving_right):
                self.update_animation(State.RUN)
            elif not (self.moving_left or self.moving_right):
                self.update_animation(State.IDLE)

            if self.in_air:
                self.update_animation(State.JUMP)
                self.jumping = False


    def update_animation(self, new_state):
        if self.state != new_state:
            self.state = new_state
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

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
        elif state == State.JUMP and self.char_type == "player": path = player_jump_path
        elif state == State.DEATH and self.char_type == "player": path = player_death_path

        elif state == State.IDLE and self.char_type == "enemy": path = enemy_idle_path
        elif state == State.RUN and self.char_type == "enemy": path = enemy_run_path 
        elif state == State.JUMP and self.char_type == "enemy": path = enemy_jump_path
        elif state == State.DEATH and self.char_type == "enemy": path = enemy_death_path

        # Get file count
        frame_count = self._file_count(path)

        # Go through each image (file) in path directory and add it to list
        for i in range(frame_count):
            frame = pygame.image.load(os.path.join(path, f"{i}.png")).convert_alpha()
            frame = pygame.transform.scale(frame, (int(frame.get_width() * scale), int(frame.get_height() * scale)))

            frame_list.append(frame)

        return frame_list


# Soldiers
Player1 = Soldier("player", x, y, scale, SPEED)
Player2 = Soldier("enemy", x + 100, y, scale, SPEED)

enemy_group.add(Player2)

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                Player1.moving_right = True
            if event.key == pygame.K_a:
                Player1.moving_left = True

            if event.key == pygame.K_s:
                if Player1.in_air:
                    Player1.moving_down = True

            if event.key == pygame.K_SPACE:
                if not Player1.in_air:
                    Player1.jumping = True
                    Player1.in_air = True

            if event.key == pygame.K_l:
                Player1.shoot()

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_d:
                Player1.moving_right = False
            if event.key == pygame.K_a:
                Player1.moving_left = False

            if event.key == pygame.K_s:
                Player1.moving_down = False

    draw_background(screen)

    # Update entities
    Player1.update()
    bullet_group.update()
    Player2.update()

    # Draw them on screen
    Player1.draw(screen)
    Player2.draw(screen)
    bullet_group.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)