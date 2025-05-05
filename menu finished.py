import pygame
import sys
import os
import math
# We import warnings here to bypass a libpng warning that triggers when some of the game assets are used
import warnings
import random
# Starts up pygame
pygame.init()

# This is to avoid certain warnings and glitches triggered by using some of the external game assets
warnings.filterwarnings("ignore", category=UserWarning, module="PIL.PngImagePlugin")

FPS = 100  # Caps the frames per second
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1000
MAP_WIDTH = 2000  # Size of the entire map
MAP_HEIGHT = 2000
screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
background_pos = (0, 0)
player_start_pos = (600, 600)
player_size = .15
player_speed = 300
vector = pygame.math.Vector2  # Sets a variable for the vector function used throughout the code
max_enemies = 5

enemies = pygame.sprite.Group()

# Screen set up
display = pygame.display.set_mode(screen_size)
pygame.display.set_caption("2D shooter")

# Variable to set up a clock object that keeps track of time
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

game_sprites = pygame.sprite.Group()

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
        dx = cursor_pos[0] - SCREEN_WIDTH/2
        dy = cursor_pos[1] - SCREEN_HEIGHT/2
        angle = math.degrees(math.atan2(dy, dx))
        self.image = pygame.transform.rotate(self.original_character, -angle + 90)
        self.rect = self.image.get_rect(center=self.hitbox.center)

    def boundary(self, direction):
        if direction == 'horizontal':
            self.hitbox.centerx = max(152, min(self.hitbox.centerx, 1929))
        if direction == 'vertical':
            self.hitbox.centery = max(221, min(self.hitbox.centery, 1911))
        self.pos = vector(self.hitbox.center)
        self.rect.center = self.hitbox.center

    def update(self, between_frames, cursor_pos):
        self.movementinputs()
        self.playermovement(between_frames)
        self.rotation(cursor_pos)

# --- Camera Class ---
class Camera:
    def __init__(self):
        self.offset = vector()
        self.bg_rect = background.get_rect(topleft=background_pos)

    def move_bg(self):
        self.offset.x = player.rect.centerx - SCREEN_WIDTH/2
        self.offset.y = player.rect.centery - SCREEN_HEIGHT/2
        bg_offset = self.bg_rect.topleft - self.offset
        display.blit(background, bg_offset)
        for sprite in game_sprites:
            pos = sprite.rect.topleft - self.offset
            display.blit(sprite.image, pos)

camera = Camera()
player = Player()
game_sprites.add(player)

# --- Bullet & Gun Classes ---
class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, direction, speed=500, color=(255,0,0), radius=3):
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
        super().__init__(owner, clip_size=24, reload_time=2.5, cooldown_ms=100)

# Initialize bullet group and gun
bullet_group = pygame.sprite.Group()
player.gun = AssaultRifle(player)

def handle_player_input(player, bullet_group, camera):
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = vector(pygame.mouse.get_pos()) + camera.offset
            direction = mouse_pos - player.rect.center
            player.gun.shoot(player.rect.center, direction, bullet_group)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            player.gun.reload()


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
        self._pick_new_direction()

    def _pick_new_direction(self):
        dx, dy = random.uniform(-1,1), random.uniform(-1,1)
        v = vector(dx, dy)
        if v.length_squared() == 0:
            v = vector(1,0)
        self.direction = v.normalize()
        self.next_change = pygame.time.get_ticks() + random.randint(500,2000)

    def update(self, dt, placeholder):
        now = pygame.time.get_ticks()
        if now >= self.next_change:
            self._pick_new_direction()
        self.pos += self.direction * self.speed * dt
        self.pos.x = max(152, min(self.pos.x, 1929))
        self.pos.y = max(221, min(self.pos.y, 1911))
        self.rect.topleft = self.pos

# Spawn initial enemy
enemy = Enemy()
enemies.add(enemy)
game_sprites.add(enemy)

# Set up spawn timer
SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWN_EVENT, 100)

# --- Menu Class ---
class Menu():
    def __init__(self, image, pos, font, text_input):
        self.image = image
        self.pos = pos
        self.font = font
        self.rect = self.image.get_rect(center=pos)
        self.text_input = text_input

    def draw(self):
        text = self.font.render(self.text_input, True, "black")
        text_rect = text.get_rect(center=self.pos)
        display.blit(self.image, self.rect)
        display.blit(text, text_rect)

    def check_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                return True
        return False

# --- Title Screen ---
def main_menu():
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

main_menu()

# --- Game Over Screen ---
def game_over_menu():
    pygame.mouse.set_visible(True)
    play_button_img = pygame.transform.scale(
    pygame.image.load("Premium top-down shooter asset pack/Play Rect.png"),
    (600, 130))
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
        pygame.display.update()
        clock.tick(FPS)

# --- Main Game Loop ---
game_running = True
while game_running:
    pygame.mouse.set_visible(False)
    between_frames = clock.tick(FPS) / 1000
    cursor = pygame.mouse.get_pos()

    # Player input and gun reload
    handle_player_input(player, bullet_group, camera)
    player.gun.update()

    # Background and sprites
    camera.move_bg()
    game_sprites.update(between_frames, cursor)
    bullet_group.update(between_frames)

    # Draw player bullets
    for bullet in bullet_group:
        pos = bullet.rect.topleft - camera.offset
        display.blit(bullet.image, pos)
    display.blit(crosshair, (cursor[0] - crosshair.get_width()//2, cursor[1] - crosshair.get_height()//2))

    # Collisions & damage
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

    # Draw health bar
    draw_health_bar(display, 20, 20, 200, 20, player.health, player.max_health)

    # Spawn events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_running = False
        elif event.type == SPAWN_EVENT:
            if len(game_sprites) < max_enemies:
                enemy = Enemy()
                enemies.add(enemy)
                game_sprites.add(enemy)

    pygame.display.update()

# Shows end screen
game_over_menu()