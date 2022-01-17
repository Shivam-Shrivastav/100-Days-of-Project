import pygame, sys, pymunk


def create_ground(space):
    body = pymunk.Body(body_type= pymunk.Body.STATIC)
    shape = pymunk.Segment(body, (-20, 700), (820, 700), 0)
    shape.friction = 50
    space.add(body, shape)
    return shape


def create_apple(space, x, y):
    body = pymunk.Body(1, 100, body_type= pymunk.Body.DYNAMIC)
    body.position = (x, y)
    shape = pymunk.Poly.create_box(body, (30, 30), 0)
    space.add(body, shape)
    return shape




def draw_apples(apples):
    for apple in apples:
        pos_x = int(apple.body.position.x)
        pos_y = int(apple.body.position.y)
        apple_surface.fill((200, 100, 50))
        apple_rect = apple_surface.get_rect(center= (pos_x,pos_y))
        screen.blit(apple_surface, apple_rect)


pygame.init()
screen = pygame.display.set_mode((800, 800))
clock = pygame.time.Clock()
apple_surface = pygame.Surface([29.9,29.9])
space = pymunk.Space()
space.gravity = (0, 1)
apples = []
apples.append(create_apple(space, 400, 400))
create_ground(space)



while True:
    for event in pygame.event.get():
        mx, my, = pygame.mouse.get_pos()
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    

    screen.fill((0,0,0))
    draw_apples(apples)
    space.step(1/50)


    pygame.draw.rect(screen, (0,200,0), pygame.Rect(0, 700, 800, 700))


    pygame.display.update()
