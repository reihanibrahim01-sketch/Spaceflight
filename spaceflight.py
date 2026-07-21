import pygame
import math
import random
import struct
import sys

# ------------------------------------------------------------------
# Inisialisasi
# ------------------------------------------------------------------
try:
    pygame.init()
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=1024)
        SOUND_OK = True
    except pygame.error:
        SOUND_OK = False
except Exception as e:
    print(f"Pygame init error: {e}")
    sys.exit(1)

W, H = 900, 500
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Spaceflight Simulator")
clock = pygame.time.Clock()

# Font
FONT_S = pygame.font.SysFont("Arial", 14)
FONT_M = pygame.font.SysFont("Arial", 18)
FONT_L = pygame.font.SysFont("Arial", 24)
FONT_XL = pygame.font.SysFont("Arial", 48, bold=True)

# Warna
BLACK = (5, 5, 15)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 50, 50)
BLUE = (30, 80, 200)
YELLOW = (255, 220, 0)
ORANGE = (255, 150, 0)
GRAY = (150, 150, 150)
DARK_GREEN = (0, 150, 0)

# ------------------------------------------------------------------
# Suara sintetis (fallback jika mixer gagal)
# ------------------------------------------------------------------
thrust_snd = None
explosion_snd = None
click_snd = None

if SOUND_OK:
    def make_thrust():
        sr = 22050; dur = 0.4; n = int(sr*dur)
        buf = []; prev = 0.0
        for _ in range(n):
            noise = random.uniform(-1,1)
            prev = 0.15*noise + 0.85*prev
            v = int(prev*0.18*32767)
            buf.extend([v,v])
        return pygame.mixer.Sound(buffer=struct.pack('<' + 'h'*len(buf), *buf))
    def make_explosion():
        sr=22050; dur=0.9; n=int(sr*dur)
        buf=[]
        for i in range(n):
            t=i/sr
            env = t/0.05 if t<0.05 else math.exp(-3.5*(t-0.05))
            noise=random.uniform(-1,1)*env*0.35
            v=int(noise*32767)
            buf.extend([v,v])
        return pygame.mixer.Sound(buffer=struct.pack('<' + 'h'*len(buf), *buf))
    def make_click():
        sr=22050; dur=0.04; n=int(sr*dur)
        buf=[]
        for i in range(n):
            t=i/sr
            v=int(math.sin(2*math.pi*600*t)*0.2*32767)
            buf.extend([v,v])
        return pygame.mixer.Sound(buffer=struct.pack('<' + 'h'*len(buf), *buf))
    try:
        thrust_snd = make_thrust()
        explosion_snd = make_explosion()
        click_snd = make_click()
    except:
        SOUND_OK = False

# ------------------------------------------------------------------
# Helper: gambar tombol lingkaran dengan ikon panah
# ------------------------------------------------------------------
def draw_arrow_btn(surf, x, y, r, direction, pressed):
    alpha = 200 if pressed else 80
    s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
    pygame.draw.circle(s, (255,255,255,alpha), (r,r), r-2)
    if direction == 'left':
        pts = [(r+8, r-10), (r-10, r), (r+8, r+10)]
    else:
        pts = [(r-8, r-10), (r+10, r), (r-8, r+10)]
    pygame.draw.polygon(s, (0,0,0,220), pts)
    surf.blit(s, (x-r, y-r))

def draw_thrust_btn(surf, x, y, r, pressed):
    alpha = 200 if pressed else 80
    col = (0,255,0,alpha) if pressed else (0,180,0,alpha)
    s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
    pygame.draw.circle(s, col, (r,r), r)
    txt = FONT_M.render("THRUST", True, WHITE)
    rect = txt.get_rect(center=(r, r))
    s.blit(txt, rect)
    surf.blit(s, (x-r, y-r))

def draw_restart_btn(surf, x, y, r, alive):
    alpha = 200 if not alive else 80
    col = (255,50,50,alpha) if not alive else (80,80,80,alpha)
    s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
    pygame.draw.circle(s, col, (r,r), r)
    pygame.draw.circle(s, (255,255,255,200), (r,r), r-4, 2)
    # panah restart
    ax = r + int((r-6)*math.cos(math.radians(-30)))
    ay = r + int((r-6)*math.sin(math.radians(-30)))
    pts = [(ax,ay), (ax-8, ay-4), (ax-4, ay+4)]
    pygame.draw.polygon(s, (255,255,255,200), pts)
    txt = FONT_S.render("R", True, WHITE)
    s.blit(txt, (r-4, r-7))
    surf.blit(s, (x-r, y-r))

def draw_menu_btn(surf, x, y, r, pressed):
    alpha = 180 if pressed else 100
    s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
    pygame.draw.rect(s, (255,255,255,alpha), s.get_rect(), border_radius=5)
    txt = FONT_S.render("MENU", True, WHITE)
    rect = txt.get_rect(center=(r,r))
    s.blit(txt, rect)
    surf.blit(s, (x-r, y-r))

# ------------------------------------------------------------------
# Tombol virtual (mendukung multitouch)
# ------------------------------------------------------------------
class TouchButton:
    def __init__(self, x, y, r, shape='circle'):
        self.x = x; self.y = y; self.r = r
        self.shape = shape
        self.rect = pygame.Rect(x-r, y-r, r*2, r*2) if shape=='rect' else None
        self.pressed = False
        self.touch_id = None

    def hit_test(self, px, py):
        if self.shape == 'circle':
            return math.hypot(px-self.x, py-self.y) <= self.r
        else:
            return self.rect.collidepoint(px, py)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hit_test(*event.pos):
                self.pressed = True; return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed: self.pressed = False; return True
        elif event.type == pygame.MOUSEMOTION:
            if self.pressed and not self.hit_test(*event.pos):
                self.pressed = False
        elif event.type == pygame.FINGERDOWN:
            fx, fy = event.x*W, event.y*H
            if self.hit_test(fx, fy):
                self.pressed = True; self.touch_id = event.finger_id; return True
        elif event.type == pygame.FINGERUP:
            if self.touch_id is not None and event.finger_id == self.touch_id:
                self.pressed = False; self.touch_id = None; return True
        elif event.type == pygame.FINGERMOTION:
            if self.touch_id is not None and event.finger_id == self.touch_id:
                fx, fy = event.x*W, event.y*H
                if not self.hit_test(fx, fy):
                    self.pressed = False; self.touch_id = None
        return False

# ------------------------------------------------------------------
# Bintang & Planet & Roket (tetap)
# ------------------------------------------------------------------
class StarField:
    def __init__(self, n=200):
        self.stars = []
        for _ in range(n):
            x = random.randint(-3000, 3000)
            y = random.randint(-3000, 3000)
            b = random.randint(120, 255)
            sp = random.uniform(0.3, 1.5)
            self.stars.append([x, y, b, sp, random.random()*2*math.pi])

    def update(self, dt):
        for s in self.stars:
            s[4] += s[3]*dt
            s[2] = 130 + 125 * math.sin(s[4])

    def draw(self, surf, ox, oy):
        for x, y, b, _, _ in self.stars:
            sx = x - ox + W//2
            sy = y - oy + H//2
            if 0 <= sx < W and 0 <= sy < H:
                c = (int(b), int(b), int(b))
                surf.set_at((int(sx), int(sy)), c)

class Planet:
    def __init__(self, x, y, radius, gm, color):
        self.x=x; self.y=y; self.radius=radius; self.gm=gm
        self.color=color
        self.craters = []
        for _ in range(8):
            ang = random.uniform(0, 2*math.pi)
            d = random.uniform(radius*0.2, radius*0.9)
            cx = x + d*math.cos(ang); cy = y + d*math.sin(ang)
            sz = random.uniform(2,5)
            self.craters.append((cx,cy,sz))

    def draw(self, surf, ox, oy):
        sx = self.x - ox + W//2
        sy = self.y - oy + H//2
        # body
        for r in range(self.radius, 0, -1):
            c = tuple(int(self.color[i]*(0.6+0.4*r/self.radius)) for i in range(3))
            pygame.draw.circle(surf, c, (int(sx), int(sy)), r)
        # craters
        for cx,cy,sz in self.craters:
            scx = cx - ox + W//2; scy = cy - oy + H//2
            pygame.draw.circle(surf, (0,0,0,100), (int(scx), int(scy)), int(sz))
        # atmosphere glow
        glow = self.radius+5
        gs = pygame.Surface((glow*2, glow*2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*self.color,40), (glow,glow), glow)
        surf.blit(gs, (sx-glow, sy-glow))

class Rocket:
    def __init__(self, x, y, angle=0):
        self.x=x; self.y=y
        self.vx=0.0; self.vy=0.0
        self.angle = math.radians(angle)
        self.trail = []
        self.alive = True
        self.thrusting = False
        self.explosion_timer = 0.0
        self.explosion_pts = []
        self.played_boom = False

    def update(self, dt, planets, rot, thrust):
        if not self.alive:
            self.explosion_timer += dt
            return
        # total gravity
        ax=ay=0.0
        for p in planets:
            dx=p.x-self.x; dy=p.y-self.y
            dist=math.hypot(dx,dy)
            if dist>p.radius:
                acc=p.gm/(dist*dist)
                ax+=acc*dx/dist; ay+=acc*dy/dist
        # rotation
        self.angle += math.radians(3.5 * dt * rot * 60)
        self.thrusting = False
        tx=ty=0.0
        if thrust:
            inside = False
            for p in planets:
                if math.hypot(p.x-self.x, p.y-self.y) <= p.radius:
                    inside=True; break
            if not inside:
                self.thrusting = True
                tx = 350 * math.cos(self.angle)
                ty = 350 * math.sin(self.angle)
        self.vx += (ax+tx)*dt
        self.vy += (ay+ty)*dt
        self.x += self.vx*dt
        self.y += self.vy*dt
        # trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > 250: self.trail.pop(0)
        # collision
        for p in planets:
            if math.hypot(p.x-self.x, p.y-self.y) <= p.radius:
                self.alive=False
                self.explosion_timer=0.0
                self.played_boom=False
                for _ in range(25):
                    a=random.uniform(0,2*math.pi)
                    spd=random.uniform(40,180)
                    self.explosion_pts.append({
                        'x':self.x,'y':self.y,
                        'vx':spd*math.cos(a),'vy':spd*math.sin(a),
                        'life':random.uniform(0.4,1.2)
                    })
                break

    def draw(self, surf, ox, oy):
        # trail
        for i,(tx,ty) in enumerate(self.trail):
            sx=tx - ox + W//2; sy=ty - oy + H//2
            alpha = int(150 * (i/len(self.trail)))
            if 0<=sx<W and 0<=sy<H:
                tr=pygame.Surface((3,3), pygame.SRCALPHA)
                pygame.draw.circle(tr, (200,200,200,alpha), (1,1), 1)
                surf.blit(tr, (sx-1, sy-1))
        if self.alive:
            sx=self.x - ox + W//2; sy=self.y - oy + H//2
            # velocity vector (panah kecil)
            v_angle = math.atan2(self.vy, self.vx)
            v_len = min(25, math.hypot(self.vx, self.vy)*0.05)
            if v_len > 2:
                end_x = sx + v_len*math.cos(v_angle)
                end_y = sy + v_len*math.sin(v_angle)
                pygame.draw.line(surf, (100,200,255), (sx,sy), (end_x,end_y), 2)
                # arrowhead
                ah = [(end_x+5*math.cos(v_angle+2.5), end_y+5*math.sin(v_angle+2.5)),
                      (end_x+5*math.cos(v_angle-2.5), end_y+5*math.sin(v_angle-2.5))]
                pygame.draw.line(surf, (100,200,255), ah[0], (end_x,end_y), 2)
                pygame.draw.line(surf, (100,200,255), ah[1], (end_x,end_y), 2)
            # rocket body
            pts = [
                (sx+12*math.cos(self.angle), sy+12*math.sin(self.angle)),
                (sx+8*math.cos(self.angle+2.7), sy+8*math.sin(self.angle+2.7)),
                (sx+3*math.cos(self.angle+math.pi), sy+3*math.sin(self.angle+math.pi)),
                (sx+8*math.cos(self.angle-2.7), sy+8*math.sin(self.angle-2.7))
            ]
            pygame.draw.polygon(surf, WHITE, pts)
            pygame.draw.polygon(surf, GRAY, pts, 1)
            if self.thrusting:
                fl = random.randint(6,14)
                fps = [
                    (sx-5*math.cos(self.angle), sy-5*math.sin(self.angle)),
                    (sx-(5+fl)*math.cos(self.angle+0.4), sy-(5+fl)*math.sin(self.angle+0.4)),
                    (sx-(5+fl)*math.cos(self.angle-0.4), sy-(5+fl)*math.sin(self.angle-0.4))
                ]
                pygame.draw.polygon(surf, YELLOW, fps)
                pygame.draw.polygon(surf, ORANGE, fps, 2)
        else:
            for p in self.explosion_pts:
                life_r = p['life']/1.2
                if life_r > 0:
                    px = p['x']+p['vx']*self.explosion_timer - ox + W//2
                    py = p['y']+p['vy']*self.explosion_timer - oy + H//2
                    col = (255, int(200*life_r), 0)
                    pygame.draw.circle(surf, col, (int(px), int(py)), int(3*life_r))

# ------------------------------------------------------------------
# Scene: Menu Utama
# ------------------------------------------------------------------
class MenuScene:
    def __init__(self):
        self.stars = StarField(250)
        self.planet = Planet(0, 0, 55, 1000, (30,80,200))
        self.play_btn = pygame.Rect(W//2-100, 220, 200, 60)
        self.quit_btn = pygame.Rect(W//2-100, 310, 200, 60)
        self.time = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            p = event.pos
            if self.play_btn.collidepoint(p):
                if SOUND_OK and click_snd: click_snd.play()
                return 'play'
            if self.quit_btn.collidepoint(p):
                return 'quit'
        elif event.type == pygame.FINGERDOWN:
            fx, fy = event.x*W, event.y*H
            if self.play_btn.collidepoint(fx, fy):
                if SOUND_OK and click_snd: click_snd.play()
                return 'play'
            if self.quit_btn.collidepoint(fx, fy):
                return 'quit'
        return None

    def update(self, dt):
        self.stars.update(dt)
        self.time += dt
        # planet rotation effect (change color a bit)
        self.planet.color = (30+int(10*math.sin(self.time*0.5)), 80, 200)

    def draw(self, surf):
        surf.fill(BLACK)
        self.stars.draw(surf, 0, 0)
        self.planet.draw(surf, 0, 0)
        # Title
        title = FONT_XL.render("SPACEFLIGHT", True, WHITE)
        shadow = FONT_XL.render("SPACEFLIGHT", True, (50,50,80))
        surf.blit(shadow, (W//2 - title.get_width()//2 + 3, 63))
        surf.blit(title, (W//2 - title.get_width()//2, 60))
        sub = FONT_L.render("SIMULATOR", True, (150,200,255))
        surf.blit(sub, (W//2 - sub.get_width()//2, 115))
        # Buttons
        for rect, text, col in [(self.play_btn, "PLAY", DARK_GREEN), (self.quit_btn, "QUIT", (150,0,0))]:
            hover = rect.collidepoint(pygame.mouse.get_pos())
            c = (0,200,0) if hover and text=="PLAY" else col
            if text=="QUIT": c = (200,0,0) if hover else col
            pygame.draw.rect(surf, c, rect, border_radius=10)
            txt = FONT_L.render(text, True, WHITE)
            tr = txt.get_rect(center=rect.center)
            surf.blit(txt, tr)
        # Info
        info = FONT_S.render("Tap PLAY to start | Keyboard: Arrows + R", True, GRAY)
        surf.blit(info, (W//2 - info.get_width()//2, H-30))

# ------------------------------------------------------------------
# Scene: Permainan
# ------------------------------------------------------------------
class GameScene:
    def __init__(self):
        self.planets = [
            Planet(0,0,55,1000,(30,80,200)),
            Planet(700,-300,35,500,(200,80,80)),
            Planet(-650,400,45,750,(80,180,80)),
            Planet(-400,-500,30,400,(160,60,200)),
            Planet(600,550,40,600,(220,150,50)),
            Planet(900,200,20,300,(255,200,100)),   # bonus kecil
            Planet(-900,-250,22,350,(100,220,220))
        ]
        self.rocket = Rocket(250, 0, angle=-90)
        self.rocket.vy = -120
        self.stars = StarField(300)
        # Kontrol virtual
        self.left_btn = TouchButton(50, H-70, 38)
        self.right_btn = TouchButton(150, H-70, 38)
        self.thrust_btn = TouchButton(W-110, H-80, 52)
        self.restart_btn = TouchButton(W-45, 45, 25, 'circle')
        self.menu_btn = TouchButton(40, 40, 20, 'rect')
        # audio
        self.thrust_channel = None
        if SOUND_OK and thrust_snd:
            self.thrust_channel = pygame.mixer.Channel(0)
        self.thrust_playing = False

    def reset_rocket(self):
        self.rocket = Rocket(250, 0, angle=-90)
        self.rocket.vy = -120
        if self.thrust_playing:
            self.thrust_channel.stop()
            self.thrust_playing = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            if SOUND_OK and click_snd: click_snd.play()
            self.reset_rocket()
        if self.left_btn.handle_event(event): pass
        if self.right_btn.handle_event(event): pass
        if self.thrust_btn.handle_event(event): pass
        if self.restart_btn.handle_event(event) and not self.rocket.alive:
            if SOUND_OK and click_snd: click_snd.play()
            self.reset_rocket()
        if self.menu_btn.handle_event(event):
            return 'menu'
        return None

    def update(self, dt):
        # input
        rot = 0
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: rot -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: rot += 1
        if self.left_btn.pressed: rot -= 1
        if self.right_btn.pressed: rot += 1

        thrust = False
        if keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]:
            thrust = True
        if self.thrust_btn.pressed:
            thrust = True

        self.rocket.update(dt, self.planets, rot, thrust)
        self.stars.update(dt)

        # suara
        if SOUND_OK:
            if self.rocket.alive and thrust:
                if not self.thrust_playing and self.thrust_channel:
                    self.thrust_channel.play(thrust_snd, loops=-1)
                    self.thrust_playing = True
            else:
                if self.thrust_playing:
                    self.thrust_channel.stop()
                    self.thrust_playing = False
            if not self.rocket.alive and not self.rocket.played_boom:
                explosion_snd.play()
                self.rocket.played_boom = True
                if self.thrust_playing:
                    self.thrust_channel.stop()
                    self.thrust_playing = False

    def draw(self, surf):
        cam_x, cam_y = self.rocket.x, self.rocket.y
        surf.fill(BLACK)
        self.stars.draw(surf, cam_x, cam_y)
        for p in self.planets:
            p.draw(surf, cam_x, cam_y)
        self.rocket.draw(surf, cam_x, cam_y)
        # HUD
        pan = pygame.Surface((250, 90), pygame.SRCALPHA)
        pan.fill((0,0,0,170))
        surf.blit(pan, (8,8))
        nearest = min(self.planets, key=lambda p: math.hypot(p.x-self.rocket.x, p.y-self.rocket.y))
        alt = max(0, math.hypot(nearest.x-self.rocket.x, nearest.y-self.rocket.y) - nearest.radius)
        spd = math.hypot(self.rocket.vx, self.rocket.vy)
        circ = math.sqrt(nearest.gm / max(1, math.hypot(nearest.x-self.rocket.x, nearest.y-self.rocket.y)))
        txt_alt = FONT_S.render(f"Altitude: {alt:.1f}", True, GREEN)
        txt_spd = FONT_S.render(f"Speed: {spd:.1f}", True, GREEN)
        txt_circ = FONT_S.render(f"Orbit spd: {circ:.1f}", True, YELLOW)
        surf.blit(txt_alt, (15,15))
        surf.blit(txt_spd, (15,35))
        surf.blit(txt_circ, (15,55))
        status = "ALIVE" if self.rocket.alive else "DESTROYED"
        st_col = GREEN if self.rocket.alive else RED
        st_surf = FONT_L.render(status, True, st_col)
        surf.blit(st_surf, (W//2 - st_surf.get_width()//2, 10))
        # virtual controls
        draw_arrow_btn(surf, self.left_btn.x, self.left_btn.y, self.left_btn.r, 'left', self.left_btn.pressed)
        draw_arrow_btn(surf, self.right_btn.x, self.right_btn.y, self.right_btn.r, 'right', self.right_btn.pressed)
        draw_thrust_btn(surf, self.thrust_btn.x, self.thrust_btn.y, self.thrust_btn.r, self.thrust_btn.pressed)
        draw_restart_btn(surf, self.restart_btn.x, self.restart_btn.y, self.restart_btn.r, self.rocket.alive)
        draw_menu_btn(surf, self.menu_btn.x, self.menu_btn.y, self.menu_btn.r, self.menu_btn.pressed)

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    scene = MenuScene()
    current = 'menu'
    while True:
        dt = clock.tick(60)/1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); return
            if current == 'menu':
                res = scene.handle_event(ev)
                if res == 'play':
                    scene = GameScene()
                    current = 'game'
                elif res == 'quit':
                    pygame.quit(); return
            elif current == 'game':
                res = scene.handle_event(ev)
                if res == 'menu':
                    scene = MenuScene()
                    current = 'menu'
        scene.update(dt)
        scene.draw(screen)
        pygame.display.flip()

if __name__ == "__main__":
    main()