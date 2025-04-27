import pygame
from sys import exit
import random
import math
from settings import *
import warnings
pygame.init()


class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.rotozoom(
            pygame.image.load("Premium top-down shooter asset pack/Zombie.png")
                   .convert_alpha(),
            0, player_size
        )
        self.rect = self.image.get_rect()
        # spawn somewhere on the map
        x = random.randint(0, MAP_WIDTH)
        y = random.randint(0, MAP_HEIGHT)
        self.pos = vector(x, y)
        self.rect.topleft = self.pos

        # wander variables
        self.speed = 80  # pixels per second
        self._pick_new_direction()

    def _pick_new_direction(self):
        # choose a random unit vector
        dx, dy = random.uniform(-1, 1), random.uniform(-1, 1)
        v = vector(dx, dy)
        if v.length_squared() == 0:
            v = vector(1, 0)
        self.direction = v.normalize()

        # next time (in ms) to pick a new dir
        self.next_change = pygame.time.get_ticks() + random.randint(500, 2000)

    def update(self, dt):
        now = pygame.time.get_ticks()
        if now >= self.next_change:
            self._pick_new_direction()

        # move
        self.pos += self.direction * self.speed * dt

        # keep inside map bounds
        self.pos.x = max(0, min(self.pos.x, MAP_WIDTH - self.rect.width))
        self.pos.y = max(0, min(self.pos.y, MAP_HEIGHT - self.rect.height))

        self.rect.topleft = self.pos

Enemy_count = 15 
enemies = pygame.sprite.group()
for i in range(Enemy_count):
    enemies.add(Enemy())




