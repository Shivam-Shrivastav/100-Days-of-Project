import pygame, sys, pymunk


pick = False
lx = 400
ly = 400
mx = 0
my = 0

def create_apple(space, x, y, pick, mx, my):
    print(mx, my)
    body = pymunk.Body(1, 100, body_type= pymunk.Body.DYNAMIC)
    if pick ==True:
        body.position = (mx, my)
    elif pick == False:
        body.position = (x, y)
    shape = pymunk.Poly.create_box(body, (30, 30), 0)
    space.add(body, shape)
    return shape
    

# def move_apple(space, apples, mx, my, pick, lx, ly):
#     for apple in apples:
#         if pick ==True:
#             apple.body.position = (mx, my)
#         elif pick == False:
#             apple.body.position = (lx, ly)
#         print(apple.body.position)
#         shape = pymunk.Poly.create_box(apple.body, (30, 30), 0)
#         shape.friction = 50
#         shape.elasticity = 0.7
#         space.add(apple.body, shape)
#         return shape




def draw_apples(apples):
    for apple in apples:
        pos_x = int(apple.body.position.x)
        pos_y = int(apple.body.position.y)
        apple_surface.fill((200, 100, 50))
        apple_rect = apple_surface.get_rect(center= (pos_x,pos_y))
        screen.blit(apple_surface, apple_rect)

def create_ground(space):
    body = pymunk.Body(body_type= pymunk.Body.STATIC)
    shape = pymunk.Segment(body, (-20, 700), (820, 700), 0)
    shape.friction = 50
    space.add(body, shape)
    return shape


pygame.init()
screen = pygame.display.set_mode((800, 800))
clock = pygame.time.Clock()
apple_surface = pygame.Surface([29.9,29.9])
space = pymunk.Space()
space.gravity = (0, 1)
apples = []
apples.append(create_apple(space, lx, ly, pick, mx, my))
print(type(apples[0]))
create_ground(space)


while True:
    for event in pygame.event.get():
        # screen.fill((0,0,0))
        mx, my, = pygame.mouse.get_pos()
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and lx-30<=mx<=lx+30 and ly-30<=my<=ly+30:
            pick = True
            print(mx, my)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            pick = False
            lx = mx
            ly = my
            print(mx, my)
            
        
    screen.fill((0,0,0))
    # move_apple(space, apples, mx, my, pick, lx, ly)
    draw_apples(apples)
    space.step(1/50)
    pygame.draw.rect(screen, (0,200,0), pygame.Rect(0, 700, 800, 700))



    
    pygame.display.update()

    
