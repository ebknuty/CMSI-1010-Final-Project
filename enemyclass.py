import pygame
import math
import warnings
import random


pygame.init()
warnings.filterwarnings("ignore", category=UserWarning, module="PIL.PngImagePlugin")

FPS = 100  # frames per second
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 1000
MAP_WIDTH, MAP_HEIGHT = 2000, 2000
PLAYER_START_POS = (600, 600)
PLAYER_SIZE = 0.15
PLAYER_SPEED = 160

display = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("2D Shooter")
clock = pygame.time.Clock()

# load assets
background = pygame.transform.scale(
    pygame.image.load("Lords Of Pain/environment/ground.png.png").convert(),
    (MAP_WIDTH, MAP_HEIGHT)
)
crosshair = pygame.image.load(
    "CMSI-1010-Final-Project/Premium_top-down_shooter_asset_pack/crosshair.png"
).convert_alpha()


Vector = pygame.math.Vector2


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = pygame.transform.rotozoom(
            pygame.image.load(
                "CMSI-1010-Final-Project/Premium_top-down_shooter_asset_pack/Player_with_AK.png"
            ).convert_alpha(),
            0,
            PLAYER_SIZE
        )
        self.image = self.original_image
        self.rect = self.image.get_rect(center=PLAYER_START_POS)
        self.pos = Vector(PLAYER_START_POS)

    def movement_inputs(self):
        keys = pygame.key.get_pressed()
        vx = vy = 0
        if keys[pygame.K_w]:
            vy -= PLAYER_SPEED
        if keys[pygame.K_s]:
            vy += PLAYER_SPEED
        if keys[pygame.K_a]:
            vx -= PLAYER_SPEED
        if keys[pygame.K_d]:
            vx += PLAYER_SPEED
        # normalize diagonal movement
        if vx != 0 and vy != 0:
            vx /= math.sqrt(2)
            vy /= math.sqrt(2)
        return vx, vy

    def update(self, dt, cursor_pos):
        # movement
        vx, vy = self.movement_inputs()
        self.pos += Vector(vx, vy) * dt
        self.rect.center = self.pos

        # rotation to face cursor
        dx = cursor_pos[0] - SCREEN_WIDTH / 2
        dy = cursor_pos[1] - SCREEN_HEIGHT / 2
        angle = math.degrees(math.atan2(dy, dx))
        self.image = pygame.transform.rotate(self.original_image, -angle + 90)
        self.rect = self.image.get_rect(center=self.rect.center)


class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.rotozoom(
            pygame.image.load(
                "CMSI-1010-Final-Project/Premium_top-down_shooter_asset_pack/Bug_enemy.png"
            ).convert_alpha(),
            0,
            PLAYER_SIZE
        )
        self.rect = self.image.get_rect()
        # spawn near player
        offset_x = random.randint(-100, 100)
        offset_y = random.randint(-100, 100)
        self.pos = Vector(PLAYER_START_POS[0] + offset_x,
                          PLAYER_START_POS[1] + offset_y)
        self.rect.topleft = self.pos

        self.speed = 80  # px/sec
        self._pick_new_direction()

    def _pick_new_direction(self):
        dx, dy = random.uniform(-1, 1), random.uniform(-1, 1)
        v = Vector(dx, dy)
        if v.length_squared() == 0:
            v = Vector(1, 0)
        self.direction = v.normalize()
        # next change in 0.5–2s
        self.next_change = pygame.time.get_ticks() + random.randint(500, 2000)

    def update(self, dt):
        now = pygame.time.get_ticks()
        if now >= self.next_change:
            self._pick_new_direction()
        # move and clamp inside map
        self.pos += self.direction * self.speed * dt
        self.pos.x = max(0, min(self.pos.x, MAP_WIDTH - self.rect.width))
        self.pos.y = max(0, min(self.pos.y, MAP_HEIGHT - self.rect.height))
        self.rect.topleft = self.pos


class Camera:
    def __init__(self):
        self.offset = Vector()
        self.bg_rect = background.get_rect(topleft=(0, 0))

    def draw(self, surface, sprites):
        # compute offset so player stays centered
        self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2
        self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2
        bg_offset = self.bg_rect.topleft - self.offset
        surface.blit(background, bg_offset)
        for sprite in sprites:
            surface.blit(sprite.image, sprite.rect.topleft - self.offset)


player = Player()
enemy = Enemy()

players = pygame.sprite.Group(player)
enemies = pygame.sprite.Group(enemy)
game_sprites = pygame.sprite.Group(player, enemy)

camera = Camera()

# spawn new enemy every 3 seconds
SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWN_EVENT, 3000)

game_running = True

#
while game_running:
    dt = clock.tick(FPS) / 1000
    cursor = pygame.mouse.get_pos()

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_running = False
        elif event.type == SPAWN_EVENT:
            e = Enemy()
            enemies.add(e)
            game_sprites.add(e)

    # --- Updates ---
    players.update(dt, cursor)
    enemies.update(dt)

    # --- Drawing ---
    camera.draw(display, game_sprites)
    display.blit(
        crosshair,
        (cursor[0] - crosshair.get_width() // 2,
         cursor[1] - crosshair.get_height() // 2)
    )
    pygame.display.update()

pygame.quit()




