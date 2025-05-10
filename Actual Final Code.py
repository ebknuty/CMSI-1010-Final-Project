import pygame
import sys
import os
import math
import warnings
import random

# Starts up pygame
pygame.init()
warnings.filterwarnings("ignore", category=UserWarning, module="PIL.PngImagePlugin")

# font for wave counter
wave_font = pygame.font.Font(None, 36)

FPS = 100  # Caps the frames per second
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1000
MAP_WIDTH = 2000
MAP_HEIGHT = 2000
screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
background_pos = (0, 0)
player_start_pos = (600, 600)
player_size = .15
player_speed = 300
vector = pygame.math.Vector2  # For vector operations

# Wave variables
wave_number = 1
current_wave_count = 5  # initial wave size
wave_clear_time = None

# Sprite groups
enemies = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
game_sprites = pygame.sprite.Group()

# Screen set up
display = pygame.display.set_mode(screen_size)
pygame.display.set_caption("2D shooter")
clock = pygame.time.Clock()

# Load and scale backgrounds
background = pygame.transform.scale(
    pygame.image.load("Lords Of Pain/environment/ground.png.png").convert(),
    (MAP_WIDTH, MAP_HEIGHT)
)
menu_background = pygame.transform.scale(
    pygame.image.load("Premium top-down shooter asset pack/yo gurt.jpg"),
    screen_size
)

# Load UI buttons and crosshair
play_button_img = pygame.transform.scale(
    pygame.image.load("Premium top-down shooter asset pack/Play Rect.png"),
    (400, 125)
)
quit_button_img = pygame.transform.scale(
    pygame.image.load("Premium top-down shooter asset pack/Quit Rect.png"),
    (400, 125)
)
crosshair = pygame.image.load(
    "Premium top-down shooter asset pack/crosshair.png"
)

# -- HEALTH BAR HELPER --
def draw_health_bar(surface, x, y, width, height, current, maximum):
    pygame.draw.rect(surface, (100, 0, 0), (x, y, width, height))
    ratio = max(current, 0) / maximum
    pygame.draw.rect(surface, (255, 0, 0), (x, y, width * ratio, height))
    pygame.draw.rect(surface, (0, 0, 0), (x, y, width, height), 2)

# --- Player Class ---
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
            center=(self.rect.width / 2, self.rect.height / 2)
        )
        self.max_health = 100
        self.health = self.max_health
        self.invincible = False
        self.invincibility_duration = 1000
        self.last_hit_time = 0

    def movementinputs(self):
        keys = pygame.key.get_pressed()
        self.move_speedx, self.move_speedy = 0, 0
        if keys[pygame.K_w]: self.move_speedy -= player_speed
        if keys[pygame.K_a]: self.move_speedx -= player_speed
        if keys[pygame.K_s]: self.move_speedy += player_speed
        if keys[pygame.K_d]: self.move_speedx += player_speed
        if (keys[pygame.K_w] or keys[pygame.K_s]) and (keys[pygame.K_a] or keys[pygame.K_d]):
            self.move_speedx /= math.sqrt(2)
            self.move_speedy /= math.sqrt(2)

    def playermovement(self, dt):
        self.pos += vector(self.move_speedx, self.move_speedy) * dt
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
            self.hitbox.centerx = max(152, min(self.hitbox.centerx, MAP_WIDTH - 71))
        if direction == 'vertical':
            self.hitbox.centery = max(221, min(self.hitbox.centery, MAP_HEIGHT - 71))
        self.pos = vector(self.hitbox.center)
        self.rect.center = self.hitbox.center

    def update(self, dt, cursor_pos):
        self.movementinputs()
        self.playermovement(dt)
        self.rotation(cursor_pos)

# --- Camera Class ---
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

# --- Bullet & Gun Classes ---

# Erin's Branch Gun Classes
class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, direction, speed=500, color=(255, 0, 0), radius=3):
        super().__init__()
        self.image = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect(center=pos)
        self.velocity = pygame.math.Vector2(direction).normalize() * speed

    def update(self, dt):
        self.rect.x += (self.velocity.x * dt)
        self.rect.y += (self.velocity.y * dt)
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
        if self.is_reloading:
            now = pygame.time.get_ticks()
            if now - self.reload_start >= self.reload_time:
                self.ammo = self.clip_size
                self.is_reloading = False

    def reload(self):
        if not self.is_reloading and self.ammo < self.clip_size:
            self.is_reloading = True
            self.reload_start = pygame.time.get_ticks()

    def shoot(self, pos, direction, bullet_group):
        now = pygame.time.get_ticks()
        if self.is_reloading or self.ammo <= 0 or (now - self.last_shot) < self.cooldown:
            return None
        self.last_shot = now
        self.ammo -= 1
        bullet = Bullet(pos, direction)
        bullet_group.add(bullet)
        return bullet

class Handgun(Gun):
    def __init__(self, owner):
        super().__init__(owner, clip_size=12, reload_time=1.5, cooldown_ms=400)

class AssaultRifle(Gun):
    def __init__(self, owner):
        super().__init__(owner, clip_size=24, reload_time=2.5, cooldown_ms=100)

class Shotgun(Gun):
    def __init__(self, owner):
        super().__init__(owner, clip_size=8, reload_time=2.0, cooldown_ms=800)
        self.pellets = 7
        self.spread_angle = 45

    def shoot(self, pos, direction, bullet_group):
        now = pygame.time.get_ticks()
        if self.is_reloading or self.ammo <= 0 or (now - self.last_shot) < self.cooldown:
            return None
        self.last_shot = now
        self.ammo -= 1
        dir_vec = pygame.math.Vector2(direction).normalize()
        base_angle = math.degrees(math.atan2(dir_vec.y, dir_vec.x))
        step = self.spread_angle / (self.pellets - 1)
        for i in range(self.pellets):
            angle = base_angle - self.spread_angle/2 + i*step
            rad = math.radians(angle)
            pellet_dir = pygame.math.Vector2(math.cos(rad), math.sin(rad))
            bullet_group.add(Bullet(pos, pellet_dir))
        return True



class Menu():
    def __init__(self, image, pos, font, text_input):
        self.image = image
        self.pos = pos
        self.font = font
        self.rect = self.image.get_rect(center = (self.pos[0],self.pos[1]))
        self.text_input = text_input

    def draw(self):
       self.text = self.font.render(self.text_input, True, "black")
       self.text_rect = self.text.get_rect(center = (self.pos[0],self.pos[1]))
       display.blit(self.image,self.rect)
       display.blit(self.text, self.text_rect)


    def check_click(self, event):
        mouse_pos = pygame.mouse.get_pos()
        if mouse_pos[0] in range(self.rect.left, self.rect.right) and mouse_pos[1] in range(self.rect.top, self.rect.bottom):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return True
        return False
    


# --- Menu & Game Over Screens ---
def main_menu():
    pygame.mouse.set_visible(True)
    display.blit(menu_background, background_pos)
    font_large = pygame.font.Font("Premium top-down shooter asset pack/font.ttf", 100)
    title = Menu(pygame.Surface((400,100), pygame.SRCALPHA), (500,100), pygame.font.Font("Premium top-down shooter asset pack/font.ttf", 60), "Welcome to Pest!")
    play_button = Menu(play_button_img, (500,600), font_large, "PLAY")
    quit_button = Menu(quit_button_img, (500,900), font_large, "QUIT")
    menu_active = True
    while menu_active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if play_button.check_click(event):
                menu_active = False
            if quit_button.check_click(event):
                pygame.quit(); sys.exit()
        display.blit(menu_background, background_pos)
        title.draw()
        play_button.draw()
        quit_button.draw()
        pygame.display.update()
        clock.tick(FPS)

score = 0
def game_over_menu():
    pygame.mouse.set_visible(True)
    play_button_img = pygame.transform.scale(
    pygame.image.load("Premium top-down shooter asset pack/Play Rect.png"),
    (600, 130))
    scoreboard = Menu(pygame.Surface((400,100), pygame.SRCALPHA), (500,100), pygame.font.Font("Premium top-down shooter asset pack/font.ttf", 40), f"Your Final Score was: {score} ")
    font_big = pygame.font.Font("Premium top-down shooter asset pack/font.ttf", 100)
    go_text = font_big.render("GAME OVER", True, ("black"))
    go_rect = go_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
    replay_button = Menu(play_button_img, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), font_big, "REPLAY")
    quit_button = Menu(quit_button_img, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 200), font_big, "QUIT")
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if replay_button.check_click(event):
                os.execv(sys.executable, [sys.executable] + sys.argv)
            if quit_button.check_click(event):
                pygame.quit(); sys.exit()
        display.blit(menu_background, background_pos)
        display.blit(go_text, go_rect)
        replay_button.draw()
        quit_button.draw()
        scoreboard.draw()
        pygame.display.update()
        clock.tick(FPS)

# --- Input Handler ---
def handle_player_input(player, bullet_group, camera):
    global score
    keys = pygame.key.get_pressed()
    
    if keys[pygame.K_1]:
        player.gun = Handgun(player)
    elif keys[pygame.K_2]:
        player.gun = Shotgun(player)
    elif keys[pygame.K_3]:
        player.gun = AssaultRifle(player)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = vector(pygame.mouse.get_pos()) + camera.offset
            direction = mouse_pos - player.rect.center
            player.gun.shoot(player.rect.center, direction, bullet_group)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            player.gun.reload()
    hits = pygame.sprite.groupcollide(enemies, bullet_group, False, True)
    for enemy_sprite, bullets in hits.items():
        enemy_sprite.health -= len(bullets)
        if enemy_sprite.health <= 0:
            enemy_sprite.kill()
            score += 1




# --- Enemy Class ---
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.rotozoom(
            pygame.image.load("Premium top-down shooter asset pack/Bug_enemy.png").convert_alpha(),
            0, player_size
        )
        self.rect = self.image.get_rect()
        offset_x = random.randint(-100, 100)
        offset_y = random.randint(-100, 100)
        self.pos = vector(player_start_pos[0] + offset_x, player_start_pos[1] + offset_y)
        self.rect.topleft = self.pos
        self.speed = 80
        self.max_health = 5
        self.health = self.max_health
        self.direction = vector(0, 0)

    def update(self, dt, placeholder):
        to_player = player.pos - self.pos
        if to_player.length_squared() > 0:
            self.direction = to_player.normalize()
        self.pos += self.direction * self.speed * dt
        self.pos.x = max(0, min(self.pos.x, MAP_WIDTH - self.rect.width))
        self.pos.y = max(0, min(self.pos.y, MAP_HEIGHT - self.rect.height))
        self.rect.topleft = self.pos

# wave spawning logic
def spawn_wave(count):
    for _ in range(count):
        e = Enemy()
        enemies.add(e)
        game_sprites.add(e)

# --- Setup & Start ---
main_menu()
camera = Camera()
player = Player()
player.gun = AssaultRifle(player)
game_sprites.add(player)
spawn_wave(current_wave_count)

# --- Main Game Loop ---
game_running = True
while game_running:
    pygame.mouse.set_visible(False)
    dt = clock.tick(FPS) / 1000
    cursor = pygame.mouse.get_pos()

    handle_player_input(player, bullet_group, camera)
    player.gun.update()
    camera.move_bg()
    game_sprites.update(dt, cursor)
    bullet_group.update(dt)

    # draw bullets & crosshair
    for b in bullet_group:
        display.blit(b.image, b.rect.topleft - camera.offset)
    display.blit(
        crosshair,
        (cursor[0] - crosshair.get_width() // 2,
         cursor[1] - crosshair.get_height() // 2)
    )

    # player damage logic
    hits = pygame.sprite.spritecollide(player, enemies, False)
    now = pygame.time.get_ticks()
    if hits and not player.invincible:
        player.health -= 10
        player.invincible = True
        player.last_hit_time = now
        if player.health <= 0:
            game_running = False
    if player.invincible and now - player.last_hit_time >= player.invincibility_duration:
        player.invincible = False

    # draw health bar
    draw_health_bar(display, 20, 20, 200, 20, player.health, player.max_health)

    # wave progression
    if len(enemies) == 0:
        if wave_clear_time is None:
            wave_clear_time = pygame.time.get_ticks()
        elif pygame.time.get_ticks() - wave_clear_time >= 5000:
            wave_number += 1
            current_wave_count = math.ceil(current_wave_count * 1.5)
            spawn_wave(current_wave_count)
            wave_clear_time = None

    # draw wave counter
    wave_text = wave_font.render(f"Wave: {wave_number}", True, (255, 255, 255))
    display.blit(wave_text, (20, 50))

    pygame.display.update()


# after loop end, show ending screen
game_over_menu()