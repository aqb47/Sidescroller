import os
from enum import Enum

import pygame

from config import (
    BULLET_DAMAGE,
    BULLET_SPEED,
    EXPLOSION_PATH,
    GRENADE_DAMAGE,
    GRENADE_SPEED,
    HEALTH_GIVEN,
    ICON_PATH,
    INITIAL_BULLETS,
    INITIAL_GRENADES,
    PLAYER_DEATH_PATH,
    PLAYER_IDLE_PATH,
    PLAYER_JUMP_PATH,
    PLAYER_RUN_PATH,
    ENEMY_DEATH_PATH,
    ENEMY_IDLE_PATH,
    ENEMY_JUMP_PATH,
    ENEMY_RUN_PATH,
    BULLETS_GIVEN,
    GRENADES_GIVEN,
    GROUND,
    SCREEN_WIDTH,
    GRAVITY,
)
from utils import file_count


class SoldierState(Enum):
    IDLE = 0
    RUN = 1
    JUMP = 2
    DEATH = 3


class ItemType(Enum):
    AMMO_BOX = 0
    GRENADE_BOX = 1
    HEALTH_BOX = 2


class ItemBox(pygame.sprite.Sprite):
    item_boxes = []
    loaded = False
    bullets_given = BULLETS_GIVEN
    grenades_given = GRENADES_GIVEN
    health_given = HEALTH_GIVEN

    def __init__(self, x, y, item_type):
        super().__init__()

        self.x = x
        self.y = y
        self.item_type = item_type

        if not ItemBox.loaded:
            self.load()
            ItemBox.loaded = True

        self.image = ItemBox.item_boxes[self.item_type.value]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = y

    def load(self):
        grenade_box_image = pygame.image.load(os.path.join(ICON_PATH, "grenade_box.png"))
        health_box_image = pygame.image.load(os.path.join(ICON_PATH, "health_box.png"))
        ammo_box_image = pygame.image.load(os.path.join(ICON_PATH, "ammo_box.png"))

        ItemBox.item_boxes.append(ammo_box_image)
        ItemBox.item_boxes.append(grenade_box_image)
        ItemBox.item_boxes.append(health_box_image)

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def update(self, player_group):
        player_collisions = pygame.sprite.spritecollide(self, player_group, False)

        for player in player_collisions:
            item_type = self.item_type
            self.kill()

            if item_type == ItemType.AMMO_BOX:
                player.bullets += ItemBox.bullets_given
            elif item_type == ItemType.GRENADE_BOX:
                player.grenades += ItemBox.grenades_given
            elif item_type == ItemType.HEALTH_BOX:
                player.health += ItemBox.health_given


class Grenade(pygame.sprite.Sprite):
    animation_list = []
    loaded = False

    def __init__(self, x, y, moving_right, speed):
        super().__init__()
        self.explode = False

        if not Grenade.loaded:
            Grenade.animation_list = self._load_frames()
            Grenade.loaded = True

        self.frame_index = 0
        self.image = pygame.image.load(os.path.join(ICON_PATH, "grenade.png")).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.draw_time = pygame.time.get_ticks()
        self.flip = not moving_right
        self.speed = speed
        self.vel_y = -self.speed * 2

    def _load_frames(self):
        frame_list = []
        frame_count = file_count(EXPLOSION_PATH)

        for i in range(frame_count):
            image = pygame.image.load(os.path.join(EXPLOSION_PATH, f"{i}.png")).convert_alpha()
            frame_list.append(image)

        return frame_list

    def draw(self, screen):
        animation_cooldown = 100

        if self.explode:
            if self.frame_index < len(Grenade.animation_list):
                if pygame.time.get_ticks() - self.draw_time >= animation_cooldown:
                    self.image = Grenade.animation_list[self.frame_index]
                    self.frame_index += 1
                    self.draw_time = pygame.time.get_ticks()
            else:
                self.kill()

        screen.blit(self.image, self.rect)

    def update(self, enemy_group):
        if not self.explode:
            dx = 0
            dy = 0

            dx += self.speed if not self.flip else -self.speed
            dy += self.vel_y

            self.vel_y += GRAVITY

            if self.rect.top + dy > GROUND:
                self.explode = True
            else:
                self.rect.x += dx
                self.rect.y += dy

            enemies_collided = pygame.sprite.spritecollide(self, enemy_group, False)
            for enemy in enemies_collided:
                if enemy.is_alive:
                    self.explode = True
                    enemy.health -= GRENADE_DAMAGE


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, moving_right, speed):
        super().__init__()

        self.image = pygame.image.load(os.path.join(ICON_PATH, "bullet.png")).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.flip = not moving_right
        self.speed = speed

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def update(self, enemy_group):
        dx = self.speed if not self.flip else -self.speed

        if self.rect.left > SCREEN_WIDTH or self.rect.right < 0:
            self.kill()
            return

        self.rect.x += dx

        enemies_collided = pygame.sprite.spritecollide(self, enemy_group, False)
        for enemy in enemies_collided:
            if enemy.is_alive:
                self.kill()
                enemy.health -= BULLET_DAMAGE


class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed):
        super().__init__()

        self.is_alive = True
        self.dying = False

        self.health = 100
        self.max_health = self.health

        self.bullets = INITIAL_BULLETS
        self.grenades = INITIAL_GRENADES

        self.char_type = char_type
        self.update_time = pygame.time.get_ticks()
        self.shoot_time = pygame.time.get_ticks()
        self.animation_list = []

        self.animation_list.append(self._load_frames(SoldierState.IDLE, scale))
        self.animation_list.append(self._load_frames(SoldierState.RUN, scale))
        self.animation_list.append(self._load_frames(SoldierState.JUMP, scale))
        self.animation_list.append(self._load_frames(SoldierState.DEATH, scale))

        self.frame_index = 0
        self.image = self.animation_list[SoldierState.IDLE.value][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.midbottom = (x, y)

        self.state = SoldierState.IDLE
        self.flip = False

        self.moving_right = False
        self.moving_left = False
        self.moving_down = False

        self.jumping = False
        self.in_air = False

        self.speed = speed
        self.vel_y = 0

    def throw_grenade(self, grenade_group):
        if self.grenades <= 0:
            return

        grenade_pos_x = self.rect.topright[0] + 10 if not self.flip else self.rect.topleft[0] - 10
        grenade_pos_y = self.rect.topright[1] + 10

        grenade = Grenade(grenade_pos_x, grenade_pos_y, not self.flip, GRENADE_SPEED)
        grenade_group.add(grenade)
        self.grenades -= 1

    def shoot(self, bullet_group):
        if self.bullets <= 0:
            return

        shoot_cooldown = 200
        if pygame.time.get_ticks() - self.shoot_time >= shoot_cooldown:
            gun_pos_x = self.rect.right + 10 if not self.flip else self.rect.left - 10
            bullet = Bullet(gun_pos_x, self.rect.centery, not self.flip, BULLET_SPEED)
            bullet_group.add(bullet)
            self.shoot_time = pygame.time.get_ticks()
            self.bullets -= 1

    def draw(self, screen):
        animation_cooldown = 100

        if pygame.time.get_ticks() - self.update_time >= animation_cooldown:
            frame_count = len(self.animation_list[self.state.value])

            if self.frame_index < frame_count - 1:
                self.frame_index += 1
            else:
                if self.dying:
                    self.dying = False

                if not self.is_alive and not self.dying:
                    self.frame_index = frame_count - 1
                else:
                    self.frame_index = 0

            self.image = self.animation_list[self.state.value][self.frame_index]
            self.update_time = pygame.time.get_ticks()

        self.image = pygame.transform.flip(self.animation_list[self.state.value][self.frame_index], self.flip, False)
        screen.blit(self.image, self.rect)

    def update(self):
        if self.health <= 0 and self.is_alive:
            self.is_alive = False
            self.dying = True

        dx = 0
        dy = 0

        if self.moving_right:
            dx += self.speed
        elif self.moving_left:
            dx -= self.speed

        if self.moving_left:
            self.flip = True
        elif self.moving_right:
            self.flip = False

        if self.jumping:
            self.vel_y = -self.speed * 2
            self.jumping = False

        self.vel_y += GRAVITY
        if self.moving_down:
            self.vel_y += 0.25 * self.speed

        dy += self.vel_y

        if self.rect.bottom + dy >= GROUND:
            dy = GROUND - self.rect.bottom
            self.vel_y = 0
            self.in_air = False

        self.rect.x += dx
        self.rect.y += dy

        if not self.is_alive:
            self.update_animation(SoldierState.DEATH)
        elif self.in_air:
            self.update_animation(SoldierState.JUMP)
        else:
            if self.moving_left or self.moving_right:
                self.update_animation(SoldierState.RUN)
            else:
                self.update_animation(SoldierState.IDLE)

    def update_animation(self, new_state):
        if self.state != new_state:
            self.state = new_state
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()
            self.image = self.animation_list[self.state.value][self.frame_index]

    def _load_frames(self, state, scale):
        frame_list = []
        path = ""

        if state == SoldierState.IDLE and self.char_type == "player":
            path = PLAYER_IDLE_PATH
        elif state == SoldierState.RUN and self.char_type == "player":
            path = PLAYER_RUN_PATH
        elif state == SoldierState.JUMP and self.char_type == "player":
            path = PLAYER_JUMP_PATH
        elif state == SoldierState.DEATH and self.char_type == "player":
            path = PLAYER_DEATH_PATH
        elif state == SoldierState.IDLE and self.char_type == "enemy":
            path = ENEMY_IDLE_PATH
        elif state == SoldierState.RUN and self.char_type == "enemy":
            path = ENEMY_RUN_PATH
        elif state == SoldierState.JUMP and self.char_type == "enemy":
            path = ENEMY_JUMP_PATH
        elif state == SoldierState.DEATH and self.char_type == "enemy":
            path = ENEMY_DEATH_PATH

        frame_count = file_count(path)

        for i in range(frame_count):
            frame = pygame.image.load(os.path.join(path, f"{i}.png")).convert_alpha()
            frame = pygame.transform.scale(frame, (int(frame.get_width() * scale), int(frame.get_height() * scale)))
            frame_list.append(frame)

        return frame_list
