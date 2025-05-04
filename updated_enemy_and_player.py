######## Hey guys. This should make it so that the player can take damage from the enemy bugs. The bugs should also die after 
######## getting shot 5 times. 



import pygame
import sys
import math
import warnings
import random

# Starts up pygame
pygame.init()
warnings.filterwarnings("ignore", category=UserWarning, module="PIL.PngImagePlugin")

FPS = 100  # Caps the frames per second
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1000
MAP_WIDTH = 2000
MAP_HEIGHT = 2000
screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
background_pos = (0, 0)
player_start_pos = (600, 600)
player_size = .15
player_speed = 160
vector = pygame.math.Vector2
max_enemies = 5

# Screen set up
display = pygame.display.set_mode(screen_size)
pygame.display.set_caption("2D shooter")
clock = pygame.time.Clock()

background = pygame.transform.scale(
    pygame.image.load("Lords Of Pain/environment/ground.png.png").convert(),
    (MAP_WIDTH, MAP_HEIGHT)
)

play_button_img = pygame.transform.scale(
    pygame.image.load("Premium top-down shooter asset pack/Play Rect.png"),
    (300, 100)
)
quit_button_img = pygame.transform.scale(
    pygame.image.load("Premium top-down shooter asset pack/Quit Rect.png"),
    (300, 100)
)

crosshair = pygame.image.load(
    "Premium top-down shooter asset pack/crosshair.png"
)

game_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()

def draw_health_bar(surface, x, y, width, height, current, maximum):
    pygame.draw.rect(surface, (100, 0, 0), (x, y, width, height))
    ratio = max(current, 0) / maximum
    pygame.draw.rect(surface, (255, 0, 0), (x, y, width * ratio, height))
    pygame.draw.rect(surface, (0, 0, 0), (x, y, width, height), 2)

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.rotozoom(
            pygame.image.load(
                "Premium top-down shooter asset pack/Player with AK.png"
            ).convert_alpha(),
            0, player_size
        )
        self.rect = self.image.get_rect()
        self.pos = vector(player_start_pos)
        self.original_character = self.image
        self.hitbox = self.original_character.get_rect(
            center=(self.rect.width/2, self.rect.height/2)
        )
        self.max_health = 100
        self.health = self.max_health
        self.invincible = False
        self.invincibility_duration = 1000
        self.last_hit_time = 0

    def movementinputs(self):
        keys = pygame.key.get_pressed()
        self.move_speedx = 0
        self.move_speedy = 0
        if keys[pygame.K_w]: self.move_speedy -= player_speed
        if keys[pygame.K_a]: self.move_speedx -= player_speed
        if keys[pygame.K_s]: self.move_speedy += player_speed
        if keys[pygame.K_d]: self.move_speedx += player_speed
        if (keys[pygame.K_w] or keys[pygame.K_s]) and (keys[pygame.K_a] or keys[pygame.K_d]):
            self.move_speedx /= math.sqrt(2)
            self.move_speedy /= math.sqrt(2)

    def playermovement(self, between_frames):
        self.pos += vector(self.move_speedx, self.move_speedy) * between_frames
        self.hitbox.center = self.pos
        self.boundary('horizontal')
        self.boundary('vertical')
        self.rect.center = self.hitbox.center

    def rotation(self, cursor_pos):
        dx = cursor_pos[0] - SCREEN_WIDTH / 2
        dy = cursor_pos[1] - SCREEN_HEIGHT / 2
        angle = math.degrees(math.atan2(dy, dx))
        self.image = pygame.transform.rotate(self.original_character, -angle + 90)
        self.rect = self.image.get_rect(center=self.hitbox.center)

    def boundary(self, direction):
        if direction == 'horizontal':
            if self.hitbox.centerx < 152: self.hitbox.centerx = 152
            elif self.hitbox.centerx > 1929: self.hitbox.centerx = 1929
        elif direction == 'vertical':
            if self.hitbox.centery < 221: self.hitbox.centery = 221
            elif self.hitbox.centery > 1911: self.hitbox.centery = 1911
        self.pos = vector(self.hitbox.center)
        self.rect.center = self.hitbox.center

    def update(self, between_frames, cursor_pos):
        self.movementinputs()
        self.playermovement(between_frames)
        self.rotation(cursor_pos)

class Camera:
    def __init__(self):
        self.offset = vector()
        self.bg_rect = background.get_rect(topleft=background_pos)

    def move_bg(self):
        self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2
        self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2
        bg_offset = self.bg_rect.topleft - self.offset
        display.blit(background, bg_offset)
        for sprite in game_sprites:
            pos = sprite.rect.topleft - self.offset
            display.blit(sprite.image, pos)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, direction, speed=500, color=(255, 0, 0), radius=3):
        super().__init__()
        self.image = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect(center=pos)
        self.velocity = vector(direction).normalize() * speed

    def update(self, dt):
        self.rect.x += self.velocity.x * dt
        self.rect.y += self.velocity.y * dt
        if not display.get_rect().colliderect(self.rect):
            self.kill()

class Gun:
    def __init__(self, owner, clip_size, reload_time, cooldown_ms):
        self.owner = owner
        self.clip_size = clip_size
        self.ammo = clip_size
        self.reload_time = reload_time * 1000
        self.cooldown = cooldown_ms
        self.last_shot = 0
        self.is_reloading = False
        self.reload_start = 0

    def update(self):
        if self.is_reloading and pygame.time.get_ticks() - self.reload_start >= self.reload_time:
            self.ammo = self.clip_size
            self.is_reloading = False

    def reload(self):
        if not self.is_reloading and self.ammo < self.clip_size:
            self.is_reloading = True
            self.reload_start = pygame.time.get_ticks()

    def shoot(self, pos, direction, bullet_group):
        now = pygame.time.get_ticks()
        if self.is_reloading or self.ammo <= 0 or now - self.last_shot < self.cooldown:
            return
        self.last_shot = now
        self.ammo -= 1
        bullet_group.add(Bullet(pos, direction))

class AssaultRifle(Gun):
    def __init__(self, owner):
        super().__init__(owner, clip_size=30, reload_time=2.5, cooldown_ms=100)

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.rotozoom(
            pygame.image.load(
                "Premium top-down shooter asset pack/Bug_enemy.png"
            ).convert_alpha(),
            0, player_size
        )
        self.rect = self.image.get_rect()
        offset_x = random.randint(-100, 100)
        offset_y = random.randint(-100, 100)
        self.pos = vector(player_start_pos[0] + offset_x,
                          player_start_pos[1] + offset_y)
        self.rect.topleft = self.pos
        self.speed = 80
        self.max_health = 5
        self.health = self.max_health
        # initial direction (won't matter once follow logic kicks in)
        self.direction = vector(0, 0)

    def update(self, dt, placeholder):
        # follow the player
        to_player = player.pos - self.pos
        if to_player.length_squared() > 0:
            self.direction = to_player.normalize()
        self.pos += self.direction * self.speed * dt
        # clamp to map bounds
        self.pos.x = max(0, min(self.pos.x, MAP_WIDTH - self.rect.width))
        self.pos.y = max(0, min(self.pos.y, MAP_HEIGHT - self.rect.height))
        self.rect.topleft = self.pos

def handle_player_input(player, bullet_group, camera):
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = vector(pygame.mouse.get_pos()) + camera.offset
            direction = mouse_pos - player.rect.center
            player.gun.shoot(player.rect.center, direction, bullet_group)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            player.gun.reload()

def main_menu():
    # ... (unchanged) ...
    pass  # placeholder for your existing menu code

# set up
camera = Camera()
player = Player()
player.gun = AssaultRifle(player)
game_sprites.add(player)

# initial enemy
enemy = Enemy()
enemies.add(enemy)
game_sprites.add(enemy)

SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWN_EVENT, 100)

# main loop
game_running = True
while game_running:
    pygame.mouse.set_visible(False)
    dt = clock.tick(FPS) / 1000
    cursor = pygame.mouse.get_pos()

    handle_player_input(player, bullet_group, camera)
    camera.move_bg()
    game_sprites.update(dt, cursor)
    bullet_group.update(dt)

    # bullet vs. enemy collisions
    hits = pygame.sprite.groupcollide(enemies, bullet_group, False, True)
    for enemy, bullets in hits.items():
        enemy.health -= len(bullets)
        if enemy.health <= 0:
            enemy.kill()

    # draw bullets & crosshair
    for b in bullet_group:
        display.blit(b.image, b.rect.topleft - camera.offset)
    display.blit(
        crosshair,
        (cursor[0] - crosshair.get_width()//2,
         cursor[1] - crosshair.get_height()//2)
    )

    # player vs. enemy collisions (unchanged)
    hits = pygame.sprite.spritecollide(player, enemies, False)
    now = pygame.time.get_ticks()
    if hits and not player.invincible:
        player.health -= 10
        player.invincible = True
        player.last_hit_time = now
        if player.health <= 0:
            print("Game Over!")
            game_running = False
    if player.invincible and now - player.last_hit_time >= player.invincibility_duration:
        player.invincible = False

    # draw player health bar
    draw_health_bar(display, 20, 20, 200, 20, player.health, player.max_health)

    # spawn new enemies
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_running = False
        elif event.type == SPAWN_EVENT and len(game_sprites) < max_enemies:
            e = Enemy()
            enemies.add(e)
            game_sprites.add(e)

    pygame.display.update()

pygame.quit()
