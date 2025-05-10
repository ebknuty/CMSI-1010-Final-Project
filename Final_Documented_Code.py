# 2D Cave Shooter Final Project
# By: Mike, Erin, Seiji

# This module runs our top-down wave-based shooter. It defines all
# the core classes and helper functions, and handles the game loop.

import pygame
import sys
import os
import math
import warnings
import random

# Initialize pygame and suppress certain image warnings
pygame.init()
warnings.filterwarnings("ignore", category=UserWarning, module="PIL.PngImagePlugin")

# --- Global Configuration ---
FPS = 100                 # Frames per second cap
SCREEN_WIDTH = 1000       # Width of the game window
SCREEN_HEIGHT = 1000      # Height of the game window
MAP_WIDTH = 2000          # Width of the full map
MAP_HEIGHT = 2000         # Height of the full map
screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
background_pos = (0, 0)   # Top-left corner of the map background
player_start_pos = (600, 600)  # Initial player spawn position
player_size = 0.15        # Scale factor for sprites
player_speed = 300        # Player movement speed (pixels/sec)
vector = pygame.math.Vector2  # For vector math operations

# Wave progression variables
wave_number = 1           # Current wave index
current_wave_count = 5    # Number of enemies in the first wave
wave_clear_time = None    # Timestamp when a wave was cleared

# Sprite groups to manage game objects
enemies = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
game_sprites = pygame.sprite.Group()

# Set up the display window and clock
display = pygame.display.set_mode(screen_size)
pygame.display.set_caption("2D shooter")
clock = pygame.time.Clock()

# --- Asset Loading ---
# Load and scale the main background
background = pygame.transform.scale(
    pygame.image.load("Lords Of Pain/environment/ground.png.png").convert(),
    (MAP_WIDTH, MAP_HEIGHT)
)
# Load menu background from asset pack
menu_background = pygame.transform.scale(
    pygame.image.load("Premium top-down shooter asset pack/yo gurt.jpg"),
    screen_size
)

# UI elements for main menu
play_button_img = pygame.transform.scale(
    pygame.image.load("Premium top-down shooter asset pack/Play Rect.png"),
    (400, 125)
)
quit_button_img = pygame.transform.scale(
    pygame.image.load("Premium top-down shooter asset pack/Quit Rect.png"),
    (400, 125)
)
# Crosshair follows the mouse cursor
crosshair = pygame.image.load(
    "Premium top-down shooter asset pack/crosshair.png"
)

# --- Health Bar Helper Function ---
def draw_health_bar(surface, x, y, width, height, current, maximum):
    """
    Draws a health bar at position (x, y) on the given surface.
    'current' and 'maximum' define the fill ratio.
    """
    # Draw background (empty) bar
    pygame.draw.rect(surface, (100, 0, 0), (x, y, width, height))
    # Compute fill ratio and draw filled portion
    ratio = max(current, 0) / maximum
    pygame.draw.rect(surface, (255, 0, 0), (x, y, width * ratio, height))
    # Draw border around the bar
    pygame.draw.rect(surface, (0, 0, 0), (x, y, width, height), 2)

# --- Player Class ---
class Player(pygame.sprite.Sprite):
    """
    Represents the player character. Handles movement, rotation, health,
    and invincibility frames after taking damage.
    """
    def __init__(self):
        super().__init__()
        # Load and scale the player sprite
        self.image = pygame.transform.rotozoom(
            pygame.image.load(
                "Premium top-down shooter asset pack/Player with AK.png"
            ).convert_alpha(),
            0, player_size
        )
        self.rect = self.image.get_rect()
        # Track precise position using a vector for smooth movement
        self.pos = vector(player_start_pos)
        self.original_character = self.image  # Keep an unrotated copy
        # Use a separate hitbox for collision accuracy
        self.hitbox = self.original_character.get_rect(
            center=(self.rect.width / 2, self.rect.height / 2)
        )
        # Health and invincibility settings
        self.max_health = 100
        self.health = self.max_health
        self.invincible = False
        self.invincibility_duration = 1000  # milliseconds
        self.last_hit_time = 0

    def movementinputs(self):
        """
        Reads keyboard input and sets movement speed on x/y axes.
        """
        keys = pygame.key.get_pressed()
        self.move_speedx, self.move_speedy = 0, 0
        if keys[pygame.K_w]: self.move_speedy -= player_speed
        if keys[pygame.K_a]: self.move_speedx -= player_speed
        if keys[pygame.K_s]: self.move_speedy += player_speed
        if keys[pygame.K_d]: self.move_speedx += player_speed
        # Normalize speed when moving diagonally
        if (keys[pygame.K_w] or keys[pygame.K_s]) and (keys[pygame.K_a] or keys[pygame.K_d]):
            self.move_speedx /= math.sqrt(2)
            self.move_speedy /= math.sqrt(2)

    def playermovement(self, dt):
        """
        Updates position based on movement speeds and delta time.
        Enforces map boundaries.
        """
        self.pos += vector(self.move_speedx, self.move_speedy) * dt
        self.hitbox.center = self.pos
        self.boundary('horizontal')
        self.boundary('vertical')
        self.rect.center = self.hitbox.center

    def rotation(self, cursor_pos):
        """
        Rotates the player sprite to face the mouse cursor.
        """
        dx = cursor_pos[0] - SCREEN_WIDTH / 2
        dy = cursor_pos[1] - SCREEN_HEIGHT / 2
        angle = math.degrees(math.atan2(dy, dx))
        # Rotate original image and recenter
        self.image = pygame.transform.rotate(self.original_character, -angle + 90)
        self.rect = self.image.get_rect(center=self.hitbox.center)

    def boundary(self, direction):
        """
        Keeps the player within the map bounds.
        """
        if direction == 'horizontal':
            self.hitbox.centerx = max(152, min(self.hitbox.centerx, MAP_WIDTH - 71))
        if direction == 'vertical':
            self.hitbox.centery = max(221, min(self.hitbox.centery, MAP_HEIGHT - 71))
        self.pos = vector(self.hitbox.center)
        self.rect.center = self.hitbox.center

    def update(self, dt, cursor_pos):
        """
        Called each frame: handles input, movement, and rotation.
        """
        self.movementinputs()
        self.playermovement(dt)
        self.rotation(cursor_pos)

# --- Camera Class ---
class Camera:
    """
    Manages the scrolling background and renders all sprites
    relative to the player's position.
    """
    def __init__(self):
        self.offset = vector()
        self.bg_rect = background.get_rect(topleft=background_pos)

    def move_bg(self):
        """
        Recenters the view on the player and draws the map plus sprites.
        """
        self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2
        self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2
        bg_offset = self.bg_rect.topleft - self.offset
        display.blit(background, bg_offset)
        # Draw each sprite at its offset position
        for sprite in game_sprites:
            pos = sprite.rect.topleft - self.offset
            display.blit(sprite.image, pos)

# --- Bullet & Gun Classes ---
class Bullet(pygame.sprite.Sprite):
    """
    Represents a bullet fired by the player. Moves in a straight line
    and self-destructs when leaving the screen.
    """
    def __init__(self, pos, direction, speed=500, color=(255, 0, 0), radius=3):
        super().__init__()
        # Draw a simple filled circle as the bullet
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect(center=pos)
        # Velocity vector from direction
        self.velocity = vector(direction).normalize() * speed

    def update(self, dt):
        """
        Moves the bullet each frame and removes it if off-screen.
        """
        self.rect.x += self.velocity.x * dt
        self.rect.y += self.velocity.y * dt
        if not display.get_rect().colliderect(self.rect):
            self.kill()

class Gun:
    """
    Base class for all gun types. Tracks ammo, reloads, and firing cooldowns.
    """
    def __init__(self, owner, clip_size, reload_time, cooldown_ms):
        self.owner = owner
        self.clip_size = clip_size
        self.ammo = clip_size
        self.reload_time = reload_time * 1000  # convert to ms
        self.cooldown = cooldown_ms
        self.last_shot = 0
        self.is_reloading = False
        self.reload_start = 0

    def update(self):
        """
        Handles automatic reload completion when time is up.
        """
        if self.is_reloading and pygame.time.get_ticks() - self.reload_start >= self.reload_time:
            self.ammo = self.clip_size
            self.is_reloading = False

    def reload(self):
        """
        Initiates reload if ammo isn't full.
        """
        if not self.is_reloading and self.ammo < self.clip_size:
            self.is_reloading = True
            self.reload_start = pygame.time.get_ticks()

    def shoot(self, pos, direction, bullet_group):
        """
        Fires a bullet if possible, applying cooldown and ammo checks.
        """
        now = pygame.time.get_ticks()
        if self.is_reloading or self.ammo <= 0 or now - self.last_shot < self.cooldown:
            return
        self.last_shot = now
        self.ammo -= 1
        bullet_group.add(Bullet(pos, direction))

class AssaultRifle(Gun):
    """
    A rapid-fire rifle with a small clip size and moderate reload time.
    """
    def __init__(self, owner):
        super().__init__(owner, clip_size=24, reload_time=2.5, cooldown_ms=100)

# --- Menu Class for Buttons & Text ---
class Menu:
    """
    Simple menu button with an image background and centered text.
    Used for main menu and game-over screens.
    """
    def __init__(self, image, pos, font, text_input):
        self.image = image
        self.pos = pos
        self.font = font
        self.rect = self.image.get_rect(center=(self.pos[0], self.pos[1]))
        self.text_input = text_input

    def draw(self):
        """
        Renders the button image and text at its position.
        """
        self.text = self.font.render(self.text_input, True, "black")
        self.text_rect = self.text.get_rect(center=(self.pos[0], self.pos[1]))
        display.blit(self.image, self.rect)
        display.blit(self.text, self.text_rect)

    def check_click(self, event):
        """
        Returns True if the left mouse button clicks within this button.
        """
        mouse_pos = pygame.mouse.get_pos()
        if (self.rect.left <= mouse_pos[0] <= self.rect.right and
            self.rect.top <= mouse_pos[1] <= self.rect.bottom):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return True
        return False

# --- Menu & Game Over Screens ---
def main_menu():
    """
    Displays the main menu and waits for PLAY or QUIT input.
    """
    pygame.mouse.set_visible(True)
    display.blit(menu_background, background_pos)
    font_large = pygame.font.Font("Premium top-down shooter asset pack/font.ttf", 100)
    title = Menu(pygame.Surface((400,100), pygame.SRCALPHA),
                 (500,100),
                 pygame.font.Font("Premium top-down shooter asset pack/font.ttf", 60),
                 "Welcome to Pest!")
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

score = 0  # Tracks the player's score across waves

def game_over_menu():
    """
    Shows the final score and allows the player to REPLAY or QUIT.
    """
    pygame.mouse.set_visible(True)
    # Load a larger play button for replay
    play_img = pygame.transform.scale(
        pygame.image.load("Premium top-down shooter asset pack/Play Rect.png"),
        (600, 130)
    )
    scoreboard = Menu(
        pygame.Surface((400,100), pygame.SRCALPHA),
        (500,100),
        pygame.font.Font("Premium top-down shooter asset pack/font.ttf", 40),
        f"Your Final Score was: {score} "
    )
    font_big = pygame.font.Font("Premium top-down shooter asset pack/font.ttf", 100)
    go_text = font_big.render("GAME OVER", True, "black")
    go_rect = go_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
    replay_button = Menu(play_img, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), font_big, "REPLAY")
    quit_button = Menu(quit_button_img,
                       (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 200),
                       font_big, "QUIT")
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

# --- Input Handling & Collision Detection ---
def handle_player_input(player, bullet_group, camera):
    """
    Processes events for firing, reloading, and quitting.
    Also handles bullet-enemy collisions and updates score.
    """
    global score
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        # Left-click fires a bullet
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = vector(pygame.mouse.get_pos()) + camera.offset
            direction = mouse_pos - player.rect.center
            player.gun.shoot(player.rect.center, direction, bullet_group)
        # 'R' key reloads
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            player.gun.reload()
    # Check collisions between bullets and enemies
    hits = pygame.sprite.groupcollide(enemies, bullet_group, False, True)
    for enemy_sprite, bullets in hits.items():
        enemy_sprite.health -= len(bullets)
        if enemy_sprite.health <= 0:
            enemy_sprite.kill()
            score += 1

# --- Enemy Class & Wave Spawning ---
class Enemy(pygame.sprite.Sprite):
    """
    Basic enemy that chases the player. Dies after enough bullet hits.
    """
    def __init__(self):
        super().__init__()
        # Load and scale enemy sprite
        self.image = pygame.transform.rotozoom(
            pygame.image.load("Premium top-down shooter asset pack/Bug_enemy.png").convert_alpha(),
            0, player_size
        )
        self.rect = self.image.get_rect()
        # Spawn around player's start position with random offset
        offset_x = random.randint(-100, 100)
        offset_y = random.randint(-100, 100)
        self.pos = vector(player_start_pos[0] + offset_x,
                          player_start_pos[1] + offset_y)
        self.rect.topleft = self.pos
        self.speed = 80           # Movement speed towards player
        self.max_health = 5       # Hits needed to kill
        self.health = self.max_health
        self.direction = vector(0, 0)

    def update(self, dt, unused):
        """
        Moves enemy in the direction of the player each frame.
        Keeps within map bounds.
        """
        to_player = player.pos - self.pos
        if to_player.length_squared() > 0:
            self.direction = to_player.normalize()
        self.pos += self.direction * self.speed * dt
        # Clamp within map edges
        self.pos.x = max(0, min(self.pos.x, MAP_WIDTH - self.rect.width))
        self.pos.y = max(0, min(self.pos.y, MAP_HEIGHT - self.rect.height))
        self.rect.topleft = self.pos

# Spawns a given number of enemies and adds them to groups
def spawn_wave(count):
    """
    Creates 'count' new enemies and adds them to tracking groups.
    """
    for _ in range(count):
        e = Enemy()
        enemies.add(e)
        game_sprites.add(e)

# --- Game Initialization & Main Loop ---
main_menu()        # Show the opening menu until PLAY is selected
camera = Camera()
player = Player()
player.gun = AssaultRifle(player)
game_sprites.add(player)
spawn_wave(current_wave_count)

game_running = True
while game_running:
    pygame.mouse.set_visible(False)
    # Delta time in seconds for frame-independent movement
    dt = clock.tick(FPS) / 1000
    cursor = pygame.mouse.get_pos()

    handle_player_input(player, bullet_group, camera)
    player.gun.update()
    camera.move_bg()
    game_sprites.update(dt, cursor)
    bullet_group.update(dt)

    # Draw bullets and custom crosshair
    for b in bullet_group:
        display.blit(b.image, b.rect.topleft - camera.offset)
    display.blit(
        crosshair,
        (cursor[0] - crosshair.get_width() // 2,
         cursor[1] - crosshair.get_height() // 2)
    )

    # Player damage and invincibility handling
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

    # Draw the player's health bar
    draw_health_bar(display, 20, 20, 200, 20, player.health, player.max_health)

    # Check for wave completion and spawn next wave
    if len(enemies) == 0:
        if wave_clear_time is None:
            wave_clear_time = pygame.time.get_ticks()
        elif pygame.time.get_ticks() - wave_clear_time >= 5000:
            wave_number += 1
            current_wave_count = math.ceil(current_wave_count * 1.5)
            spawn_wave(current_wave_count)
            wave_clear_time = None

    # Show current wave number
    wave_text = wave_font.render(f"Wave: {wave_number}", True, (255, 255, 255))
    display.blit(wave_text, (20, 50))

    pygame.display.update()

# Once the player dies, show game over screen
game_over_menu()
