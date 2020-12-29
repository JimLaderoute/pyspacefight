import pygame,os,sys,math,random # importing modules
import pickle, neat
from pygame.locals import *  # pygame.locals.QUIT --> QUIT
vec = pygame.math.Vector2


TITLE = "Space Fight"
FONTNAME = "comicsansms"
FONTSIZE=24
WIDTH = 800
HEIGHT = 800
FPS = 60
LEFT = 1
RIGHT = 3
MIDDLE = 2

WAYPOINT_TIME = 800
MAX_VEL = 8
MIN_DISTANCE = 30
ROBOT_RADIUS = 10
WAYPOINT_RADIUS = 15
ACCEL_AMOUNT = 0.2
FUEL_UNITS_DEFAULT = 1000.0

# COLORS
BACKGROUND = (217, 217, 217)

class Settings():
    def __init__(self):
        self.aimodel = 0
        self.randomwaypoints = False
        random.seed(3)
    def setAiModelNumber(self,modelnum):
        self.aimodel = modelnum
    def getAiModelName(self):
        return "ai"+str(self.aimodel)
    def toggleRandom(self):
        self.randomwaypoints = not self.randomwaypoints

setting = Settings()

class Robot():
    def __init__(self, pos, color, aimodel):
        self.center = vec( pos )
        self.radius = ROBOT_RADIUS
        self.color = color
        self.velocity = vec((0,0))
        self.accel = vec((0,0))
        self.waypoint = 0
        self.aimodel = aimodel
        self.timepass=0
        self.score = 0      # how many targets it touched
        self.fuel = FUEL_UNITS_DEFAULT

    # Neural Network AI Model
    def ai5(self, points):
        # Created by Sam
        pickle_in = open("NNAIMODEL_4000.pickle", "rb")
        genome = pickle.load(pickle_in)
        local_dir = os.path.dirname(__file__)
        config_path = os.path.join(local_dir, "config-feedforward_4000.txt")
        config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                    neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                    config_path)
        net = neat.nn.FeedForwardNetwork.create(genome, config)

        outputs = net.activate((self.center.x, self.center.y, self.velocity.x, self.velocity.y,
                                    points[self.waypoint].center.x, points[self.waypoint].center.y,
                                    points[self.waypoint].velocity.x, points[self.waypoint].velocity.y))
        self.accel.x = outputs[0]/5.0
        self.accel.y = outputs[1]/5.0

    def ai4(self, points):
        # Created by Sam

        # Step waypoint into the future
        target = points[self.waypoint]
        distance = math.sqrt(math.pow(self.center.x - target.center.x, 2) + math.pow(self.center.y - target.center.y, 2))
        normDist = (distance/(WIDTH))#*math.sqrt(2)/2))

        # Depending on distance determine how far into the future to look
        future = normDist * FPS*2  # every FPS(60) = 1 second

        targX = target.center.x + target.velocity.x * future
        targY = target.center.y + target.velocity.y * future

        # step robot into the future?
        vRobotX = self.center.x
        vRobotY = self.center.y
        vRobotVX = self.velocity.x
        vRobotVY = self.velocity.y

        # Find angle of self to future waypoint
        dy = vRobotY - targY
        dx = vRobotX - targX
        angle = math.atan2(dy, dx)

        # Find vector to add to current vel that gives desired angle
        desV = vec()
        desV.x = vRobotVX - math.cos(angle)*MAX_VEL
        desV.y = vRobotVY - math.sin(angle)*MAX_VEL

        # Find acc that gives vel of that angle
        accX =  desV.x*normDist - vRobotVX
        accY =  desV.y*normDist - vRobotVY


        # set that acc
        if accX > ACCEL_AMOUNT:
            accX = ACCEL_AMOUNT
        if accX < -ACCEL_AMOUNT:
            accX = -ACCEL_AMOUNT
        if accY > ACCEL_AMOUNT:
            accY = ACCEL_AMOUNT
        if accY < -ACCEL_AMOUNT:
            accY = -ACCEL_AMOUNT

        # print (distance)
        if (normDist > 0.5):    # 260
            self.accel.x = accX
            self.accel.y = accY
        else:
            testBot = Robot(self.center, self.color, self.aimodel)
            best_d = WIDTH*3
            new_acc_x = ACCEL_AMOUNT
            new_acc_y = ACCEL_AMOUNT
            for i in range(-20,20):
                for j in range(-20,20):
                    # RESET VALUES
                    testBot.center.x = self.center.x
                    testBot.center.y = self.center.y
                    testBot.velocity.x = self.velocity.x
                    testBot.velocity.y = self.velocity.y
                    testBot.waypoint = self.waypoint

                    # SET TEST ACC
                    testBot.accel.x = i/100.0
                    testBot.accel.y = j/100.0

                    # UPDATE TEST BOT VEL AND LOCATION
                    testBot.update_speed()
                    testBot.center.x = testBot.center.x + testBot.velocity.x*future
                    testBot.center.y = testBot.center.y + testBot.velocity.y*future
                    # UPDATE TARGET LOCATION
                    newTargetX = points[testBot.waypoint].center.x + points[testBot.waypoint].velocity.x*future
                    newTargetY = points[testBot.waypoint].center.y + points[testBot.waypoint].velocity.y*future

                    # CHECK DISTANCE
                    tar = vec()
                    tar.x = newTargetX
                    tar.y = newTargetY
                    d = testBot.center.distance_to(tar)
                    if d < best_d:
                        best_d = d
                        new_acc_x = i/100.0
                        new_acc_y = j/100.0
            self.accel.x = new_acc_x
            self.accel.y = new_acc_y


    def ai3(self, points):
        target = points[self.waypoint]
        best_d = WIDTH * 2
        factor = 20.0
        best_accel_x = ACCEL_AMOUNT
        best_accel_y = ACCEL_AMOUNT
        accels = [ACCEL_AMOUNT/8.0, ACCEL_AMOUNT/4.0, ACCEL_AMOUNT/2.0, ACCEL_AMOUNT, -ACCEL_AMOUNT, -ACCEL_AMOUNT/2.0, -ACCEL_AMOUNT/4.0, -ACCEL_AMOUNT/8.0]
        test_bot = Robot(self.center, self.color, setting.getAiModelName() )
        for ay in accels:
            for ax in accels:
                test_bot.center.x = self.center.x
                test_bot.center.y = self.center.y
                test_bot.velocity.x = self.velocity.x
                test_bot.velocity.y = self.velocity.y
                test_bot.waypoint = self.waypoint
                test_bot.accel.x = ax
                test_bot.accel.y = ay 
                #--------------------------------------------
                test_bot.update_speed()
                test_bot.center.x += test_bot.velocity.x * factor
                test_bot.center.y += test_bot.velocity.y * factor 
                #--------------------------------------------
                d = test_bot.center.distance_to(target.center)
                if d < best_d:
                    best_d = d
                    best_accel_x = ax
                    best_accel_y = ay
                    if d < 200:
                        factor = 15.0
                    if d < 100:
                        factor = 10.0
        self.accel.x = best_accel_x
        self.accel.y = best_accel_y

    def ai2(self, points):
        self.ai1(points,True) # look ahead

    def ai1(self, points, lookAhead=False):
        target = points[self.waypoint]
        #print("in ai1 now\n")
        # try different accelerations from 0.01 to ACCEL_AMOUNT; after each
        # try, find the best in terms of how close to the waypoint we would get
        best_d = WIDTH * 2
        best_accel_x = ACCEL_AMOUNT
        best_accel_y = ACCEL_AMOUNT
        accels = [ACCEL_AMOUNT/4.0, ACCEL_AMOUNT/2.0, ACCEL_AMOUNT, -ACCEL_AMOUNT, -ACCEL_AMOUNT/2.0, -ACCEL_AMOUNT/4.0]
        test_bot = Robot(self.center, self.color, setting.getAiModelName() )
        for ay in accels:
            for ax in accels:
                test_bot.center.x = self.center.x
                test_bot.center.y = self.center.y
                test_bot.velocity.x = self.velocity.x
                test_bot.velocity.y = self.velocity.y
                test_bot.waypoint = self.waypoint
                test_bot.accel.x = ax
                test_bot.accel.y = ay 
                #--------------------------------------------
                test_bot.update_speed()
                test_bot.center.x += test_bot.velocity.x * 10
                test_bot.center.y += test_bot.velocity.y * 10
                #--------------------------------------------
                if lookAhead:
                    x = points[test_bot.waypoint].center.x
                    y = points[test_bot.waypoint].center.y 
                    thedist = min(200,int(test_bot.center.distance_to(points[test_bot.waypoint].center)))//3
                    for i in range(thedist):
                        points[test_bot.waypoint].update()
                    d = test_bot.center.distance_to(points[test_bot.waypoint].center)
                    points[test_bot.waypoint].center.x = x
                    points[test_bot.waypoint].center.y = y
                else:
                    d = test_bot.center.distance_to(points[test_bot.waypoint].center)
                if d < best_d:
                    best_d = d
                    best_accel_x = ax
                    best_accel_y = ay
                    #print("best d={} at ax{} ay{}\n".format(d,ax,ay))

        self.accel.x = best_accel_x
        self.accel.y = best_accel_y


    def ai0(self,points,accelvalue):
        target = points[self.waypoint]
        for i in range(2):
            if self.center[i] < target.center[i]:
                self.accel[i] = accelvalue 
            else:
                self.accel[i] = -accelvalue

    def update_speed(self):
        self.velocity.x += self.accel.x
        self.velocity.y += self.accel.y
        if abs(self.velocity.y) > MAX_VEL:
           self.velocity.y -= self.accel.y
        if abs(self.velocity.x) > MAX_VEL:
           self.velocity.x -= self.accel.x

    def update(self, points):
        self.timepass = (self.timepass + 1) % WAYPOINT_TIME
        if self.timepass==0:
            self.waypoint = (self.waypoint + 1) % len(points)
        else:
            # if we are within a certain distance of the waypoint, then
            # move on to the next one.
            distance = self.center.distance_to(points[self.waypoint].center)
            if distance < MIN_DISTANCE:
                self.waypoint = (self.waypoint + 1) % len(points)
                self.timepass = 0
                if self.score==0 or (self.score > 0 and len(points) > 1):
                    self.score += 1

        if self.aimodel =="ai0":
            self.ai0(points, ACCEL_AMOUNT )
        elif self.aimodel =="ai1":
            self.ai1(points)
        elif self.aimodel =="ai2":
            self.ai2(points)
        elif self.aimodel =="ai3":
            self.ai3(points)
        elif self.aimodel == "ai4":
            self.ai4(points)
        elif self.aimodel == "ai5":
            self.ai5(points)


        if self.fuel <= 0:
            self.accel.x = 0
            self.accel.y = 0
            self.fuel = 0
        else:
            f = math.sqrt( self.accel.x * self.accel.x + self.accel.y * self.accel.y )
            self.fuel -= f

        self.update_speed()
        self.center.x += self.velocity.x
        self.center.y += self.velocity.y

    def render(self, surface):
        pos = ( int(self.center.x), int(self.center.y) )
        # based on accel x,y draw lines
        pygame.draw.line(surface, self.color, pos, (pos[0]-int(300*self.accel.x), pos[1]))
        pygame.draw.line(surface, self.color, pos, (pos[0], pos[1]-int(300*self.accel.y)))
        pygame.draw.circle(surface, self.color, pos, self.radius)
        txtsurf = font.render(str(self.score), True, (0,0,0))
        txtrect = txtsurf.get_rect()
        txtrect.bottomleft= pos
        screen.blit(txtsurf,txtrect)
        txtsurf = font.render(self.aimodel, True, (0,0,0))
        txtrect = txtsurf.get_rect()
        txtrect.topright= pos
        screen.blit(txtsurf,txtrect)

        pygame.draw.rect(surface, (255,0,0), pygame.Rect(int(pos[0] - 20), int(pos[1] + 20), 100, 5))
        pygame.draw.line(surface, (0,255,0), (int(pos[0] - 20), int(pos[1] + 22)), (int(pos[0] - 20) + int(100*self.fuel//FUEL_UNITS_DEFAULT), int(pos[1] + 22)))


class Point():
    def __init__(self, pos, color, number):
        self.center = vec( (pos[0],pos[1])) 
        self.color = color
        self.count = number
        self.radius = WAYPOINT_RADIUS
        if setting.randomwaypoints:
            self.velocity = vec((random.randint(-20,20)/10.0,random.randint(-20,20)/10.0) )
        else:
            self.velocity = vec((0, 0))

    def update(self):
        self.center.x += self.velocity.x
        self.center.y += self.velocity.y
        if self.center.x > WIDTH:
            self.center.x = 0
        if self.center.x < 0:
            self.center.x = WIDTH
        if self.center.y < 0:
            self.center.y = HEIGHT
        if self.center.y > HEIGHT:
            self.center.y = 0

    def render(self,surface):
        pos = ( int(self.center.x), int(self.center.y) )

        pygame.draw.circle(surface, (55,55,55), pos, MIN_DISTANCE)
        if len(robots):
            for r in robots:
                if self == points[r.waypoint]:
                    pygame.draw.circle(surface, r.color, pos, MIN_DISTANCE)

        pygame.draw.circle(surface, self.color, pos, self.radius)
        txtsurf = font.render(str(self.count), True, (0,0,0))
        txtrect = txtsurf.get_rect()
        txtrect.center = pos
        screen.blit(txtsurf,txtrect)

pygame.init() # initiating pygame
screen = pygame.display.set_mode((WIDTH,HEIGHT)) # creating the display surface
pygame.display.set_caption(TITLE)
clock  = pygame.time.Clock() # creating the game clock
font = pygame.font.SysFont(FONTNAME, FONTSIZE)

points = [] 
robots = []

text = []
text_surface = font.render("Click Left Mouse Button to create WayPoints", True, (255,0,0))
text.append(text_surface)
text_surface = font.render("Click Right Mouse Button to create a Robot", True, (255,0,0))
text.append(text_surface)
text_surface = font.render("Press R to toggle random vel of waypoints.", True, (255,0,0))
text.append(text_surface)
text_surface = font.render("Press 0 to set AI model to AI0.", True, (255,0,0))
text.append(text_surface)
text_surface = font.render("Press 1 to set AI model to AI1.", True, (255,0,0))
text.append(text_surface)
text_surface = font.render("Press 2 to set AI model to AI2.", True, (255,0,0))
text.append(text_surface)
text_surface = font.render("Press 3 to set AI model to AI3.", True, (255,0,0))
text.append(text_surface)
text_surface = font.render("Press 4 to set AI model to AI4.", True, (255,0,0))
text.append(text_surface)
text_surface = font.render("Press 5 to set AI model to AI5.", True, (255,0,0))
text.append(text_surface)


def main():
    global points

    any_mouse_clicked = False
    show_help = True
    pointCounter=0

    while True: # Game Loop
        for event in pygame.event.get(): # checking for user input
            if event.type == QUIT: # input to close the game
                show_stats()
                pygame.quit()
                sys.exit()
            # look for keyboard events
            if event.type == KEYUP:
                if event.key == K_KP_ENTER or event.key == K_RETURN:
                   # clear all waypoints
                   points = []
                   pointCounter=0
                   screen.fill(BACKGROUND)
                   for r in robots:
                       r.waypoint = 0
                elif event.key == K_h:
                    show_help = not show_help
                elif event.key == K_r:
                    setting.toggleRandom()
                elif event.key == K_0:
                    setting.setAiModelNumber(0)
                elif event.key == K_1:
                    setting.setAiModelNumber(1)
                elif event.key == K_2:
                    setting.setAiModelNumber(2)
                elif event.key == K_3:
                    setting.setAiModelNumber(3)
                elif event.key == K_4:
                    setting.setAiModelNumber(4)
                elif event.key == K_5:
                    setting.setAiModelNumber(5)



            # Look for MOUSE CLICK events
            if event.type == MOUSEBUTTONUP:
                if event.button == LEFT:
                    if not any_mouse_clicked:
                        show_help = False
                    any_mouse_clicked = True
                    pos = pygame.mouse.get_pos()
                    pointCounter += 1
                    points.append( Point(pos, (255,0,0),pointCounter))
                elif event.button == RIGHT:
                    pos = pygame.mouse.get_pos()
                    robots.append( Robot(pos, (random.randint(0,255), random.randint(0,255),random.randint(0,255)), 
                        setting.getAiModelName()) ) 

        screen.fill(BACKGROUND) # background color

        if not len(points)==0:
            for p in points:
                p.update()
            for r in robots:
                r.update(points)
            for p in points:
                p.render(screen)

        for r in robots:
            r.render(screen)

        if show_help :
            ypos = 10
            for t in text:
                text_rect = t.get_rect()
                text_rect.topleft = (10,ypos)
                screen.blit(t, text_rect)
                ypos += 25
        
        pygame.display.update() # rendering the frame
        clock.tick(FPS) # limiting the frames per second

def show_stats():
    for r in robots:
        print( "Model: {}  score: {}  fuel: {}\n".format(r.aimodel,r.score,r.fuel))

if __name__ == "__main__":
    main()

