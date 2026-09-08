import pygame

from config import (
    FPS,
    GROUND,
    PLAYER_SCALE,
    PLAYER_START_X,
    PLAYER_START_Y,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SPEED,
)
from entities import Bullet, Grenade, ItemBox, ItemType, Soldier
from utils import draw_background


class Game:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Sidescroller")

        self.clock = pygame.Clock()

        self.player_group = pygame.sprite.Group()
        self.enemy_group = pygame.sprite.Group()

        self.bullet_group = pygame.sprite.Group()
        self.grenade_group = pygame.sprite.Group()

        self.item_box_group = pygame.sprite.Group()

        self.player = Soldier("player", PLAYER_START_X, PLAYER_START_Y, PLAYER_SCALE, SPEED)
        self.enemies = [
            Soldier("enemy", PLAYER_START_X + 100, PLAYER_START_Y, PLAYER_SCALE, SPEED),
            Soldier("enemy", PLAYER_START_X + 200, PLAYER_START_Y, PLAYER_SCALE, SPEED),
        ]

        self.item_box = ItemBox(400, GROUND, ItemType.AMMO_BOX)

        self.player_group.add(self.player)
        self.enemy_group.add(*self.enemies)
        self.item_box_group.add(self.item_box)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_d:
                    self.player.moving_right = True
                if event.key == pygame.K_a:
                    self.player.moving_left = True

                if event.key == pygame.K_s:
                    if self.player.in_air:
                        self.player.moving_down = True
                if event.key == pygame.K_SPACE:
                    if not self.player.in_air:
                        self.player.jumping = True
                        self.player.in_air = True

                if event.key == pygame.K_e:
                    self.player.shoot(self.bullet_group)
                if event.key == pygame.K_q:
                    self.player.throw_grenade(self.grenade_group)

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_d:
                    self.player.moving_right = False
                if event.key == pygame.K_a:
                    self.player.moving_left = False

                if event.key == pygame.K_s:
                    self.player.moving_down = False

    def update(self):
        for player in self.player_group:
            player.update()
        for enemy in self.enemy_group:
            enemy.update()

        for bullet in self.bullet_group:
            bullet.update(self.enemy_group)
        for grenade in self.grenade_group:
            grenade.update(self.enemy_group)

        for box in self.item_box_group:
            box.update(self.player_group)

    def draw(self):
        draw_background(self.screen)

        for player in self.player_group:
            player.draw(self.screen)
        for enemy in self.enemy_group:
            enemy.draw(self.screen)

        for bullet in self.bullet_group:
            bullet.draw(self.screen)
        for grenade in self.grenade_group:
            grenade.draw(self.screen)

        for box in self.item_box_group:
            box.draw(self.screen)

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
