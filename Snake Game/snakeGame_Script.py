import pygame
import random
x = pygame.init()


#Colours
white = (255, 255, 255)
red = (255, 0, 0)
black = (0, 0 , 0)

screen_width = 500
screen_height = 400
#Creating GameWindow
gameWindow = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("My First Game")

font = pygame.font.SysFont(None, 25)


def text_screen(text , color, x, y):
    screen_text = font.render(text, True, color)
    gameWindow.blit(screen_text, [x, y])

def plot_snake(gameWindow, color, snk_lst, snake_size):
    for x,y in snk_lst:
        pygame.draw.rect(gameWindow, color, [x, y, snake_size, snake_size])


#Creating a Game Loop
def gameloop():

    with open(r"C:\\Users\\Mahi\Documents\\Python\\Python-Projects\\PyGame\\FlappyBird\\highscore.txt", "r") as f:
        hiscore = f.read()
    
    #Game Specific Variable
    exit_game = False
    game_over = False
    snake_x = 45
    snake_y = 45
    snake_size = 10
    fps = 120
    velocity_x = 0
    velocity_y = 0
    init_velocity = 2

    food_x = random.randint(20, screen_width/2)
    food_y = random.randint(20, screen_height/2)
    score = 0
    snk_list = []
    snk_len = 1
    clock = pygame.time.Clock()


    while not exit_game:
        if game_over:
            with open(r"C:\\Users\\Mahi\Documents\\Python\\Python-Projects\\PyGame\\FlappyBird\\highscore.txt", "w") as f:
                f.write(str(hiscore))
            gameWindow.fill(white)
            text_screen("Game Over!! Press Enter to Continue", red, 100, 170)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        gameloop()

        else:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT:
                        velocity_x = init_velocity
                        velocity_y = 0
                        
                    elif event.key == pygame.K_LEFT:
                        velocity_x = -init_velocity
                        velocity_y = 0
                    elif event.key == pygame.K_UP:
                        velocity_y = -init_velocity
                        velocity_x = 0
                    elif event.key == pygame.K_DOWN:
                        velocity_y = init_velocity
                        velocity_x = 0

            snake_x = snake_x + velocity_x
            snake_y = snake_y + velocity_y 
            if abs(snake_x - food_x)<7 and abs(snake_y - food_y)<7:
                score += 10
                food_x = random.randint(20, screen_width/2)
                food_y = random.randint(20, screen_height/2)
                snk_len+=5
                if score>int(hiscore):
                    hiscore = score
            
            gameWindow.fill(white)
            head = []
            head.append(snake_x)
            head.append(snake_y)
            snk_list.append(head)



            if len(snk_list)>snk_len:
                del snk_list[0]
            
            if head in snk_list[:-1]:
                game_over = True
            if snake_x<0 or snake_x>screen_width or snake_y<0 or snake_y>screen_height:
                game_over = True
                print("Game over")

            text_screen("Score: "+str(score)+" High Score: "+str(hiscore), red, 5, 5 )
            # pygame.draw.rect(gameWindow, black, [snake_x, snake_y, snake_size, snake_size])
            pygame.draw.rect(gameWindow, red, [food_x, food_y, snake_size, snake_size])
            plot_snake(gameWindow, black, snk_list, snake_size)
        pygame.display.update()  
        clock.tick(fps)          

    pygame.quit()
    quit()

gameloop()



