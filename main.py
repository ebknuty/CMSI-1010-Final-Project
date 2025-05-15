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

# Starts up pygame
pygame.init()
warnings.filterwarnings("ignore", category=UserWarning, module="PIL.PngImagePlugin")

# font for wave counter
wave_font = pygame.font.Font(None, 36)

FPS = 100  # Caps the frames per second
SCREEN_WIDTH = 1000  # Width of the game window
SCREEN_HEIGHT = 1000  # Height of the game window
MAP_WIDTH = 2000  # Width of the entire map background
MAP_HEIGHT = 2000  # Height of the entire map background
screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT)  # Tuple for screen dimensions
background_pos = (0, 0)  # Top-left origin for background blitting
player_start_pos = (600, 600)  # Starting position of the player
player_size = .15  # Scaling factor for player sprite
player_speed = 300  # Movement speed of the player
vector = pygame.math.Vector2  # For vector operations throughout the code

# Wave variables to manage wave progression
wave_number = 1  # Current wave index
current_wave_count = 5  # Number of enemies in the current wave
wave_clear_time = None  # Time when a wave was cleared

# Sprite groups for organization
enemies = pygame.sprite.Group()     # All enemy sprites
bullet_group = pygame.sprite.Group()  # All bullet sprites
game_sprites = pygame.sprite.Group()  # All active game sprites (including player)

# Screen setup and window caption
display = pygame.display.set_mode(screen_size)
pygame.display.set_caption("2D shooter")
clock = pygame.time.Clock()  # Clock object to track time and FPS

# Load and scale the main game background
background = pygame.transform.scale(
    pygame.image.load("Lords Of Pain/environment/ground.png.png").convert(),
    (MAP_WIDTH, MAP_HEIGHT)
)
# Load and scale the menu background
menu_background = pygame.transform.scale(
    pygame.image.load("Premium top-down shooter asset pack/yo gurt.jpg"),
    screen_size
)

# Load UI button images and scale them
play_button_img = pygame.transform.scale(
    pygame.image.load("Premium top-down shooter asset pack/Play Rect.png"),
    (400, 125)
)
quit_button_img = pygame.transform.scale(
    pygame.image.load("Premium top-down shooter asset pack/Quit Rect.png"),
    (400, 125)
)
# Crosshair sprite for aiming
crosshair = pygame.image.load(
    "Premium top-down shooter asset pack/crosshair.png"
)

# -- HEALTH BAR HELPER --
def draw_health_bar(surface, x, y, width, height, current, maximum):
    """
    Draws a health bar on the given surface.
    surface: pygame Surface to draw on
    x, y: top-left position of the bar
    width, height: size of the bar
    current, maximum: current and max health values
    """
    # Draw the red background for missing health
    pygame.draw.rect(surface, (100, 0, 0), (x, y, width, height))
    # Calculate health ratio and draw the foreground
    ratio = max(current, 0) / maximum
    pygame.draw.rect(surface, (255, 0, 0), (x, y, width * ratio, height))
    # Draw a black border around the health bar
    pygame.draw.rect(surface, (0, 0, 0), (x, y, width, height), 2)

# --- Player Class ---
class Player(pygame.sprite.Sprite):
    """
    Represents the player character, handling movement, rotation,
    health status, and hitbox management.
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
        self.rect = self.image.get_rect()  # Rectangle for blitting
        self.pos = vector(player_start_pos)  # Float-based position vector
        self.original_character = self.image  # Store unrotated sprite
        # Hitbox for collision detection, centered in the sprite
        self.hitbox = self.original_character.get_rect(
            center=(self.rect.width / 2, self.rect.height / 2)
        )
        # Health attributes
        self.max_health = 100
        self.health = self.max_health
        self.invincible = False
        self.invincibility_duration = 1000  # ms of invincibility after hit
        self.last_hit_time = 0  # Timestamp of last damage taken

    def movementinputs(self):
        """
        Reads keyboard input (WASD) and sets movement speed in x/y.
        """
        keys = pygame.key.get_pressed()
        self.move_speedx, self.move_speedy = 0, 0
        if keys[pygame.K_w]: self.move_speedy -= player_speed
        if keys[pygame.K_a]: self.move_speedx -= player_speed
        if keys[pygame.K_s]: self.move_speedy += player_speed
        if keys[pygame.K_d]: self.move_speedx += player_speed
        # Normalize diagonal movement
        if (keys[pygame.K_w] or keys[pygame.K_s]) and (keys[pygame.K_a] or keys[pygame.K_d]):
            self.move_speedx /= math.sqrt(2)
            self.move_speedy /= math.sqrt(2)

    def playermovement(self, dt):
        """
        Updates player position based on speed and delta time,
        enforces map boundaries, and updates rect center.
        """
        self.pos += vector(self.move_speedx, self.move_speedy) * dt
        self.hitbox.center = self.pos
        self.boundary('horizontal')
        self.boundary('vertical')
        self.rect.center = self.hitbox.center

    def rotation(self, cursor_pos):
        """
        Rotates player sprite to face the mouse cursor.
        """
        dx = cursor_pos[0] - SCREEN_WIDTH / 2
        dy = cursor_pos[1] - SCREEN_HEIGHT / 2
        angle = math.degrees(math.atan2(dy, dx))
        self.image = pygame.transform.rotate(self.original_character, -angle + 90)
        self.rect = self.image.get_rect(center=self.hitbox.center)

    def boundary(self, direction):
        """
        Keeps player within the map bounds horizontally or vertically.
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
        dt: time since last frame in seconds
        cursor_pos: current mouse position
        """
        self.movementinputs()
        self.playermovement(dt)
        self.rotation(cursor_pos)

# --- Camera Class ---
class Camera:
    """
    Manages drawing the scrolling background and all sprites
    relative to the camera offset.
    """
    def __init__(self):
        self.offset = vector()  # Current camera offset
        self.bg_rect = background.get_rect(topleft=background_pos)

    def move_bg(self):
        """
        Updates the offset based on player position and
        blits background and sprites accordingly.
        """
        self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2
        self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2
        bg_offset = self.bg_rect.topleft - self.offset
        display.blit(background, bg_offset)
        for sprite in game_sprites:
            pos = sprite.rect.topleft - self.offset
            display.blit(sprite.image, pos)

# --- Bullet & Gun Classes ---
class Bullet(pygame.sprite.Sprite):
    """
    Represents a bullet fired from a gun, handles movement
    and self-removal when off-screen.
    """
    def __init__(self, pos, direction, speed=500, color=(255, 0, 0), radius=3):
        super().__init__()
        self.image = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect(center=pos)
        self.velocity = pygame.math.Vector2(direction).normalize() * speed

    def update(self, dt):
        """
        Moves bullet by its velocity and kills it if it leaves display.
        dt: time since last frame
        """
        self.rect.x += self.velocity.x * dt
        self.rect.y += self.velocity.y * dt
        if not display.get_rect().colliderect(self.rect):
            self.kill()

class Gun:
    """
    Base class for all guns. Handles ammo, reloading,
    and shooting cooldown.
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
        Completes reload if reload_time has elapsed.
        """
        if self.is_reloading:
            now = pygame.time.get_ticks()
            if now - self.reload_start >= self.reload_time:
                self.ammo = self.clip_size
                self.is_reloading = False

    def reload(self):
        """
        Initiates reload sequence if ammo is not full.
        """
        if not self.is_reloading and self.ammo < self.clip_size:
            self.is_reloading = True
            self.reload_start = pygame.time.get_ticks()

    def shoot(self, pos, direction, bullet_group):
        """
        Fires a single bullet if not reloading, has ammo,
        and cooldown has passed. Returns bullet or None.
        """
        now = pygame.time.get_ticks()
        if self.is_reloading or self.ammo <= 0 or (now - self.last_shot) < self.cooldown:
            return None
        self.last_shot = now
        self.ammo -= 1
        bullet = Bullet(pos, direction)
        bullet_group.add(bullet)
        return bullet

class Handgun(Gun):
    """ Simple handgun: small clip, moderate cooldown. """
    def __init__(self, owner):
        super().__init__(owner, clip_size=12, reload_time=1.5, cooldown_ms=400)

class AssaultRifle(Gun):
    """ Assault rifle: larger clip, faster fire rate. """
    def __init__(self, owner):
        super().__init__(owner, clip_size=24, reload_time=2.5, cooldown_ms=100)

class Shotgun(Gun):
    """
    Shotgun: fires multiple pellets in a spread.
    Overrides shoot to emit several Bullet instances.
    """
    def __init__(self, owner):
        super().__init__(owner, clip_size=8, reload_time=2.0, cooldown_ms=800)
        self.pellets = 7
        self.spread_angle = 45

    def shoot(self, pos, direction, bullet_group):
        """
        Fires a spread of pellets if conditions are met.
        Returns True if fired, else None.
        """
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

# --- Menu & Game Over Screens ---
class Menu():
    """
    Generic UI button with image, position, font, and text.
    Used for main menu and game over screens.
    """
    def __init__(self, image, pos, font, text_input):
        self.image = image
        self.pos = pos
        self.font = font
        self.rect = self.image.get_rect(center=(self.pos[0], self.pos[1]))
        self.text_input = text_input

    def draw(self):
        """
        Renders button image and text to the display.
        """
        self.text = self.font.render(self.text_input, True, "black")
        self.text_rect = self.text.get_rect(center=(self.pos[0], self.pos[1]))
        display.blit(self.image, self.rect)
        display.blit(self.text, self.text_rect)

    def check_click(self, event):
        """
        Returns True if this button was clicked.
        """
        mouse_pos = pygame.mouse.get_pos()
        if (self.rect.left <= mouse_pos[0] <= self.rect.right and
            self.rect.top <= mouse_pos[1] <= self.rect.bottom):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return True
        return False

def main_menu():
    """
    Displays the main menu until PLAY or QUIT is clicked.
    """
    pygame.mouse.set_visible(True)
    display.blit(menu_background, background_pos)
    font_large = pygame.font.Font("Premium top-down shooter asset pack/font.ttf", 100)
    title = Menu(
        pygame.Surface((400,100), pygame.SRCALPHA),
        (500,100),
        pygame.font.Font("Premium top-down shooter asset pack/font.ttf", 60),
        "Welcome to Pest!"
    )
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

score = 0  # Player's score counter

def game_over_menu():
    """
    Shows the game over screen with final score and options
    to replay or quit.
    """
    pygame.mouse.set_visible(True)
    play_button_img_replay = pygame.transform.scale(
        pygame.image.load("Premium top-down shooter asset pack/Play Rect.png"),
        (600, 130)
    )
    scoreboard = Menu(
        pygame.Surface((400,100), pygame.SRCALPHA),
        (500,100),
        pygame.font.Font("Premium top-down shooter asset pack/font.ttf", 40),
        f"Your Final Score was: {score}"
    )
    font_big = pygame.font.Font("Premium top-down shooter asset pack/font.ttf", 100)
    go_text = font_big.render("GAME OVER", True, ("black"))
    go_rect = go_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
    replay_button = Menu(play_button_img_replay, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), font_big, "REPLAY")
    quit_button = Menu(quit_button_img, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 200), font_big, "QUIT")
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if replay_button.check_click(event):
                # Restart the script
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
    """
    Processes keyboard and mouse input for the player,
    handles weapon switching and shooting, and updates score.
    """
    global score
    keys = pygame.key.get_pressed()
    # Weapon selection
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

    # Handle bullet hits on enemies and update score
    hits = pygame.sprite.groupcollide(enemies, bullet_group, False, True)
    for enemy_sprite, bullets in hits.items():
        enemy_sprite.health -= len(bullets)
        if enemy_sprite.health <= 0:
            enemy_sprite.kill()
            score += 1

# --- Enemy Class ---
class Enemy(pygame.sprite.Sprite):
    """
    Simple enemy that chases the player, has health,
    and removes itself when defeated.
    """
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.rotozoom(
            pygame.image.load("Premium top-down shooter asset pack/Bug_enemy.png").convert_alpha(),
            0, player_size
        )
        self.rect = self.image.get_rect()
        # Spawn around the player's start position
        offset_x = random.randint(-100, 100)
        offset_y = random.randint(-100, 100)
        self.pos = vector(player_start_pos[0] + offset_x, player_start_pos[1] + offset_y)
        self.rect.topleft = self.pos
        self.speed = 80  # Movement speed
        self.max_health = 5
        self.health = self.max_health
        self.direction = vector(0, 0)

    def update(self, dt, placeholder):
        """
        Moves enemy toward the player each frame.
        dt: time since last frame
        placeholder: unused but required by group update
        """
        to_player = player.pos - self.pos
        if to_player.length_squared() > 0:
            self.direction = to_player.normalize()
        self.pos += self.direction * self.speed * dt
        # Keep within map bounds
        self.pos.x = max(0, min(self.pos.x, MAP_WIDTH - self.rect.width))
        self.pos.y = max(0, min(self.pos.y, MAP_HEIGHT - self.rect.height))
        self.rect.topleft = self.pos

def spawn_wave(count):
    """
    Creates 'count' new enemies and adds them to the game.
    """
    for _ in range(count):
        e = Enemy()
        enemies.add(e)
        game_sprites.add(e)

# --- Setup & Start ---
main_menu()                     # Show main menu first
camera = Camera()               # Initialize camera
player = Player()               # Create player instance
player.gun = AssaultRifle(player)  # Give player a starting weapon
game_sprites.add(player)        # Add player to sprite group
spawn_wave(current_wave_count)  # Spawn the first wave

# --- Main Game Loop ---
game_running = True
while game_running:
    pygame.mouse.set_visible(False)
    dt = clock.tick(FPS) / 1000  # Delta time in seconds
    cursor = pygame.mouse.get_pos()

    handle_player_input(player, bullet_group, camera)
    player.gun.update()
    camera.move_bg()
    game_sprites.update(dt, cursor)
    bullet_group.update(dt)

    # Draw bullets and the crosshair
    for b in bullet_group:
        display.blit(b.image, b.rect.topleft - camera.offset)
    display.blit(
        crosshair,
        (cursor[0] - crosshair.get_width() // 2,
         cursor[1] - crosshair.get_height() // 2)
    )

    # Player damage and invincibility logic
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

    # Wave progression check
    if len(enemies) == 0:
        if wave_clear_time is None:
            wave_clear_time = pygame.time.get_ticks()
        elif pygame.time.get_ticks() - wave_clear_time >= 5000:
            wave_number += 1
            current_wave_count = math.ceil(current_wave_count * 1.5)
            spawn_wave(current_wave_count)
            wave_clear_time = None

    # Draw wave counter on screen
    wave_text = wave_font.render(f"Wave: {wave_number}", True, (255, 255, 255))
    display.blit(wave_text, (20, 50))

    pygame.display.update()

# After the game loop ends, show game over screen
game_over_menu()

