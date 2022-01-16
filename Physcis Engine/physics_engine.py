import pygame, sys, pymunk


def create_apple(space, pos):
    body = pymunk.Body(1, 100, body_type= pymunk.Body.DYNAMIC)
    body.position = pos
    # shape = pymunk.Circle(body, 30)
    shape = pymunk.Poly.create_box(body, (30, 30), 0)
    print(pos)

    shape.friction = 50
    shape.elasticity = 0.7

    space.add(body, shape)
    return shape

def create_ground(space):
    body = pymunk.Body(body_type= pymunk.Body.STATIC)
    shape = pymunk.Segment(body, (-20, 700), (820, 700), 0)
    shape.friction = 50
    space.add(body, shape)
    return shape


def draw_apples(apples):
    for apple in apples:
        pos_x = int(apple.body.position.x)
        pos_y = int(apple.body.position.y)
        apple_surface.fill((200, 100, 50))
        apple_rect = apple_surface.get_rect(center= (pos_x,pos_y))
        screen.blit(apple_surface, apple_rect)
def static_ball(space, x, y):
    body = pymunk.Body(body_type= pymunk.Body.STATIC)
    body.position = (x, y)
    shape = pymunk.Circle(body, 20)
    space.add(body, shape)
    return shape

def draw_static_ball(balls):
    for ball in balls:
        pos_x = int(ball.body.position.x)
        pos_y = int(ball.body.position.y)
        pygame.draw.circle(screen, (60,20,40), (pos_x, pos_y), 20)





pygame.init()
screen = pygame.display.set_mode((800, 800))
clock = pygame.time.Clock()
space = pymunk.Space()
space.gravity = (0, 120)
# apple_surface = pygame.image.load('small_apple2.png')
apple_surface = pygame.Surface([29.9,29.9])
apples = []

balls = []
balls.append(static_ball(space, 430, 450))
balls.append(static_ball(space, 248, 550))
create_ground(space)



lx = 400
ly = 700

while True:
    for event in pygame.event.get():
        screen.fill((217, 217, 217))
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            apples.append(create_apple(space, event.pos))

    
    screen.fill((217, 217, 217))
    draw_apples(apples)
    # draw_static_ball(balls)
    space.step(1/50)
    pygame.draw.rect(screen, (0,200,0), pygame.Rect(0, 700, 800, 700))
    pygame.display.update()
    clock.tick(120)
