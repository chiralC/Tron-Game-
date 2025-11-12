# game.py
from ursina import *
from ursina.shaders import unlit_shader
import math, random, sys

# ---------- PALETTES ----------
PALETTES = [
    {"name": "Teal vs Orange (Classic)", "player": (0, 255, 230, 255), "ai": (255, 140, 0, 255)},
    {"name": "Magenta vs Teal",          "player": (255, 70, 200, 255), "ai": (50, 255, 230, 255)},
    {"name": "Crimson vs Cyan",          "player": (220, 20, 60, 255),  "ai": (0, 220, 255, 255)},
    {"name": "Emerald vs Gold",          "player": (30, 200, 120, 255), "ai": (245, 200, 70, 255)},
]

GRID_WARM = (255, 190, 130, 85)
WALL_WARM = (255, 200, 150, 110)

# ---------- COLOR UTIL ----------
def norm_component(v):
    if isinstance(v, (int,)) and v > 1:
        return max(0.0, min(1.0, v / 255.0))
    try:
        vf = float(v)
        if vf > 1.1:
            return max(0.0, min(1.0, vf / 255.0))
        return max(0.0, min(1.0, vf))
    except:
        return 0.0

def make_color(col_like, alpha=None):
    if isinstance(col_like, Color):
        r = norm_component(col_like.r)
        g = norm_component(col_like.g)
        b = norm_component(col_like.b)
        a = norm_component(col_like.a) if getattr(col_like, 'a', None) is not None else 1.0
    elif isinstance(col_like, (tuple, list)) and len(col_like) >= 3:
        r = norm_component(col_like[0])
        g = norm_component(col_like[1])
        b = norm_component(col_like[2])
        if len(col_like) >= 4:
            a = norm_component(col_like[3])
        else:
            a = 1.0
    else:
        r = g = b = 1.0
        a = 1.0
    if alpha is not None:
        a = norm_component(alpha)
    return Color(r, g, b, a)

# ---------- CAMERA ----------
class FollowCam:
    def __init__(self, target, distance=19, height=8, fov=95):
        self.target = target
        self.distance = distance
        self.height = height
        camera.fov = fov
        camera.position = (0, height, -distance)
        camera.rotation_x = 14
    def update(self):
        if not self.target: return
        tp = self.target.world_position + (self.target.forward * -self.distance) + Vec3(0, self.height, 0)
        camera.position = lerp(camera.position, tp, time.dt * 5)
        camera.look_at(self.target.world_position + Vec3(0, 1.2, 0))
        camera.rotation_z = lerp(camera.rotation_z, (held_keys['d'] - held_keys['a']) * 4, time.dt * 6)

# ---------- GRID ----------
class SoftGrid:
    def __init__(self, bounds=72.0, step=18, thickness=0.05, base_alpha=70, fade_range=48):
        self.bounds = float(bounds)
        self.step = int(step)
        self.thickness = thickness
        self.fade_range = float(fade_range)
        self.lines = []
        self.base_col = make_color(GRID_WARM, alpha=base_alpha/255.0)
        self._build()
    def _build(self):
        for L in self.lines: destroy(L["ent"])
        self.lines.clear()
        b = int(self.bounds)
        first = -b - (-b % self.step if self.step else 0)
        last  =  b - ( b % self.step if self.step else 0)
        span = 2 * b
        y = 0.01
        for i in range(first, last + 1, self.step):
            v = Entity(model='quad', rotation_x=90, color=self.base_col, x=i, y=y,
                       scale=(self.thickness, span, 1), shader=unlit_shader)
            h = Entity(model='quad', rotation_x=90, color=self.base_col, z=i, y=y,
                       scale=(span, self.thickness, 1), shader=unlit_shader)
            v.texture = None; h.texture = None
            self.lines.append({"ent": v, "axis": "x", "coord": i, "base": self.base_col})
            self.lines.append({"ent": h, "axis": "z", "coord": i, "base": self.base_col})
    def fade_with_distance(self, ref_pos: Vec3):
        fr = self.fade_range
        for L in self.lines:
            d = abs(L["coord"] - (ref_pos.x if L["axis"] == "x" else ref_pos.z))
            f = max(0.0, 1.0 - (d / fr) ** 2)
            base = L["base"]
            new_alpha = max(0.03, base.a * f)
            L["ent"].color = Color(base.r, base.g, base.b, new_alpha)
    def gentle_pulse(self, t):
        delta = 0.005 * math.sin(t * 0.9)
        for L in self.lines:
            c = L["ent"].color
            a = max(0.02, min(1.0, c.a + delta))
            L["ent"].color = Color(c.r, c.g, c.b, a)

# ---------- BOUNDARY WALLS ----------
class BoundaryWalls:
    def __init__(self, bounds=72.0, height=0.5, thickness=0.20, color_rgba=WALL_WARM):
        self.bounds = float(bounds)
        b = self.bounds; h = height; t = thickness; span = 2 * b
        col = make_color(color_rgba, alpha=(110/255.0))
        self.walls = [
            Entity(model='cube', shader=unlit_shader, color=col, position=(0, h/2,  b), scale=(span, h, t)),
            Entity(model='cube', shader=unlit_shader, color=col, position=(0, h/2, -b), scale=(span, h, t)),
            Entity(model='cube', shader=unlit_shader, color=col, position=( b, h/2, 0), scale=(t, h, span)),
            Entity(model='cube', shader=unlit_shader, color=col, position=(-b,h/2, 0), scale=(t, h, span)),
        ]
        for w in self.walls: w.texture = None

# ---------- TRAILS ----------
class SmoothTrail:
    def __init__(self, color_rgba, width=0.28, alpha=0.58, min_step=0.16):
        self.width = width
        self.min_step = min_step
        self.last = None
        self.visuals = []
        self.segs = []
        self.set_color(color_rgba, alpha)
    def set_color(self, color_rgba, alpha=0.58):
        self.base = color_rgba
        self.col = make_color(color_rgba, alpha=alpha)
        for q in self.visuals:
            q.color = self.col
    def _segment(self, p0: Vec3, p1: Vec3):
        d = Vec3(p1.x - p0.x, 0, p1.z - p0.z)
        L = max(0.001, math.hypot(d.x, d.z))
        if L < self.min_step: return
        mid = (p0 + p1) / 2
        ang = math.degrees(math.atan2(d.x, d.z))
        quad = Entity(model='quad', shader=unlit_shader, color=self.col,
                      position=Vec3(mid.x, 0.06, mid.z),
                      rotation=Vec3(90, ang, 0), scale=Vec3(self.width, L, 1))
        quad.texture = None
        self.visuals.append(quad)
        self.segs.append((Vec2(p0.x, p0.z), Vec2(p1.x, p1.z)))
        if len(self.visuals) > 1000: destroy(self.visuals.pop(0))
        if len(self.segs) > 1000: self.segs.pop(0)
    def step(self, pos3d: Vec3):
        p = Vec3(pos3d.x, 0, pos3d.z)
        if self.last is None: self.last = p; return
        d = p - self.last; dist = math.hypot(d.x, d.z)
        if dist >= self.min_step * 2.5:
            steps = max(2, int(dist / self.min_step))
            prev = self.last
            for _ in range(steps):
                q = Vec3(prev.x + d.x/steps, 0, prev.z + d.z/steps)
                self._segment(prev, q); prev = q
            self.last = prev
        else:
            self._segment(self.last, p); self.last = p
    def clear(self):
        for e in self.visuals: destroy(e)
        self.visuals.clear(); self.segs.clear(); self.last = None
    @staticmethod
    def _point_to_seg_dist2(p: Vec2, a: Vec2, b: Vec2):
        ab = b - a; ap = p - a
        ab2 = ab.x*ab.x + ab.y*ab.y
        if ab2 <= 1e-6: return ap.x*ap.x + ap.y*ap.y
        t = max(0.0, min(1.0, (ap.x*ab.x + ap.y*ab.y)/ab2))
        cx, cy = a.x + ab.x*t, a.y + ab.y*t
        dx, dy = p.x - cx, p.y - cy
        return dx*dx + dy*dy
    def hits(self, pos3d: Vec3, skip_recent=10, radius=0.30):
        if len(self.segs) <= skip_recent: return False
        p = Vec2(pos3d.x, pos3d.z); r2 = radius*radius
        for a, b in self.segs[:-skip_recent]:
            if self._point_to_seg_dist2(p, a, b) <= r2: return True
        return False

def glow_disk(col_like, scale=(1.5,1.5), y=0.02):
    c = make_color(col_like, alpha=(90/255.0))
    g = Entity(model='circle', color=c, rotation_x=90, scale=scale, y=y, shader=unlit_shader)
    g.texture = None
    return g

# ---------- BIKES ----------
class PlayerCycle(Entity):
    def __init__(self, col, base_speed=10.5, accel=1.3, max_speed=30.0, turn_speed=175.0, start_pos=(-14,0.5,0)):
        super().__init__(model='cube', color=make_color(col, alpha=1.0), scale=(0.8,0.8,2.3),
                         position=start_pos, shader=unlit_shader)
        self.base_color = col
        self.speed, self.accel, self.max_speed, self.turn_speed = base_speed, accel, max_speed, turn_speed
        self.alive = True
        self.trail = SmoothTrail(self.base_color, width=0.28, alpha=0.58, min_step=0.16)
        self.glow = glow_disk(self.base_color)
    def set_color(self, col):
        self.base_color = col
        self.color = make_color(col, alpha=1.0)
        self.trail.set_color(col, 0.58)
        self.glow.color = make_color(col, 90/255.0)
    def reset(self, pos=(-14,0.5,0), rot_y=0):
        self.position = pos; self.rotation = (0,rot_y,0)
        self.speed = 10.5; self.trail.clear(); self.alive = True
        self.color = make_color(self.base_color, 1.0)
        self.glow.position = (pos[0], 0.02, pos[2])
    def step(self, dt):
        if not self.alive: return
        self.speed = min(self.max_speed, self.speed + self.accel * dt)
        fwd = (1 if held_keys['w'] else 0) - (1 if held_keys['s'] else 0)
        if held_keys['a']: self.rotation_y -= self.turn_speed * dt
        if held_keys['d']: self.rotation_y += self.turn_speed * dt
        self.position += self.forward * (fwd * self.speed * dt)
        self.trail.step(self.position); self.glow.position = (self.x, 0.02, self.z)
    def die(self): self.alive = False; self.color = make_color((255,60,60,255), alpha=1.0)

class AICycle(Entity):
    def __init__(self, col, base_speed=11.0, turn_speed=170.0, arena_bounds=72.0, start_pos=(14,0.5,0)):
        super().__init__(model='cube', color=make_color(col, alpha=1.0), scale=(0.8,0.8,2.3),
                         position=start_pos, shader=unlit_shader)
        self.base_color = col
        self.base_speed = base_speed; self.speed = base_speed
        self.turn_speed = turn_speed; self.arena_bounds = arena_bounds
        self.alive = True
        self.trail = SmoothTrail(self.base_color, width=0.28, alpha=0.58, min_step=0.16)
        self._think_t = 0.0; self._think_interval = random.uniform(0.18,0.42); self._turn = 0
        self.glow = glow_disk(self.base_color)
    def set_color(self, col):
        self.base_color = col
        self.color = make_color(col, alpha=1.0)
        self.trail.set_color(col, 0.58)
        self.glow.color = make_color(col, 90/255.0)
    def reset(self, pos=(14,0.5,0), rot_y=180):
        self.position = pos; self.rotation=(0,rot_y,0)
        self.trail.clear(); self._think_t=0.0; self._turn=0; self.speed=self.base_speed; self.alive=True
        self.color = make_color(self.base_color, alpha=1.0)
        self.glow.position = (pos[0], 0.02, pos[2])
    def _sense_bounds(self):
        ahead = self.world_position + self.forward * 7.0
        b = self.arena_bounds
        return abs(ahead.x) > b-5 or abs(ahead.z) > b-5
    def step(self, dt):
        if not self.alive: return
        self._think_t += dt
        if self._think_t >= self._think_interval:
            self._think_t = 0.0; self._think_interval = random.uniform(0.18,0.42)
            self.speed = max(8.0, min(30.0, self.speed + random.uniform(-1.1, 1.1)))
            self._turn = random.choice([-1,1]) if self._sense_bounds() else random.choices([0,-1,1],[0.7,0.15,0.15])[0]
        if self._turn: self.rotation_y += self._turn * self.turn_speed * dt
        self.position += self.forward * (self.speed * dt)
        self.trail.step(self.position); self.glow.position = (self.x, 0.02, self.z)
    def die(self): self.alive = False; self.color = make_color((255,120,50,255), alpha=1.0)

# ---------- GAME ----------
class TronGame:
    def __init__(self):
        window.color = color.black
        DirectionalLight().enabled = False
        AmbientLight(color=color.rgb(0,0,0))

        self.bounds = 72.0
        self.grid   = SoftGrid(bounds=self.bounds, step=18, thickness=0.05, base_alpha=70, fade_range=48)
        self.walls  = BoundaryWalls(bounds=self.bounds, height=0.5, thickness=0.20, color_rgba=WALL_WARM)

        self.palette_index = 0
        pcol = PALETTES[self.palette_index]["player"]
        acol = PALETTES[self.palette_index]["ai"]

        self.player = PlayerCycle(col=pcol, base_speed=10.5, accel=1.3, max_speed=30.0, turn_speed=175.0)
        self.ai     = AICycle (col=acol, base_speed=11.0, turn_speed=170.0, arena_bounds=self.bounds)

        self.player.reset(pos=(-14,0.5,0), rot_y=0)
        self.ai.reset(pos=(14,0.5,0), rot_y=180)

        self.cam = FollowCam(self.player, distance=19, height=8, fov=95)
        self.t = 0.0

        self.menu_panel = None
        self.match_over = False

        self.status = Text("", origin=(0,0), scale=1.5, y=0.42, color=color.white)
        # Centered horizontally, placed low near bottom edge
        self.hint = Text(
        "W/S move • A left • D right • C cycle colours • Q reset",
        origin=(0, -0.5),      # centers horizontally
        x=0,                   # dead center
        y=-0.47,               # move down near bottom edge
        scale=0.85,
        color=color.rgba(255, 255, 255, 150)
        )


        self.apply_palette(self.palette_index)

    def apply_palette(self, idx):
        self.palette_index = idx % len(PALETTES)
        p = PALETTES[self.palette_index]
        player_col = p["player"]
        ai_col = p["ai"]

        self.player.set_color(player_col)
        self.ai.set_color(ai_col)

        self.win_player_color = make_color(player_col, alpha=1.0)
        self.win_ai_color = make_color(ai_col, alpha=1.0)

        self.hint.text = f"W/S move • A left • D right • C cycle colours • Q reset  —  Palette: {p['name']}"

    def cycle_palette(self):
        self.apply_palette(self.palette_index + 1)

    def clamp_bounds(self, e):
        b = self.bounds
        e.x = max(-b, min(b, e.x))
        e.z = max(-b, min(b, e.z))

    def check_trail_crashes(self):
        skip, rad = 10, 0.30
        if self.player.alive and (self.player.trail.hits(self.player.position, skip, rad)
                                  or self.ai.trail.hits(self.player.position, skip, rad)):
            self.player.die(); self.on_match_end()
        if self.ai.alive and (self.ai.trail.hits(self.ai.position, skip, rad)
                               or self.player.trail.hits(self.ai.position, skip, rad)):
            self.ai.die(); self.on_match_end()

    def restart(self):
        if self.menu_panel:
            destroy(self.menu_panel); self.menu_panel = None
        self.match_over = False
        self.player.reset(pos=(-14,0.5,0), rot_y=0)
        self.ai.reset(pos=(14,0.5,0), rot_y=180)
        self.status.text = ""
        self.player.trail.clear(); self.ai.trail.clear()

    def on_match_end(self):
        if self.match_over: return
        self.match_over = True
        if not self.player.alive and not self.ai.alive:
            self.status.text = "DRAW";    self.status.color = color.yellow
        elif not self.player.alive:
            self.status.text = "AI WINS"; self.status.color = self.win_ai_color
        elif not self.ai.alive:
            self.status.text = "YOU WIN"; self.status.color = self.win_player_color
        self.show_menu()

    def show_menu(self):
        panel = Entity(parent=camera.ui, model='quad', color=Color(0,0,0,0.7), scale=(1.2, .6), z=0)
        Text(parent=panel, text="Match Over", scale=2.0, y=0.22, origin=(0,0), color=color.white)
        Text(parent=panel, text=self.status.text, scale=1.5, y=0.0, origin=(0,0), color=self.status.color)

        def do_restart():
            self.restart()

        def do_exit():
            sys.exit(0)

        btn_new = Button(parent=panel, text="New Game", scale=(0.35, 0.18), y=-0.22, x=-0.18, on_click=lambda: do_restart())
        btn_exit = Button(parent=panel, text="Exit",     scale=(0.35, 0.18), y=-0.22, x=0.18,  on_click=lambda: do_exit())

        btn_new.text_color = color.black
        btn_exit.text_color = color.black
        btn_new.color = make_color((230,230,230,255))
        btn_exit.color = make_color((230,230,230,255))

        self.menu_panel = panel

    def update(self):
        dt = time.dt; self.t += dt

        if held_keys['c']:
            if not hasattr(self, "_c_held") or not self._c_held:
                self.cycle_palette()
                self._c_held = True
        else:
            self._c_held = False

        if held_keys['q']:
            if not hasattr(self, "_q_held") or not self._q_held:
                self.restart()
                self._q_held = True
        else:
            self._q_held = False

        if self.match_over:
            return

        self.player.step(dt); self.ai.step(dt)
        self.clamp_bounds(self.player); self.clamp_bounds(self.ai)
        self.check_trail_crashes()

        if not self.player.alive and not self.ai.alive:
            self.status.text = "DRAW";    self.status.color = color.yellow
        elif not self.player.alive:
            self.status.text = "AI WINS"; self.status.color = self.win_ai_color
        elif not self.ai.alive:
            self.status.text = "YOU WIN"; self.status.color = self.win_player_color

        self.cam.update()
        self.grid.fade_with_distance(self.player.position)
        self.grid.gentle_pulse(self.t)

# ---------- RUN ----------
app = Ursina()
game = TronGame()
def update(): game.update()
app.run()
