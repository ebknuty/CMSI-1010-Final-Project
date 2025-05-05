import pygame
import math
# We import warnings here to bypass a libpng warning that triggers when some of the game assets are used
import warnings
import random
# Starts up pygame
pygame.init()

# This is to avoid certain warnings and glitches triggered by using some of the external game assets
warnings.filterwarnings("ignore",category = UserWarning, module = "PIL.PngImagePlugin")

FPS = 100  # Caps the frames per second
SCREEN_WIDTH = 1000 
SCREEN_HEIGHT = 1000
screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT) # Portion of the map the player is able to see at any given moment
MAP_WIDTH = (2000) # Size of the entire map
MAP_HEIGHT = (2000)
background_pos = (0,0)
player_start_pos = (600 , 600)
player_size = .15
player_speed = 160
vector = pygame.math.Vector2 # Sets a variable for the vector function used throughout the code

# Screen set up
display = pygame.display.set_mode(screen_size)
pygame.display.set_caption("2D shooter")


# Variable to set up a clock object that keeps track of time
clock = pygame.time.Clock()



# Variable to set up and scale the background image that makes up the map
background = pygame.transform.scale(pygame.image.load("Lords Of Pain/environment/ground.png.png").convert(), (MAP_HEIGHT,MAP_WIDTH))

crosshair = pygame.image.load("Premium top-down shooter asset pack\crosshair.png")
game_sprites = pygame.sprite.Group()



class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__() # Inherits the methods and attributes of the premade pygame player class
        self.image = pygame.transform.rotozoom(pygame.image.load("Premium top-down shooter asset pack\Player with AK.png").convert_alpha(), 0, player_size) # Creates and scales the image of the playable character onto the screen
        self.image_width = self.image.get_width()
        self.image_height = self.image.get_height()
        self.rect = self.image.get_rect() # Draws a rectangle around the character to be used for displaying the image, collisions, movement, etc.
        self.pos = vector(player_start_pos) # Sets the players position as a vector with direction and magnitude to enable movement
        self.original_character = self.image
        self.hitbox = self.original_character.get_rect(center = (self.image_width/2 , self.image_height/2)) # Creates the hitbox for the player
    def movementinputs(self):
        input = pygame.key.get_pressed()
        self.move_speedx = 0
        self.move_speedy = 0
        # When the player presses W, A, S, or D on their keyboard this method adds or subtracts a speed variable from the players position to create movement
        if input[pygame.K_w]:
            self.move_speedy -= player_speed
        if input[pygame.K_a]:
            self.move_speedx -= player_speed
        if input[pygame.K_s]:
            self.move_speedy += player_speed
        if input[pygame.K_d]:
            self.move_speedx += player_speed
        # The conditionals below normalize the velocity/speed of the  player when moving diagonally. Because of the pythagorean theorem, a player will move as fast as the player_speed variable times the square root of 2. By dividing the square root of 2 from the number we are able to cancel it out.
        if input[pygame.K_w] and input[pygame.K_a]:
            self.move_speedx /= math.sqrt(2)
            self.move_speedy /= math.sqrt(2)
        if input[pygame.K_w] and input[pygame.K_d]:
            self.move_speedx /= math.sqrt(2)
            self.move_speedy /= math.sqrt(2)
        if input[pygame.K_s] and input[pygame.K_a]:
            self.move_speedx /= math.sqrt(2)
            self.move_speedy /= math.sqrt(2)
        if input[pygame.K_s] and input[pygame.K_d]:
            self.move_speedx /= math.sqrt(2)
            self.move_speedy /= math.sqrt(2)
    def playermovement(self, between_frames):
        self.pos += vector(self.move_speedx, self.move_speedy) * between_frames # The position will be changed based on the keys pressed by the player and the frame rate is stabilized by multiplying the delta_time variable
        self.hitbox.center = self.pos
        self.rect.center = self.hitbox.center
    def rotation(self, cursor_pos):
        self.cursor_pos = pygame.mouse.get_pos()
        self.delta_x = (self.cursor_pos[0] - SCREEN_WIDTH / 2)
        self.delta_y = (self.cursor_pos[1] - SCREEN_HEIGHT / 2)
        self.angle = math.degrees(math.atan2(self.delta_y, self.delta_x))
        self.image = pygame.transform.rotate(self.original_character, (-self.angle + 90))
        self.rect = self.image.get_rect(center = (self.hitbox.centerx, self.hitbox.centery))


    def update(self, between_frames, cursor_pos):
        self.movementinputs()
        self.playermovement(between_frames)
        self.rotation(cursor_pos)


# Camera Class to allow for a scrolling effect
class Camera(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.offset = pygame.math.Vector2()
        self.bg_rect = background.get_rect(topleft = (background_pos))


    # Method to offset the background relative to players movement
    def move_bg(self):
        self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2  # Moves the background based on the center position of the player
        self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2

        bg_offset = self.bg_rect.topleft - self.offset
        display.blit(background, bg_offset)
        
        for sprite in game_sprites:  # This for loop allows the game to run through all sprites that are loaded in and updates the offset background
            bg_pos = sprite.rect.topleft - self.offset
            display.blit(sprite.image, bg_pos)

camera = Camera()
    
        

player = Player()
game_sprites.add(player)

pygame.mouse.set_visible(False)



game_running = True  # The game runs until this variable is false
# Main game loop
while game_running == True:
    cursor = pygame.mouse.get_pos()
    between_frames = clock.tick(FPS) / 1000 # This variable keeps players movement smooth regardless of the framerate. Because the clock.tick() function returns time in milliseconds, we need to divide by 1000 to convert back to seconds and that will give us the seconds between each frame that has been drawn. Using this we can multiply it by the position in order to assure the player moves the same speed even if FPS is slow or fast.

    # display.blit(background, background_pos) # Draws background
    camera.move_bg()
    game_sprites.update(between_frames, cursor)
    display.blit(crosshair, (cursor[0] - crosshair.get_width() // 2, cursor[1] - crosshair.get_height() // 2))
    

    # Quitting loop
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_running = False

    
    pygame.display.update() #Refreshes the screen


