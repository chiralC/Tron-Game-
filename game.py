from ursina import *    #ursina is a free 3D game engine for python
                        #"from ursina import *" means to import everything from the ursina library
from ursina.shaders import unlit_shader 
#the unlit_shader is a program in the ursina.shaders module that lets us create graphics which are not affected by lighting, i.e.
#shadows, lights do not have any effect on these graphics. they appear the same in all lighting conditions
import math
import random
import sys
#importing these modules (math,random,sys) for use further down the road

#what is __init__ : it is a constructor. also called a "dunder method". it starts and ends with a double underscore. 
#another example for a dunder method is the __str__ constructor. 

BIKE_COLORS = [{"name": "Tron Colors", "player": (0, 255, 230, 255), "ai": (255, 140, 0, 255)}]
#so BIKE_COLORS here a is a list containing dictionaries. these dictionaries have their "keys" as "name","player","ai". 
#the "name" key tells the colours in that theme(each dictionary in the list is a theme} in a readable format to the user
#the "player" and the "ai" key tells the colours in a format that is understandable to the computer, i.e. in RGBA tuple format,
#(R,G,B,A) R=Red,G=Green,B=Blue,A=Alpha. The value of Alpha controls how opqaue or transparent the color will be. 
#A=0 : Fully Transparent. A=110(ar any value inbetween 0 and 255) : Translucent. A=255 : Fully Opaque
#the key "player" indicates he colour for the car of the player(the user), and the key "ai" will be the colour for the ai cars

GRID_COLOR = (70, 200, 255, 255)     #bright neon blue grid
WALL_COLOR = (255, 200, 150, 110)    #peach orange colour

def color_tuple_to_color(t, alpha=None):
    # Converts a color tuple (0-255) to a Color in Ursina
    #so basically the colour palettes we just mentioned above are all in a format that is in integers from 0 to 255. 
    #the ursina game engine uses a different format. in this format the colours are represented by floating point numbers between 0.0 to 1.0
    #this color_tuple_to_color function, basically means "normalize" the colours to a format that is used by the ursina game engine. 
    r = max(0.0, min(1.0, (t[0]/255.0)))    #red will be the first item in the tuple t, hence t[0]
    g = max(0.0, min(1.0, (t[1]/255.0)))    #green will be the second item in the tuple t, hence we access it by t[1]
    b = max(0.0, min(1.0, (t[2]/255.0)))    #blue will be the third item in the tuple t, hence t[2]
    #basically max(0.0,...) so that the return value never becomes negative. 
    #and min(1.0,...) so that the return value never becomes greater than 1.0
    if len(t) > 3:  #if the tuple object len>3,i.e. it also contains the value for alpha
        a = max(0.0, min(1.0, (t[3]/255.0)))
    else:   #if the alpha is not defined in the tuple, then default value of a is set to 1.0 (fully opaque)
        a = 1.0
    if alpha is not None:
        a = max(0.0, min(1.0, alpha))
    return Color(r, g, b, a)

# Camera follows the player, always looking down but a little behind
class ChaseCam: #the class for a third person camera that follows the player's car
    def __init__(self, target_entity, dist=19, height=8, fov=95):
        #the distance and height are the parameters where the camera is viewing the player's car from
        #fov = fielf of view
        #here we have set the default values of these parameters
        self.target = target_entity
        self.dist = dist
        self.height = height
        #the ursina game engine provides a camera (global) object. basically this object is like the "eye" that watches the game. 
        #this object is provided by ursina. it is an instance object of the class Camera (built in class of Ursina library)
        camera.fov = fov
        camera.position = (0, height, -dist)    #position of the camera  (x,y,z) coordinates of the camera. 
        #x=0 meaning the camera is on the yz plane. 
        #y=height, meaning the height tells us the distance of the camera from the the plane in which the car is in (xz plane)
        #z=-distance, the positive z axis is out of the screen
        camera.rotation_x = 14  #rotation_x titls the camera to look up or look down (here we have tilted the camera to look
        #14 degrees downward) (similar to titling our head up and down to say yes)
        #EXTRA INFO
        #rotation_y tilts the camera to the left or to right (similar to tilting our head to the left and right to say no)
        #rotation_z tilts the camera to the sideways (similar to tilting our head towards our shoulder (like trying to touch our shoulder
        #with our head))
        #so camera.rotation_x or y or z - basically rotates the object, which is the "camera" here 
    def update(self):   #update is a method of the FollowCamera class
        #but the thing is that, update is a special built in name in the Ursina library that the Ursina automatically looks for
        #its job is to keep the position of the camera (the eye) updated so that it keeps on "following" the player's car
        if not self.target:     #if the player's car,i.e. self.target no longer exists(if it got destroyed), the update function/method must 
                                #no longer run so we can prevent the game from crashing
            return              #return statement here means that we exit this function. 
        pos = self.target.world_position - (self.target.forward * self.dist) + Vec3(0, self.height, 0)
        #the pos variable basically contains the real time data of the position where the camera should be 
        #self.target.world_position - the car's current position
        #self.target.forward - is basically a vector that is pointing in front of the car (to the direction in which the car is moving)
        #self.dist - we have already definde what this is (check line 48 of code)
        #self.target.world_position - (self.target.forward * self.dist) = this gives us a point that is at self.dist behind the player's car
        #and adding Vec3(0,self.height,0) adds height to this value. so now this point is at self.dist behind the player's car and at a 
        #height self.height above the player's car
        camera.position = lerp(camera.position, pos, time.dt * 5)
        #lerp = linear interpolation - what the lerp function does is that it moves the camera from the initial position - camera.position
        #towards a new target position - pos
        #basically instead of quickly zooming out or zooming in or moving, the lerp function basically does these things smoothly
        camera.look_at(self.target.world_position + Vec3(0, 1.2, 0))
        #look_at() is a standard built in method of the the Camera class of the Ursina library. 
        #basically what it does is that it tells the camera to aim at/"look at" the player's car. 
        #we do not have to calculate the rotation and all the other things to keep looking at the player's car becaues the look_at() 
        #does this job automatically. 
        #Side-to-side tilt based on A/D keys
        camera.rotation_z = lerp(camera.rotation_z, (held_keys['d'] - held_keys['a']) * 4, time.dt * 6)
        #basically tilts the camera based on how we use the A and D keys to move the car sideways. Now the use of the lerp() here is
        #that it makes the tilting process very smooth

# Grid lines on the ground (for style and reference!)
class Grid:
    #this class is basically used to print/display lines on the ground/floor/road and these lines will dynamically fade away as they
    #further away from the player's car. Basically the lines will smoothly disappear as they get further away from the player's car.
    def __init__(self, size=72.0, gap=18, thickness=0.5, fade=48):
        self.size = size                #size of the grid
        self.gap = gap                  #the gap/spacing between each lines in the grid
        self.thickness = thickness      #thickness of each of the lines in the grid
        self.fade = fade                #the distance from the player's car at which the lines should start to fade
        self.lines = []                 #an empty list created to hold all line objects(all objects created inside the create_list method)
        #self.lines is an instance variable (obviously since it is defined inside the __init__ (i.e. inside the class definition))
        base_color = color_tuple_to_color(GRID_COLOR, alpha=70/255.0)   #sets the colour of the lines in the grid
        self.create_lines(base_color)                                   #calls the create_lines method to create the grids

    def create_lines(self, base_color):
        for l in self.lines:    #making sure to delete all the old lines so we dont create any duplicates when we create new lines 
                                #when the car is moving forward. basically everytime the car moves the update() runs and we create new lines
                                #so we have to delete the old lines so as to prevent the old lines (?)
            destroy(l)          #destroy() is a built in function in the Ursina library that "destroys" an entity entirely/completely. 
        self.lines = []         #we again initialize the self.lines list to an empty list just to make extra sure that there are no old 
                                #lines left even after using the destroy()
        edge = int(self.size)   #edge is the total distance from the centre(origin) to the edge of the screen
        start = -edge - (-edge % self.gap if self.gap else 0)   #calculating the start and stop/end point for the grid to make sure the
                                                                #grid is centred with respect to the origin. 
        stop = edge - (edge % self.gap if self.gap else 0)      
        #how it works :
        #edge%eself.gap if self.gap else 0 - is basically nothing but
        #if self.gap!=0:    in python 0 is considered False and any other integer is considered True
        #   stop=edge-(edge%self.gap)
        #else:
        #   stop=edge-0
        #note that start is at -edge and stop is at +edge. This is the only difference between them. 
        span = 2 * edge         #the total size of the grid will be 2 times the edge by symmetry since from -ve x to origin to +ve x right
        for v in range(start, stop+1, self.gap):    #the control variable v takes the values in the range (will include 0 because
                                                    #start will be -ve and stop will be +ve). stop+1 so as v takes the the stop value also. 
            l1 = Entity(model='quad', rotation_x=90, color=base_color, x=v, y=0.01, scale=(self.thickness, span, 1), shader=unlit_shader)
            #l1 is the vertical line. 
            #model="quad" - we are telling the game engine Ursina to basically consider a square
            #x=v basically means that x keeps taking values of v in each iteration of the loop, while y stays the same(=0.01)
            #scale=(X,Y,Z) - the values of X,Y,Z is how much we stretch, i.e. the width along either of these directions of the shape will be
            #scale=(self.thickness, span,1) - so basically its thickness along the x axis(width of the line) will be equal to the thickness
            #value given by the user(self.thickness), and it will stretch it along the y axis(since "span") and along the z axis its width=1
            #not much importance to the z axis since these lines are basically in 2D, so we only need 2 coorindates set. 
            #so what we did is that we took a square and stretched it to make it a very thin line. 
            l2 = Entity(model='quad', rotation_x=90, color=base_color, z=v, y=0.01, scale=(span, self.thickness, 1), shader=unlit_shader)
            #l2 is the horizontal line.
            l1.texture = None
            l2.texture = None
            #basically makes the texture of the lines to be None,i.e. the lines are solid and dont have any patterns or anything. 
            self.lines.append(l1)
            self.lines.append(l2)

    def update_fade(self, player_pos):
    #this is the functon that is responsible for making the lines fade dynamically as they get further away from the  player's car
        for line in self.lines:
            d = abs(line.x - player_pos.x) if abs(line.scale_x - self.thickness)<0.01 else abs(line.z - player_pos.z)
            #basically
            #if abs(line.scale_x - self.thickness)<0.01:    #so that the thickness of the line is equal to or similar to the self.thickness
            #   d = abs(line.x - player_pos.x)
            #else:
            #   d = abs(line.z - player_pos.z)
            fade_factor = 1.0 - (d / self.fade) ** 2 if self.fade else 1.0 
            #d/self.fade normalizes the fade distance to between 0 and 1. 
            #if self.fade is None or =0 (i.e. False), then set the fade_factor to 1.0 else calculate its value by normalisation. 
            #1-d/self.fade to invert the value. if distance(d)=0(min), then fade_factor=1(max), and if d=1(max), then fade_factor=0(min)
            c = line.color
            line.color = Color(c.r, c.g, c.b, max(0.03, c.a if isinstance(c, Color) else 1.0) * max(0.0, fade_factor))
            #the r,g,b values are kept the same but the alpha value is re-calculated. 
            #alpha value is = c.a (the actual value if isinstance(c,Colour) is true. else it just sets the alpha value to 1.0
            #max(0.03,..) so that the alpha value is atleast 3%,i.e. we set a minimum base opacity for the lines

# Set up simple boundary box walls
class Boundary:
    #this class is basically for creating an invisible/semi visible walls to keep the cars inside the area. 
    def __init__(self, size=72.0, height=0.5, thickness=0.2):
        color_rgba = color_tuple_to_color(WALL_COLOR, alpha=110/255.0)
        edge = size     #how far the boundary is from the centre(origin (0,0))
        span = 2*edge   #the total length of the boundary from start(-ve x) to end(+ve x)
        h = height/2.0  #half the height(so that the base is on the ground(note that we assume that the car is at the centre))
        self.walls = [Entity(model='cube', shader=unlit_shader, color=color_rgba, position=(0, h, edge), scale=(span, height, thickness)),
                    Entity(model='cube', shader=unlit_shader, color=color_rgba, position=(0, h, -edge), scale=(span, height, thickness)),
                    Entity(model='cube', shader=unlit_shader, color=color_rgba, position=(edge, h, 0), scale=(thickness, height, span)),
                    Entity(model='cube', shader=unlit_shader, color=color_rgba, position=(-edge, h, 0), scale=(thickness, height, span))]
        
                    #each entity is a wall line. and the list named self.walls contain these wall lines. these walls are defined in a
                    #way similar to that in lines of code 127 and 136
# Leaves a glowing trail behind your bike
class Trail:
    def __init__(self, color, width=0.28, alpha=0.58, min_segment=0.16):
        self.width = width  #how wide the trail should be
        self.min_segment = min_segment  #self.min_segment - this stores the minimum distance the car should travel before a trail is drawn
        #this prevents the game from drawing lots of trails even for a small movement 
        self.last_pos = None    #self.last_pos will remember where the last trail was left off at/dropped at. 
        #it is initialized to None because no trails have been created up until now. 
        self.segments = []  #an empty list to hold/contain the data/info for each trail segment, like its position and direction, 
                            #like the x,y,z coordinates etc. 
        self.visuals = []   #an empty list that will hold/contain the actual visual objects that get drawn/displayed on the screen
                            #like the actual 3D models that the game engine renders. 
        self.color = color_tuple_to_color(color, alpha=alpha)   #the color of the trail. 

    def add_segment(self, a: Vec3, b: Vec3):
        #this method is called repeatedly for drawing the trails on the ground. 
        #this method takes two arguments a- the previous position(self.last-pos) and b- the current position
        #Vec3 is shortfrom for Vector 3. Vec3 is a data type in the Ursina library. It is basically an object that holds three numbers
        #which are always either int or float.  basically Vec3 holds in the format (x coordinates,y coordinates, z coordinates)
        d = Vec3(b.x-a.x, 0, b.z-a.z)   #calculates the distance between two points only on the ground plane(the rood/floor(XZ plane))
                                        #it ignores any height difference by setting the y coordinates to 0. all this is assigned to "d"
        length = math.hypot(d.x, d.z)   #calculates the 2D length of the trail using the Pythoagorean theorem. 
                                        #hypnot(a,b) returns the hypotenuse say c= root of a^2+b^2
        if length < self.min_segment: return
        #so basically if the length of the trail is less than the min distance required to be travlled by the car to leave behind a trail
        #then return None,i.e. to not create any trails. 
        mid = (a + b) / 2   #mid is the midpoint of the start and end of the trail. this is where the new trail will begin at. 
        angle = math.degrees(math.atan2(d.x, d.z))  
        #math.atan2 calculates the angle of the vector d
        #atan2(a,b) gives you the arctan of y/x,i.e. tan inverse(y/x). here we get tan inverse(d.x/d.z). d.x gives x component of d. 
        #d.z gives z component of d. 
        #math.degrees() converts the angle returned by math.atan2 which will be in radian into degrees. 
        #we convert the angle from radian into degrees because degrees is the format which the Ursina game engine understands. 
        seg = Entity(model='quad', shader=unlit_shader, color=self.color,
                     position=Vec3(mid.x, 0.06, mid.z),
                     rotation=Vec3(90, angle, 0),scale=Vec3(self.width, length, 1)) #creating the actual trail Entity visible to us
        #basically seg is the variable that holds the visual trail which we can see in the game
        #Entity is the name in the Ursina game library for an object which exists in the game world. 
        seg.texture = None  #no specific texture or pattern for the trail. just plain. 
        self.visuals.append(seg)    #adding the new visual object contained in the variable seg in our visuals list which contains all the 
                                    #visual objects in the game we have created. 
        self.segments.append((Vec2(a.x,a.z), Vec2(b.x,b.z)))    #appending the 2D coordinates of the starting point of the trail (a) and
                                                                #the ending point of the trail(b). 
        if len(self.visuals)>1000: destroy(self.visuals.pop(0)) #if the trail has more than 1000 visual pieces it destroys the 1st one. 
        if len(self.segments)>1000: self.segments.pop(0)        #it removes the oldest segment's data to keep adding data of new segments. 

    def step(self, pos3d: Vec3):    
        #the step method is called on every frame of the game to update the trail based on the car's new position (pos3d)
        p = Vec3(pos3d.x, 0, pos3d.z)   #creates 2D vector of the car's current position ignoring the height (y=0)
        if self.last_pos is None:       #if there is no value for self.last_pos/no value has been set for self.last_pos
            
            self.last_pos = p           #then it sets the current position of the car to the last position
            return                      #it returns nothing, i.e. exits the function because no trail can be drawn since there's only 
                                        #one point. 
        d = p - self.last_pos           #the 2D vector(distance and direction) the car has moved since the last frame of the game. 
        dist = math.hypot(d.x, d.z)     #it calculates the length of that motion/movement using Pythogorean 
        if dist >= self.min_segment*2.5:#if the car has moved a distance greater than or equal to the minimum distance required to be 
                                        #moved by the car to leave behind a trail time 2.5. 
                                        #WHY MULTIPLY BY 2.5?
                                        #Threshold check: only when the movement distance is large enough do we treat it specially. Multiplying self.min_segment by 2.5 creates a tolerance margin above the basic segment length. Practically this does three things: Filters tiny jitter: prevents creating many tiny segments when movement is negligible.Detects large moves: flags cases where the car jumped or moved a lot between samples (fast motion, lag, or a sharp turn).Controls smoothing subdivision: if the movement is substantially larger than min_segment, subdivide it into multiple smaller segments for a smooth trail rather than one long segment.
                                        #a lag spike due to car making a sharp turn or just a normal segment. 
                                        #if it is a normal segment spike, then follow the if block, since if conditoin will be true
                                        #otherwise follow the else block. 
            steps = max(2, int(dist / self.min_segment))    #decides how many segments to create
            prev = self.last_pos                            #the previous position of the player's car 
            #the loop below repeatedly calculates small steps and calls the self.add_segment method on each step so as to create/draw a
            #very smooth curve/line/segment which is the trail instead of creating just a long straight line. 
            for _ in range(steps):
                nxt = Vec3(prev.x + d.x/steps, 0, prev.z + d.z/steps)
                self.add_segment(prev, nxt)
                prev = nxt
            self.last_pos = prev    #the new final positon(prev) is assigned as the last position of the car. 
                                    #this repeatedly happens everytime the loop runs. 
        else:   #else block if the car has moved a straught 
            self.add_segment(self.last_pos, p)  #just basically add a new segment from the last positoin to the current position
            self.last_pos = p                   #and then assign the current position as the last position of the player's car. 

    def clear(self):
        #this function is basically a reset button to clear all the trails when we reset the game/end the game/race and start a new game/race. 
        for e in self.visuals:
            destroy(e)          #destroys every element present in the self.visuals list which contains all the visual elements created
                                #in a single run of the game/race. 
        self.visuals.clear()    #completely clears the list
        self.segments.clear()   #completely clears the list
        self.last_pos = None    #resets the last position of the car to None. 

    def collides(self, pos3d: Vec3, skip_recent=10, radius=0.30):
        #the job of this function is to check if the car at pos3d has hit any of its older trails. 
        #if it has hit any of its older trails, then the game is over. 
        # Check if pos3d hits the trail except very recently created segments
        if len(self.segments)<=skip_recent: #skip_recent means to skip 10 of the recent segments. 
                                            #so that we check only if the car has hit any of the older segments. 
            return False
        #basically we consider the player's car as a 2D circle. and if this 2D circle touches any of the older trail segments, then
        #the game is over. 
        p = Vec2(pos3d.x, pos3d.z)  #we are converting the 3D position, basically the car into a 2D point on the ground/floor/road. 
        r2 = radius*radius          #the variable r2 holds the square of the radius. calculating the square of the radius to find the 
                                    #square root later rather than using the math.sqrt() since this is more optimized way. 
        for a, b in self.segments[:-skip_recent]:   #creates a nested list containing all the segments other than the 10 recent
                                                    #segments since we used skip_recent. 
            ab = b - a      #vector ab = b-a (vector representing the trail segment from a to b)
            ap = p - a      #vector ap = p-a
            ab2 = ab.x*ab.x+ab.y*ab.y   #ab2 is the variable that holds the squared length of vector ab (square of magnitude of vector ab)
            if ab2 <= 1e-6:             #basically saying that if ab2 is a point, i.e both ab2 segment has its start and end point almost
                                        #the same. 1e-6 is a notation in programming to represent a very small +ve number. 
                                        #we didn't use if ab2==0 since ab2 could be ==0.00000000001 and still the condition would be False
                if ap.x*ap.x+ap.y*ap.y <= r2: return True   #if ap2 is less than the square of the radius of the player's car. 
                continue                
            #finding the closest point to the player's car on the line segment ab
            t = max(0.0, min(1.0, (ap.x*ab.x+ap.y*ab.y)/ab2))   #t will always be positive and range of t is [0,1]
            #ap.x*ab.x+ap.y*ab.y is the dot product of ab and ap
            #(ap.x*ab.x+ap.y*ab.y)/ab2 is the projection of the point ap on the vector ab
            #HOW DOES IT WORK(?)
            cx, cy = a.x + ab.x*t, a.y + ab.y*t
            #cx and cy are the actual x and y coordinates of this point of collision
            dx, dy = p.x-cx, p.y-cy
            #dx and dy are the distance between the points of collision(cx,cy) and the player's car. 
            if dx*dx+dy*dy <= r2: return True
            #if the squaer of the distance between the player's car and the point of collision on the line is less than or equal to the 
            #radius of the circle, then there will be a collision. 
        return False    #after the loop checks all the segments and then if no collisions are found, then the car is safe and the game
                        #keeps on running. then the function must return False since there was no collision right. 

def bike_glow(col, scale=(1.5,1.5), y=0.02):
    #this function basically creates a glow effect under the player's car/bike. 
    c = color_tuple_to_color(col, alpha=90/255.0)   #basically taking the "col" argument taken by the function and converting it into a 
                                                    #colour object by using the color_tuple_to_color function we defined earlier. 
                                                    #basically the col argument will be in the form of a tuple. we will convert this tuple
                                                    #into an object having the Color class(inbuilt class in the Ursina library)
    return Entity(model='circle', color=c, rotation_x=90, scale=scale, y=y, shader=unlit_shader, texture=None)
    #so now we are returning the glow effect. we are creating an Entity(refer to line of code 215)
    #shader=unlit_shader basically we are telling this Entity(the glow effect) to ignore all the lighting and shadows in the game
    #refer to beginning of code to understand what the unlit_shader is. 
    #rotation_x=90, so that it lies flat on the ground instead of standing upright. 
    #y=y=0.02 (default value when we defined the function). we are placing the glow slightly above the ground to prevent it from flickering
    #with the road texture. 

class PlayerBike(Entity):
    #this is the class that has everything related to the player's car/bike. 
    #PlayerBike is a subclass of the Entity parent class. and Entity is a predefined class in the Ursina library.
    def __init__(self, col, start=(-14,0.5,0)):
        #super() is a built in function in the Python library. 
        #it lets us invoke the method of the parent class. 
        #basically if the parent class has a useful method but for some specific reason in the subclass we need to return the contents
        #of the parent class method but also we need to add some extra things to return when we call this method, we use the super()
        super().__init__(model='cube',
            color=color_tuple_to_color(col, alpha=1.0),
            scale=(0.8,0.8,2.3),
            position=start,
            shader=unlit_shader)
        self.base_col = col
        self.speed = 10.5                   #current speed of the bike
        self.accel = 1.3                    #acceleration of the bike
        self.max_speed = 30.0               #maximum speed of the bike
        self.turn_speed = 175.0             #how fast the bike can turn
        self.alive = True                   #a variable that tells if the bike is alive or not(i.e. if it has crashed or not)
        self.trail = Trail(self.base_col)   #we are creating a new instance of the Trail class we have just defined with the colour of
                                            #the trail as the base colour. and we are assinging this instance of the Trail class to the
                                            #instance variable named as self.trail. and self.trial is a variable in the PlayerBike class. 
                                            #so now we can call the methods of the PlayerBike class on the self.trail variable. 
        self.glow = bike_glow(self.base_col)

    def reset(self, pos=(-14,0.5,0), rot=0):
        #this method is used to reset everything related to the player's bike after a crash or when we reset the game or start a new race
        #we reset the position and the rotation of the bike(to 0)
        self.position = pos         #default position already defined in the definiton of the reset method. 
        self.rotation = (0,rot,0)   #rotation along all axes is 0
        self.speed = 10.5
        self.trail.clear()  #clears the trail when we reset everything (obviously)
        self.alive = True   #obviously when the game restarts the player is alive
        self.color = color_tuple_to_color(self.base_col, 1.0)
        self.glow.position = (pos[0], 0.02, pos[2]) #resets the glow position also (obviously)

    def step(self, dt):
        #this method runs in every single frame of the game and handles all the input(from the player) and the movement of the bike. 
        if not self.alive: return   #if not self.alive means if self.alive==False: then return None (return simply means return None)
                                    #return statement is used means that we exit the function (obviously if the player is not alive
                                    #the step method must not keep running right? YES)
        self.speed = min(self.max_speed, self.speed + self.accel * dt)  #this line handles the acceleration of the player's bike
        #how does it work?
        #dt is the time elapsed
        #self.accel*dt is the speed to be added to the current speed in this current frame. since acceleration is basically d(speed)/dt.
        #so multilpying acceleration by dt we get d(speed). 
        #self.speed+self.accel*dt - we are adding the increased speed to the current speed(self.speed)
        #but the current speed can never be greater than the max speed(self.max_speed) right? therefore we do min(self.max_speed,..)
        #basically we are updating the self.speed in each frame(since the step method runs in each method of the game)
        fwd = (1 if held_keys['w'] else 0) - (1 if held_keys['s'] else 0)
        #fwd is basically like the accelerator of the player's car/bike. 
        #fwd=1 if held_keys["w"] - means if the w key is pressed then the value of fwd=1 else it is 0. 
#??????        #CASE SENSITIVE NAHI KARNA HEI???? W or w must have same effect right?
        #if fwd=1 it is like accelerate     (forward)
        #if fwd=-1 it is like deccelerate   (reverse)
        #if fwd=0 it is like neutral.       (neutral)
        if held_keys['a']: self.rotation_y -= self.turn_speed * dt
        if held_keys['d']: self.rotation_y += self.turn_speed * dt
        self.position += self.forward * (fwd * self.speed * dt)
        #how we are adding to the position of the player's car/bike with respect to the fwd value. 
        #(fwd * self.speed * dt) - is basically the distance the bike should travel in each frame. 
        #if fwd=1 then it will move the distance self.speed*dt forward
        #if fwd=-1 then it will move the distance self.speed*dt in the reverse direction(since fwd=-1)
        #if fwd-0 then it will stay in the same position
        #self.speed*dt is change in position right. since speed=d(position)/dt
        #forward is an attribute/property that is pre built in the Entity class. 
        #basically it is a Vec3(Vector in 3D) that always points in the forward direction. 
        #self.position += self.forward * (fwd * self.speed * dt) - calculates where the player's car/bike should be in the next frame. 
        self.trail.step(self.position)  #we also have to call the step method on the trail object too so that it updates along with 
                                        #player's bike/car. 
        self.glow.position = (self.x, 0.02, self.z) #applying the position method on the glow object too so that it matches with the 
                                                    #position of the player's car/bike. the y coordinate of the glow stays the same. 

    def die(self):
        self.alive = False  #basically if the self.alive is False means that the player's bike has crashed
        self.color = color_tuple_to_color((255,60,60,255), alpha=1.0)

class AIBike(Entity):
    #AIBike is the subclass of the Entity parent class. 
    #AIBike is the bike that is controlled by the computer/AI. this is the opponent to the player's car'/bike. 
    #Basically same as the PlayerBike class but we have made a few changes for it to have its own "brain". 
    def __init__(self, col, arena_bounds=72.0, start=(14,0.5,0)):
        super().__init__(model='cube',
            color=color_tuple_to_color(col, alpha=1.0),
            scale=(0.8,0.8,2.3),
            position=start,
            shader=unlit_shader)
        self.base_col = col
        self.speed = 11.0
        self.max_speed = 30.0
        self.turn_speed = 170.0
        self.arena_bounds = arena_bounds    #this is a new thing we have defined. this is not present in the PlayerBike class. 
                                            #this is basically so that the AI knows the bounds of the arena so that it knows when to turn
                                            #away from the walls. 
        self.alive = True                   #just like the PlayerBike the AIBike also has this. 
        self.trail = Trail(self.base_col)   #same as PlayerBike
        self.timer = 0.0    #this is a simple timer and we have initialized this to 0.0 seconds.              
        self.think_interval = random.uniform(0.18,0.42) #this is a randomized timer. the AI Bike will make a decision randomly like to make
                            #a turn at a random interval between 0.18 and 0.42 seconds. 
                            #random.uniform(a,b) is used to get a floating point number between a and b (both a and b included)
        self.turning = 0    #this is a variable to store the current action of the AI
                            #if self.turning=0 - go straight
                            #if self.turning=1 - turn to the right
                            #if self.turning=-1 - turn to the left
        self.glow = bike_glow(self.base_col)        #same as PlayerBike

    def reset(self, pos=(14,0.5,0), rot=180):
        #this function(actually it is a method (obviosly)) is basically used to reset the AI after we crash or start a new race/ restart. 
        #basically same as PlayerBike  
        self.position = pos
        self.rotation = (0,rot,0)
        self.trail.clear()
        self.timer = 0.0
        self.turning = 0
        self.speed = 11.0
        self.alive = True
        self.color = color_tuple_to_color(self.base_col, alpha=1.0)
        self.glow.position = (pos[0], 0.02, pos[2])

    def step(self, dt):
        #the step method runs on every frame of the game (dt)
        if not self.alive: return   #same as PlayerBike
        self.timer += dt            #basically an automatic timer is setup when this method runs/is called. 
        near_wall = False           #intializing that the AIBike is near the wall is False(i.e. it is not near the wall(not about to crash))
        ahead = self.world_position + self.forward * 7.0    #basically we are creating a sensor point at a distance 7 units from the
                                                            #player's bike's position. 
        #self.forward is a forward vector of 1 unit length that points in the current direction that the AI Bike is facing. 
        #so self.foward * 7 basically now makes it a vector of magnitue(length) 7 units (mulitplying a vector with a scalar concept)
        #so now we have a vector of length 7 unit that points in the current direction that the AI Bike is facing/pointing at. 
        #self.world_position gives the current absolute position of the object self in the game world
        #so self.world_position + self.forward*7.0 = ahead. so ahead is basically a 3D coordinate point that is always at a distance of 7
        #units from the current position of the AI Bike. 
        #ANSWER : Because self.position gives the position of the object self with respect to/relative to its parent. 
        #If AIBike doesn't have any parent class then self.position and self.world_position will basically give the same position. 
        if abs(ahead.x)>self.arena_bounds-5 or abs(ahead.z)>self.arena_bounds-5:    #checking if the x or y coordinate of this area is
            #outside of the arena_bounds-5. why do we substract 5? because just to make sure that the AI Bike turns earlier. 
            #it has to turn earlier so that it has enough time and space to make the turn. 
            near_wall = True    #so in case the if condition i true, then near_wall = True(i.e. the AI Bike is near the walls)
        if self.timer>=self.think_interval: #the AI only has to think to make a decision(like whether to make a turn) only when the
            #timer runs out. 
            self.timer = 0.0    #when the timer runs out, we reset the timer back to 0.0 seconds. 
            self.think_interval = random.uniform(0.18,0.42) #we start the timer again. 
            self.speed = max(8.0, min(30.0, self.speed + random.uniform(-1.1,1.1))) #it randomly chooses a speed for the AI Bike. 
            #the minimum speed of the AI bike is 8.0 metres/second. the maximum speed of the AI Bike is 30.0 metres/second. 
            if near_wall:   #basically means if near_wall==True:
                self.turning = random.choice([-1,1])
                #random.choice(sequence=list,tuple,string). it chooses any item from the sequence. each item in the sequence has an
                #equal probability of being chosen. 
                #if is near a wall the value of self.turning will be chosen on random, i.e. whether to turn to the left or to the right
                #will be chosen on random. 
                #self.turning=1 means to turn to the right
                #self.turning=-1 means to turn to the left

            else:   #if there is no wall nearbye, it can either choose to turn to either sides or to go straight. 
                self.turning = random.choices([0,-1,1],[0.7,0.15,0.15])[0]
                #if self.turning=0 means to go straight
                #self.turning=1 means to turn to the right
                #self.turning=-1 means to turn to the left
        if self.turning:    #basically means if self.turning=True(any integer other than 0)
                            #so it BASICALLY MEANS if self.turning!=0, i.e. if the AI Bike chooses not to go straight
            self.rotation_y += self.turning * self.turn_speed * dt
            #self.turning * self.turn_speed * dt - basically self.turning value = either 1 or -1 and then multiply it with the distiance
            #to (since self.turn_speed*dt gives the distance to turn)
            #this result is being added to the self.rotation_y, i.e. the rotation of the AI Bike.
        self.position += self.forward * (self.speed * dt)
        #self.speed * dt is the change in position of the bike, i.e. the distance that the bike should move in each frame(in dt time)
        #self.forward - already described (vector in the direction in which the AI Bike is facing/moving in)
        #basically same concept as the PlayerBike
        #just that we don't have to worry about whether this self.speed*dt distance is to be travelled forward or in reverse unlike
                                                                                                                    #in PlayerBike
        self.trail.step(self.position)                  #same as PlayerBike
        self.glow.position = (self.x, 0.02, self.z)     #same as PlayerBike

    def die(self):  #same as PlayerBike
        self.alive = False
        self.color = color_tuple_to_color((255,120,50,255), alpha=1.0)

class TronGame:
    def __init__(self):
        window.color = color.black              #we are setting the colour of the main window's background to black. 
        DirectionalLight().enabled = False      #we are turning off the default DirectionalLight (like the sun)
        AmbientLight(color=color.rgb(0,0,0))    #we are adding an ambient light. 
        #basically we are trying to bring the classic tron game theme to our game by setting these colours. 
        self.bounds = 72.0                      #setting the size of the arena. 
        self.grid = Grid(size=self.bounds)      #creating the Grid for the floor. Grid is a class we created. 
        self.walls = Boundary(size=self.bounds) #Creating the boundary walls. Boundary is a class we created. 
        col_player = BIKE_COLORS[0]["player"]   #
        col_ai = BIKE_COLORS[0]["ai"]
        self.player = PlayerBike(col=col_player)    #creating the object for player's bike using the PlayerBike class. 
        self.ai = AIBike(col=col_ai, arena_bounds=self.bounds)  #similary with the AIBike class. 
        #self.player is now a PlayerBike class object that is an instance variable of the TronGame class.  
        #self.ai is now an AIBike class object that is an instance variable of the TronGame class. 
        self.player.reset() #bringing the self.player to start position. 
        self.ai.reset()     #bringing the self.ai to start position.
        self.cam = ChaseCam(self.player)    #creates an object of class ChaseCam to chase the player's bike. 
        self.over = False                   #self.over = False since the game is running. If/when the game is over, it will be = True. 
        #below are basically code for menu ui
        self.menu_panel = None             
        self.status = Text("", origin=(0,0), scale=1.5, y=0.42, color=color.white)  
        self.hint = Text("W/S move • A left • D right • Q reset", origin=(0, -0.5), x=0, y=-0.47, scale=0.85, color=color.rgba(255,255,255,150))
        self.win_color = color_tuple_to_color(col_player, alpha=1.0)
        self.lose_color = color_tuple_to_color(col_ai, alpha=1.0)

    def clamp(self, thing):
        #this is a method that "clamps" the value of "thing" to be inside the boundary/to be smaller than b and larger than +b. 
        #the clamp method takes an argument "thing" and makes sure it does not go out of the boundaries, i.e. makes sure its x and z stay
        #inside the arena's boundaries. 
        b = self.bounds
        #thing.x returns the x coordinates of the point "thing"
        thing.x = max(-b, min(b, thing.x))  #thing.x will always be between -b and +b
        #thing.z returns the y coordinates of the point "thing"
        thing.z = max(-b, min(b, thing.z))  #thing.z will always be between -b and +b

    def check_collisions(self):
        # Player runs into their own trail's or the AI Bike's trail, then the player dies. 
        skip = 10   #this tells method when it checks for if collision with the trail has occured, to skip the recent 10 trails
        rad = 0.30  #this is the radius of the player's bike when it is considered as a 2D circle. 
        if self.player.alive and (self.player.trail.collides(self.player.position, skip, rad) or self.ai.trail.collides(self.player.position, skip, rad)):
            #if self.player.alive means if self.player.alive==True, i.e. if the player's bike is alive.
            #and if either the player's bike has collided with its own trail OR if the player's bike has collided with the trail of the AI bike
            self.player.die()   #then the player must die
            self.end_game()     #and the game must end. i.e. GAME OVER. 
        if self.ai.alive and (self.ai.trail.collides(self.ai.position, skip, rad) or self.player.trail.collides(self.ai.position, skip, rad)):
            #if self.ai.alive means if self.ai.alive==True, i.e. if the ai player is still alive. 
            #and if either the ai bike has collided with its own trail OR if the ai bike has collided with the player's bike's trail. 
            self.ai.die()   #then the ai player must die
            self.end_game() #and the game must end. i.e. GAME OVER. 

    def restart(self):
        #this function is basically to reset the game menu and all that stuff when the game ends/race ends. 
        if self.menu_panel:             #if self.menu_panel still exists on the screen
            destroy(self.menu_panel)    #we destroy it
            self.menu_panel = None      #and we reset the self.menu_panel variable to None. 
        self.over = False               #if the game is not over, i.e. if the game is still going on
        self.player.reset()             #it resets everything related to the player. 
        self.ai.reset()                 #it resets everything related to the ai. 
        self.status.text = ""           #it clears the "You win" or "You lose" status on the screen to nothing (hence an empty string). 
        self.player.trail.clear()       #it clears the trail of the player
        self.ai.trail.clear()           #it clears the trail of the ai

    def end_game(self):
        #this method/function is called everytime a crash occurs. the job of this function is to basically figure out who won the current
        #game, the player or the ai. 
        if self.over: return    #if self.over==True, then return to exit the function. 
        self.over = True        #else we end the game. and this now stops the update() from running anymore. 
        if not self.player.alive and not self.ai.alive: #if self.player.alive==False and self.ai.alive==False:
            self.status.text = "DRAW"   #then self.status.text, i.e. the status to be shown on the screen is "DRAW"
                                        #(since both the player and the ai died)
            self.status.color = color.yellow    #basically the color in which the status is to be shown on the screen. 
        elif not self.player.alive:                 #if onlt the player is not alive, then the ai wins. 
            self.status.text = "AI WINS"
            self.status.color = self.lose_color     #if only the ai is not alive, then the player wins. 
        elif not self.ai.alive:
            self.status.text = "YOU WIN"
            self.status.color = self.win_color
        self.show_menu()                            #now we show the menu after the game is over so as to exit or start a new game/race

    def show_menu(self):
        #this is the menu that appears on the screen after the game is over. 
        panel = Entity(parent=camera.ui, model='quad', color=Color(0,0,0,0.7), scale=(1.2, .6), z=0)    
        Text(parent=panel, text="Match Over", scale=2.0, y=0.22, origin=(0,0), color=color.white)
        Text(parent=panel, text=self.status.text, scale=1.5, y=0.0, origin=(0,0), color=self.status.color)
        #this is basically the main background panel for the menu. 
        def do_restart(): self.restart()    #these are wrapper functions. they are created so as to pass these to the buttons.
        def do_exit(): sys.exit(0)          #these are wrapper functions. they are created so as to pass these to the buttons.

        btn_new = Button(parent=panel, text="New Game", scale=(0.35, 0.18), y=-0.22, x=-0.18, on_click=do_restart)
        #on_clock= do_start, i,e uppon click of this button we have to call the do_restart functon. 
        btn_exit = Button(parent=panel, text="Exit", scale=(0.35, 0.18), y=-0.22, x=0.18, on_click=do_exit)
        btn_new.text_color = color.black
        btn_exit.text_color = color.black
        btn_new.color = color_tuple_to_color((230,230,230,255))
        btn_exit.color = color_tuple_to_color((230,230,230,255))
        self.menu_panel = panel

    def update(self):
        #the update function is a special pre built function in the Ursina library that is called automatically on every single frame. 
        #this function is basically responsible for running all the other parts of the game in the correct order. 
        dt = time.dt    #stores the time since the last frame in a variable named as "dt" (time.dt is the "time since the last frame")
        if held_keys['q']:  #if the "q" is pressed is True:
            if not hasattr(self, "_q_held") or not self._q_held:
                #hasattr basically checks if a variable has a certain attribute. 
                #so if not hasattr(self,"_q_held") means that if the variable self doesn't have the _q_held attribute, or
                #if self._q_held == False, then
                #basically it prevents the game from calling self.restart() multiple times if the "q" key is kept pressed for a long time. x
                #restart 
                self.restart()
                self._q_held = True #now make the self._q_held==True. 
        else:
            self._q_held = False  

        if self.over: return
        #if the game is over, i.e. self.over==True, then exit the function. 
        #if the game is not over
        self.player.step(dt)    #so if the game keeps running then update the player
        self.ai.step(dt)        #so if the game keeps running then update the ai
        self.clamp(self.player) 
        self.clamp(self.ai)
        self.check_collisions()

        if not self.player.alive and not self.ai.alive:
            self.status.text = "DRAW"
            self.status.color = color.yellow
        elif not self.player.alive:
            self.status.text = "AI WINS"
            self.status.color = self.lose_color
        elif not self.ai.alive:
            self.status.text = "YOU WIN"
            self.status.color = self.win_color

        self.cam.update()
        self.grid.update_fade(self.player.position)

app = Ursina()      #initialises the entire Ursina game engine and creates the game's application window
game = TronGame()   #game is an instance object of TronGame class
def update():game.update() 
app.run()                   