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
        self.image = pygame.transform.rotozoom(pygame.image.load("Premium top-down shooter asset pack\Zombie.png").convert_alpha(), 0, player_size)
        self.rect = self.image.get_rect()
        self.rect.topleft = (random.randint(0, MAP_WIDTH), random.randint(0, MAP_HEIGHT))  # position on screen
        self.pos = pygame.math.Vector2(self.rect.topleft)
    def movementinputs(self):
        self.move_speedx = 0
        self.move_speedy = 0
        input = pygame.key.get_pressed()
        if input[pygame.K_w]:
            self.move_speedy -= player_speed
        elif input[pygame.K_a]:
            self.move_speedx -= player_speed
        elif input[pygame.K_s]:
            self.move_speedy += player_speed
        elif input[pygame.K_d]:
            self.move_speedx += player_speed




