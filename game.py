from ursina import *
from ursina.shaders import unlit_shader
import math
import random
import sys

# Just one palette for now, orange vs blue, classic Tron look
BIKE_COLORS = [
    {
        "name": "Tron Colors",
        "player": (0, 255, 230, 255),
        "ai": (255, 140, 0, 255)
    }
]

GRID_COLOR = (70, 200, 255, 255)
WALL_COLOR = (255, 200, 150, 110)

def color_tuple_to_color(t, alpha=None):
    # Converts a color tuple (0-255) to a Color in Ursina
    r = max(0.0, min(1.0, (t[0]/255.0)))
    g = max(0.0, min(1.0, (t[1]/255.0)))
    b = max(0.0, min(1.0, (t[2]/255.0)))
    if len(t) > 3:
        a = max(0.0, min(1.0, (t[3]/255.0)))
    else:
        a = 1.0
    if alpha is not None:
        a = max(0.0, min(1.0, alpha))
    return Color(r, g, b, a)

# Camera follows the player, always looking down but a little behind
class ChaseCam:
    def __init__(self, target_entity, dist=19, height=8, fov=95):
        self.target = target_entity
        self.dist = dist
        self.height = height
        camera.fov = fov
        camera.position = (0, height, -dist)
        camera.rotation_x = 14

    def update(self):
        if not self.target: return
        pos = self.target.world_position - (self.target.forward * self.dist) + Vec3(0, self.height, 0)
        camera.position = lerp(camera.position, pos, time.dt * 5)
        camera.look_at(self.target.world_position + Vec3(0, 1.2, 0))
        # Side-to-side tilt based on A/D keys
        camera.rotation_z = lerp(camera.rotation_z, (held_keys['d'] - held_keys['a']) * 4, time.dt * 6)

# Grid lines on the ground (for style and reference!)
class Grid:
    def __init__(self, size=72.0, gap=18, thickness=0.5, fade=48):
        self.size = size
        self.gap = gap
        self.thickness = thickness
        self.fade = fade
        self.lines = []
        base_color = color_tuple_to_color(GRID_COLOR, alpha=70/255.0)
        self.create_lines(base_color)

    def create_lines(self, base_color):
        for l in self.lines:
            destroy(l)
        self.lines = []
        edge = int(self.size)
        start = -edge - (-edge % self.gap if self.gap else 0)
        stop = edge - (edge % self.gap if self.gap else 0)
        span = 2 * edge
        for v in range(start, stop+1, self.gap):
            l1 = Entity(model='quad', rotation_x=90, color=base_color, x=v, y=0.01,
                        scale=(self.thickness, span, 1), shader=unlit_shader)
            l2 = Entity(model='quad', rotation_x=90, color=base_color, z=v, y=0.01,
                        scale=(span, self.thickness, 1), shader=unlit_shader)
            l1.texture = None
            l2.texture = None
            self.lines.append(l1)
            self.lines.append(l2)

    def update_fade(self, player_pos):
        for line in self.lines:
            d = abs(line.x - player_pos.x) if abs(line.scale_x - self.thickness)<0.01 else abs(line.z - player_pos.z)
            fade_factor = 1.0 - (d / self.fade) ** 2 if self.fade else 1.0
            c = line.color
            line.color = Color(c.r, c.g, c.b, max(0.03, c.a if isinstance(c, Color) else 1.0) * max(0.0, fade_factor))

# Set up simple boundary box walls
class Boundary:
    def __init__(self, size=72.0, height=0.5, thickness=0.2):
        color_rgba = color_tuple_to_color(WALL_COLOR, alpha=110/255.0)
        edge = size
        span = 2*edge
        h = height/2.0
        self.walls = [
            Entity(model='cube', shader=unlit_shader, color=color_rgba, position=(0, h, edge), scale=(span, height, thickness)),
            Entity(model='cube', shader=unlit_shader, color=color_rgba, position=(0, h, -edge), scale=(span, height, thickness)),
            Entity(model='cube', shader=unlit_shader, color=color_rgba, position=(edge, h, 0), scale=(thickness, height, span)),
            Entity(model='cube', shader=unlit_shader, color=color_rgba, position=(-edge, h, 0), scale=(thickness, height, span))
        ]

# Leaves a glowing trail behind your bike
class Trail:
    def __init__(self, color, width=0.28, alpha=0.58, min_segment=0.16):
        self.width = width
        self.min_segment = min_segment
        self.last_pos = None
        self.segments = []
        self.visuals = []
        self.color = color_tuple_to_color(color, alpha=alpha)

    def add_segment(self, a: Vec3, b: Vec3):
        d = Vec3(b.x-a.x, 0, b.z-a.z)
        length = math.hypot(d.x, d.z)
        if length < self.min_segment: return
        mid = (a + b) / 2
        angle = math.degrees(math.atan2(d.x, d.z))
        seg = Entity(model='quad', shader=unlit_shader, color=self.color,
                     position=Vec3(mid.x, 0.06, mid.z), rotation=Vec3(90, angle, 0),
                     scale=Vec3(self.width, length, 1))
        seg.texture = None
        self.visuals.append(seg)
        self.segments.append((Vec2(a.x,a.z), Vec2(b.x,b.z)))
        if len(self.visuals)>1000: destroy(self.visuals.pop(0))
        if len(self.segments)>1000: self.segments.pop(0)

    def step(self, pos3d: Vec3):
        p = Vec3(pos3d.x, 0, pos3d.z)
        if self.last_pos is None:
            self.last_pos = p
            return
        d = p - self.last_pos
        dist = math.hypot(d.x, d.z)
        if dist >= self.min_segment*2.5:
            steps = max(2, int(dist / self.min_segment))
            prev = self.last_pos
            for _ in range(steps):
                nxt = Vec3(prev.x + d.x/steps, 0, prev.z + d.z/steps)
                self.add_segment(prev, nxt)
                prev = nxt
            self.last_pos = prev
        else:
            self.add_segment(self.last_pos, p)
            self.last_pos = p

    def clear(self):
        for e in self.visuals:
            destroy(e)
        self.visuals.clear()
        self.segments.clear()
        self.last_pos = None

    def collides(self, pos3d: Vec3, skip_recent=10, radius=0.30):
        # Check if pos3d hits the trail except very recently created segments
        if len(self.segments)<=skip_recent: return False
        p = Vec2(pos3d.x, pos3d.z)
        r2 = radius*radius
        for a, b in self.segments[:-skip_recent]:
            ab = b - a
            ap = p - a
            ab2 = ab.x*ab.x+ab.y*ab.y
            if ab2 <= 1e-6:
                if ap.x*ap.x+ap.y*ap.y <= r2: return True
                continue
            t = max(0.0, min(1.0, (ap.x*ab.x+ap.y*ab.y)/ab2))
            cx, cy = a.x + ab.x*t, a.y + ab.y*t
            dx, dy = p.x-cx, p.y-cy
            if dx*dx+dy*dy <= r2: return True
        return False

def bike_glow(col, scale=(1.5,1.5), y=0.02):
    c = color_tuple_to_color(col, alpha=90/255.0)
    return Entity(model='circle', color=c, rotation_x=90, scale=scale, y=y, shader=unlit_shader, texture=None)

class PlayerBike(Entity):
    def __init__(self, col, start=(-14,0.5,0)):
        super().__init__(
            model='cube',
            color=color_tuple_to_color(col, alpha=1.0),
            scale=(0.8,0.8,2.3),
            position=start,
            shader=unlit_shader
        )
        self.base_col = col
        self.speed = 10.5
        self.accel = 1.3
        self.max_speed = 30.0
        self.turn_speed = 175.0
        self.alive = True
        self.trail = Trail(self.base_col)
        self.glow = bike_glow(self.base_col)

    def reset(self, pos=(-14,0.5,0), rot=0):
        self.position = pos
        self.rotation = (0,rot,0)
        self.speed = 10.5
        self.trail.clear()
        self.alive = True
        self.color = color_tuple_to_color(self.base_col, 1.0)
        self.glow.position = (pos[0], 0.02, pos[2])

    def step(self, dt):
        if not self.alive: return
        self.speed = min(self.max_speed, self.speed + self.accel * dt)
        fwd = (1 if held_keys['w'] else 0) - (1 if held_keys['s'] else 0)
        if held_keys['a']: self.rotation_y -= self.turn_speed * dt
        if held_keys['d']: self.rotation_y += self.turn_speed * dt
        self.position += self.forward * (fwd * self.speed * dt)
        self.trail.step(self.position)
        self.glow.position = (self.x, 0.02, self.z)

    def die(self):
        self.alive = False
        self.color = color_tuple_to_color((255,60,60,255), alpha=1.0)

class AIBike(Entity):
    def __init__(self, col, arena_bounds=72.0, start=(14,0.5,0)):
        super().__init__(
            model='cube',
            color=color_tuple_to_color(col, alpha=1.0),
            scale=(0.8,0.8,2.3),
            position=start,
            shader=unlit_shader
        )
        self.base_col = col
        self.speed = 11.0
        self.max_speed = 30.0
        self.turn_speed = 170.0
        self.arena_bounds = arena_bounds
        self.alive = True
        self.trail = Trail(self.base_col)
        self.timer = 0.0
        self.think_interval = random.uniform(0.18,0.42)
        self.turning = 0
        self.glow = bike_glow(self.base_col)

    def reset(self, pos=(14,0.5,0), rot=180):
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
        if not self.alive: return
        self.timer += dt
        near_wall = False
        ahead = self.world_position + self.forward * 7.0
        if abs(ahead.x)>self.arena_bounds-5 or abs(ahead.z)>self.arena_bounds-5:
            near_wall = True
        if self.timer>=self.think_interval:
            self.timer = 0.0
            self.think_interval = random.uniform(0.18,0.42)
            self.speed = max(8.0, min(30.0, self.speed + random.uniform(-1.1,1.1)))
            if near_wall:
                self.turning = random.choice([-1,1])
            else:
                self.turning = random.choices([0,-1,1],[0.7,0.15,0.15])[0]
        if self.turning: self.rotation_y += self.turning * self.turn_speed * dt
        self.position += self.forward * (self.speed * dt)
        self.trail.step(self.position)
        self.glow.position = (self.x, 0.02, self.z)

    def die(self):
        self.alive = False
        self.color = color_tuple_to_color((255,120,50,255), alpha=1.0)

class TronGame:
    def __init__(self):
        window.color = color.black
        DirectionalLight().enabled = False
        AmbientLight(color=color.rgb(0,0,0))
        self.bounds = 72.0
        self.grid = Grid(size=self.bounds)
        self.walls = Boundary(size=self.bounds)
        col_player = BIKE_COLORS[0]["player"]
        col_ai = BIKE_COLORS[0]["ai"]
        self.player = PlayerBike(col=col_player)
        self.ai = AIBike(col=col_ai, arena_bounds=self.bounds)
        self.player.reset()
        self.ai.reset()
        self.cam = ChaseCam(self.player)
        self.over = False
        self.menu_panel = None
        self.status = Text("", origin=(0,0), scale=1.5, y=0.42, color=color.white)
        self.hint = Text("W/S move • A left • D right • Q reset", origin=(0, -0.5), x=0, y=-0.47, scale=0.85, color=color.rgba(255,255,255,150))
        self.win_color = color_tuple_to_color(col_player, alpha=1.0)
        self.lose_color = color_tuple_to_color(col_ai, alpha=1.0)

    def clamp(self, thing):
        b = self.bounds
        thing.x = max(-b, min(b, thing.x))
        thing.z = max(-b, min(b, thing.z))

    def check_collisions(self):
        # Player runs into their own or AI's trail: dies
        skip = 10
        rad = 0.30
        if self.player.alive and (self.player.trail.collides(self.player.position, skip, rad) or self.ai.trail.collides(self.player.position, skip, rad)):
            self.player.die()
            self.end_game()
        if self.ai.alive and (self.ai.trail.collides(self.ai.position, skip, rad) or self.player.trail.collides(self.ai.position, skip, rad)):
            self.ai.die()
            self.end_game()

    def restart(self):
        # Start again
        if self.menu_panel:
            destroy(self.menu_panel)
            self.menu_panel = None
        self.over = False
        self.player.reset()
        self.ai.reset()
        self.status.text = ""
        self.player.trail.clear()
        self.ai.trail.clear()

    def end_game(self):
        if self.over: return
        self.over = True
        if not self.player.alive and not self.ai.alive:
            self.status.text = "DRAW"
            self.status.color = color.yellow
        elif not self.player.alive:
            self.status.text = "AI WINS"
            self.status.color = self.lose_color
        elif not self.ai.alive:
            self.status.text = "YOU WIN"
            self.status.color = self.win_color
        self.show_menu()

    def show_menu(self):
        panel = Entity(parent=camera.ui, model='quad', color=Color(0,0,0,0.7), scale=(1.2, .6), z=0)
        Text(parent=panel, text="Match Over", scale=2.0, y=0.22, origin=(0,0), color=color.white)
        Text(parent=panel, text=self.status.text, scale=1.5, y=0.0, origin=(0,0), color=self.status.color)

        def do_restart(): self.restart()
        def do_exit(): sys.exit(0)

        btn_new = Button(parent=panel, text="New Game", scale=(0.35, 0.18), y=-0.22, x=-0.18, on_click=do_restart)
        btn_exit = Button(parent=panel, text="Exit", scale=(0.35, 0.18), y=-0.22, x=0.18, on_click=do_exit)
        btn_new.text_color = color.black
        btn_exit.text_color = color.black
        btn_new.color = color_tuple_to_color((230,230,230,255))
        btn_exit.color = color_tuple_to_color((230,230,230,255))
        self.menu_panel = panel

    def update(self):
        dt = time.dt

        if held_keys['q']:
            if not hasattr(self, "_q_held") or not self._q_held:
                self.restart()
                self._q_held = True
        else:
            self._q_held = False

        if self.over: return

        self.player.step(dt)
        self.ai.step(dt)
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

app = Ursina()
game = TronGame()
def update(): game.update()
app.run()
