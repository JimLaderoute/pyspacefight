import pygame,sys,math,random # importing modules
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

# COLORS
BACKGROUND = (217, 217, 217)

class Settings():
    def __init__(self):
        self.aimodel = 0
    def setAiModelNumber(self,modelnum):
        self.aimodel = modelnum
    def getAiModelName(self):
        return "ai"+str(self.aimodel)

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

    def ai3(self, points):
        # find which target we are heading for
        target = points[self.waypoint]
        # find the vector that the target is moving towards
        x0 = target.center.x
        y0 = target.center.y
        x1 = target.center.x + target.velocity.x
        y1 = target.center.y + target.velocity.y
        # now determine our robot's current vector
        rx0 = self.center.x
        ry0 = self.center.y
        rx1 = rx0 + self.velocity.x
        ry1 = ry0 + self.velocity.y
        # We want to adjust our angle so that it points to the target's location
        # we are only allowed to adjust our thrust boosters, we can't just
        # change our x,y velocities. And we have a max thrust and max velocity for
        # our object. We can't break the rules.
        dx = rx1 - x1
        dy = ry1 - y1
        distToTarget = math.sqrt( dx*dx + dy*dy)
        angleToTarget = math.atan2( dy, dx)
        lastd = WIDTH + HEIGHT
        for a in range(1,10):
            ax = -math.cos(angleToTarget) * ACCEL_AMOUNT * (a / 10.0)
            ay = -math.sin(angleToTarget) * ACCEL_AMOUNT * (a / 10.0)
            vx = self.velocity.x + ax
            vy = self.velocity.y + ay
            rx1 = self.center.x + vx
            ry1 = self.center.y + vy 
            dx = rx1 - x1
            dy = ry1 - y1 
            d = math.sqrt( dx*dx + dy*dy)
            if d < lastd:
                lastd = d
                last_ax = ax
                last_ay = ay

        self.accel.x = last_ax
        self.accel.y = last_ay


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
                    print("thedist num={}\n".format(thedist))
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




class Point():
    def __init__(self, pos, color, number):
        self.center = vec( (pos[0],pos[1])) 
        self.color = color
        self.count = number
        self.radius = WAYPOINT_RADIUS
        self.velocity = vec( (random.randint(0,20)/10.0,random.randint(0,20)/10.0) )

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
text_surface = font.render("Press 0 to set AI model to AI0.", True, (255,0,0))
text.append(text_surface)
text_surface = font.render("Press 1 to set AI model to AI1.", True, (255,0,0))
text.append(text_surface)
text_surface = font.render("Press 2 to set AI model to AI2.", True, (255,0,0))
text.append(text_surface)

any_mouse_clicked = False
pointCounter=0

while True: # Game Loop
    for event in pygame.event.get(): # checking for user input
        if event.type == QUIT: # input to close the game
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
            elif event.key == K_0:
                setting.setAiModelNumber(0)
            elif event.key == K_1:
                setting.setAiModelNumber(1)
            elif event.key == K_2:
                setting.setAiModelNumber(2)
            elif event.key == K_3:
                setting.setAiModelNumber(3)


        # Look for MOUSE CLICK events
        if event.type == MOUSEBUTTONUP:
            if event.button == LEFT:
                any_mouse_clicked = True
                pos = pygame.mouse.get_pos()
                pointCounter += 1
                points.append( Point(pos, (255,0,0),pointCounter))
            elif event.button == RIGHT:
                any_moude_clicked = True
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

    if not any_mouse_clicked :
        ypos = 10
        for t in text:
            text_rect = t.get_rect()
            text_rect.topleft = (10,ypos)
            screen.blit(t, text_rect)
            ypos += 25
    
    pygame.display.update() # rendering the frame
    clock.tick(FPS) # limiting the frames per second

