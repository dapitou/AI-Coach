import cv2
import mediapipe as mp
import numpy as np
import math
import time
import threading 
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass

# ==========================================
# 0. 驱动初始化
# ==========================================
try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False
    print("[System] Warning: Pygame not found. Audio disabled.")

# ==========================================
# 1. 摄像头驱动
# ==========================================
class CameraLoader:
    def __init__(self, src=0, w=1280, h=720):
        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.w, self.h = w, h
        self.ret, self.frame = False, None
        self.running = True
        self.lock = threading.Lock()
        self.is_video, self.video_len, self.current_pos = False, 0, 0
        self.seek_req = -1 
        self.src = src
        self.paused = False
        self.open_source(src)
        self.t = threading.Thread(target=self._update, daemon=True)
        self.t.start()
    
    def open_source(self, src):
        with self.lock:
            if hasattr(self, 'cap') and self.cap is not None: self.cap.release()
            self.current_pos = 0; self.seek_req = -1; self.frame = None; self.paused = False
            if isinstance(src, int): self.cap = cv2.VideoCapture(src, cv2.CAP_DSHOW) 
            else: self.cap = cv2.VideoCapture(src)
            
            if isinstance(src, str):
                self.is_video = True
                self.video_len = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            else:
                self.is_video = False
                self.cap.set(3, self.w); self.cap.set(4, self.h); self.cap.set(5, 30)
            self.src = src

    def switch_source(self, src): self.open_source(src)
    def seek(self, ratio): 
        if self.is_video: self.seek_req = max(0.0, min(1.0, ratio))
    def toggle_pause(self, src): 
        if self.is_video: self.paused = not self.paused
    def get_progress(self): 
        return (self.current_pos / self.video_len) if (self.is_video and self.video_len > 0) else 0.0

    def _update(self):
        while self.running:
            force = False
            if self.is_video and self.seek_req >= 0:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, int(self.seek_req * self.video_len))
                self.seek_req = -1; force = True
            if self.is_video and self.paused and not force:
                time.sleep(0.03); continue
            if self.cap.isOpened(): ret, frame = self.cap.read()
            else: ret, frame = False, None
            if not ret:
                if self.is_video and self.video_len > 0: self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0); continue
                else: time.sleep(0.1); continue
            if self.is_video: self.current_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            with self.lock: self.ret, self.frame = ret, frame
            time.sleep(0.005 if not self.is_video else 0.03)

    def read(self):
        with self.lock:
            return self.ret, self.frame.copy() if self.frame is not None else None

    def release(self):
        self.running = False
        self.cap.release()

# ==========================================
# 2. 全局配置
# ==========================================
ERR_NAMES_MAP = {
    'shrug': '耸肩',
    'arm': '小臂',
    'valgus': '膝扣',
    'rounding': '弓背',
    'depth': '深度',
    'range': '行程',
    'lunge_valgus': '前膝', 
    'lunge_depth': '幅度'
}

@dataclass(frozen=True)
class AlgoConfig:
    STD_HEIGHT: float = 180.0
    GLOBAL_DIR_FLIP: float = -1.0 
    LATERAL_GAIN: float = 0.5 
    ROUNDING_AMP: float = 6.5  
    LOC_THORAX: float = 0.33
    LOC_LUMBAR: float = 0.66
    HINGE_TOLERANCE_GAIN: float = 0.50 
    CAMERA_PITCH_TOLERANCE: float = 0.08
    CALIBRATION_RATE: float = 0.05
    VIEW_SIDE_RATIO: float = 0.28  
    VIEW_FRONT_RATIO: float = 0.45 

    PRESS_VERT_TOLERANCE: int = 25
    SHRUG_RATIO_TH: float = 0.35
    SHRUG_SMOOTH_FACTOR: float = 0.6
    
    SQUAT_CHECK_START_BASE: int = 300
    
    # [深蹲阈值]
    SQUAT_DOWN_TH_PIXEL: int = 80
    SQUAT_UP_TH_PIXEL: int = 120
    VALGUS_RATIO: float = 1.2
    
    # [弓步蹲 - 相对位移阈值]
    LUNGE_DROP_DOWN_RATIO: float = 0.15 # 下降 > 15% 躯干长 -> DOWN
    LUNGE_DROP_UP_RATIO: float = 0.10   # 下降 < 10% 躯干长 -> UP
    LUNGE_VALGUS_RATIO: float = 0.95 
    LUNGE_VALGUS_START_RATIO: float = 0.33 
    LUNGE_VALGUS_CHECK_OFFSET: int = 100 
    
    ROUNDING_COMPRESS_TH: float = 0.01 
    HINGE_ANGLE_MIN: float = 15.0
    
    RAISE_HEIGHT_RATIO: float = 0.5
    RAISE_GATE_WIDTH_RATIO: float = 2.0
    RAISE_GATE_CENTER_TOL: float = 0.5
    
    # 弓步蹲配置
    LUNGE_STANCE_X_RATIO: float = 0.5 
    LUNGE_KNEE_TOLERANCE_PIXEL: int = 35
    
    COUNT_COOLDOWN: float = 0.2
    GATEKEEPER_TIMEOUT: float = 0.5
    SQUAT_GATE_STANCE_RATIO: float = 0.5
    SQUAT_GATE_FEET_Y_TOL: float = 0.10
    SQUAT_GATE_ALIGN_TOL: float = 0.15
    SQUAT_GATE_GRAVITY_TOL: float = 0.2

@dataclass(frozen=True)
class TextConfig:
    WINDOW_NAME: str = "AEKE Fitness Mirror V2.20.0 (Startup Safe)"
    ACT_PRESS: str = "推举"
    ACT_SQUAT: str = "深蹲"
    ACT_RAISE: str = "前平举"
    ACT_LUNGE: str = "弓步蹲"
    LABEL_COUNT: str = "COUNT"
    LABEL_FPS: str = "FPS"
    LABEL_ACC: str = "正确率"
    LABEL_HEIGHT: str = "身高" 
    UNIT_CM: str = "cm"
    BTN_CAM: str = "摄像头"
    BTN_VIDEO: str = "导入视频"
    MSG_GOOD: str = "完美动作！"
    
    TIP_PRESS_DO: str = "请做“推举”动作"
    ERR_PRESS_ARM: str = "小臂全程垂直于地面效果更好！"
    ERR_PRESS_SHRUG: str = "动作中耸肩影响训练效果！"
    TIP_SQUAT_DO: str = "请做“深蹲”动作"
    ERR_SQUAT_DEPTH: str = "蹲至大腿平行地面效果更好！"
    ERR_SQUAT_VALGUS: str = "注意膝关节不要内扣！"
    ERR_SQUAT_ROUNDING: str = "背部挺直，不要弓腰！" 
    TIP_RAISE_DO: str = "请做“前平举”动作"
    ERR_RAISE_RANGE: str = "肘部抬至与肩等高效果更好"
    TIP_LUNGE_DO: str = "请做“弓步蹲”动作"
    ERR_LUNGE_KNEE: str = "注意前腿膝关节不要内扣！"
    ERR_LUNGE_DEPTH: str = "蹲至前腿平行地面效果更好！"

@dataclass(frozen=True)
class ColorConfig:
    BG: tuple = (15, 15, 20)
    GRID: tuple = (40, 40, 50)
    NEON_BLUE: tuple = (255, 200, 0)
    NEON_GREEN: tuple = (50, 255, 50)
    NEON_RED: tuple = (50, 50, 255)
    NEON_YELLOW: tuple = (0, 215, 255)
    NEON_ORANGE: tuple = (0, 140, 255)
    NEON_PURPLE: tuple = (255, 0, 255)
    FPS: tuple = (0, 255, 128)
    TEXT_MAIN: tuple = (250, 250, 250)
    TEXT_DIM: tuple = (160, 160, 160)
    UI_BORDER_NORMAL: tuple = (60, 60, 60)
    UI_BORDER_ACTIVE: tuple = (0, 215, 255)

@dataclass
class AppConfig:
    W: int = 1280
    H: int = 720
    HALF_W: int = 640
    FONT: str = "msyh.ttc"
    VOL: float = 0.5
    MENU_ANIM_STEP: float = 0.15 

# ==========================================
# 3. 核心工具
# ==========================================
class GeomUtils:
    @staticmethod
    def dist(p1, p2):
        return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

    @staticmethod
    def dist_3d(p1, p2):
        return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

    @staticmethod
    def is_vertical(p1, p2, tolerance):
        dx = abs(p1[0] - p2[0])
        dy = abs(p1[1] - p2[1])
        if dy == 0: return False
        return math.degrees(math.atan(dx / dy)) < tolerance

    @staticmethod
    def calc_inclination(p1, p2):
        dx = abs(p1[0] - p2[0])
        dy = abs(p1[1] - p2[1])
        if dy == 0: return 90.0
        return math.degrees(math.atan(dx/dy))

class PointSmoother:
    def __init__(self, alpha=0.5):
        self.prev_pts = {}
        self.min_alpha = 0.3
        self.max_alpha = 0.95

    def filter(self, current_pts):
        if not self.prev_pts:
            self.prev_pts = current_pts
            return current_pts
        smoothed = {}
        for k, v in current_pts.items():
            if v is None: 
                smoothed[k] = None
                continue
            if k not in self.prev_pts or self.prev_pts[k] is None:
                smoothed[k] = v
            else:
                prev = self.prev_pts[k]
                dist = math.hypot(v[0]-prev[0], v[1]-prev[1])
                dynamic_alpha = self.min_alpha + (self.max_alpha - self.min_alpha) * min(dist / 10.0, 1.0)
                sx = int(dynamic_alpha * v[0] + (1 - dynamic_alpha) * prev[0])
                sy = int(dynamic_alpha * v[1] + (1 - dynamic_alpha) * prev[1])
                smoothed[k] = (sx, sy)
        self.prev_pts = smoothed
        return smoothed

class SoundManager:
    def __init__(self):
        self.sounds = {}
        if HAS_AUDIO:
            try: self._gen_sounds()
            except: pass

    def _gen_wave(self, freq, dur, type='sine'):
        sr = 44100
        t = np.linspace(0, dur, int(sr*dur), False)
        if type == 'sine': w = np.sin(2*np.pi*freq*t)
        elif type == 'square': w = np.sign(np.sin(2*np.pi*freq*t))
        w *= np.linspace(1, 0, len(t)) * 0.5
        audio = (w * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(np.column_stack((audio, audio)))

    def _gen_sounds(self):
        self.sounds['count'] = self._gen_wave(880, 0.1)
        self.sounds['error'] = self._gen_wave(150, 0.4, 'square')
        t = np.linspace(0, 0.6, int(44100*0.6), False)
        w = (np.sin(2*np.pi*523*t) + np.sin(2*np.pi*659*t) + np.sin(2*np.pi*784*t))/3
        w *= np.linspace(1, 0, len(t)) * 0.5
        audio = (w * 32767).astype(np.int16)
        self.sounds['success'] = pygame.sndarray.make_sound(np.column_stack((audio, audio)))

    def play(self, name):
        if HAS_AUDIO and name in self.sounds:
            try:
                self.sounds[name].set_volume(AppConfig.VOL)
                self.sounds[name].play()
            except: pass

# ==========================================
# 5. 渲染引擎
# ==========================================
class UIRenderer:
    def __init__(self):
        try:
            self.font_lg = ImageFont.truetype(AppConfig.FONT, 42)
            self.font_md = ImageFont.truetype(AppConfig.FONT, 26)
            self.font_sm = ImageFont.truetype(AppConfig.FONT, 18)
            self.font_xs = ImageFont.truetype(AppConfig.FONT, 14)
        except:
            self.font_lg = self.font_md = self.font_sm = self.font_xs = ImageFont.load_default()
        
        self.menu_height_ratio = 0.0
        self.hit_boxes = {} 
        self.hover = {k:False for k in ["menu","height","seek_bar","btn_play","btn_cam","btn_video","i0","i1","i2","i3"]}
        self.update_layout(False, 4)

    def update_layout(self, menu_open, num_actions):
        self.hit_boxes['menu_btn'] = (20, 20, 240, 70)
        self.hit_boxes['height_input'] = (260, 20, 480, 70)
        self.hit_boxes['seek_bar'] = (60, AppConfig.H-25, AppConfig.W-20, AppConfig.H)
        self.hit_boxes['btn_play'] = (10, AppConfig.H-30, 50, AppConfig.H)
        by = AppConfig.H - 65
        self.hit_boxes['btn_cam'] = (20, by, 100, by+30)
        self.hit_boxes['btn_video'] = (120, by, 220, by+30)
        
        self.hit_boxes['menu_items'] = []
        if menu_open:
            for i in range(num_actions):
                y_start = 75 + i * 55
                self.hit_boxes['menu_items'].append((20, y_start, 240, y_start + 50))
        else:
            self.hit_boxes['menu_items'] = []

    def hit_test(self, x, y):
        if 'menu_items' in self.hit_boxes:
            for i, rect in enumerate(self.hit_boxes['menu_items']):
                if rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]:
                    return f"item_{i}"
        for name, rect in self.hit_boxes.items():
            if name == 'menu_items': continue
            if rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]:
                return name
        return None

    def update_hover(self, x, y, menu_open, num_actions=4):
        self.update_layout(menu_open, num_actions)
        for k in self.hover: self.hover[k] = False
        hit = self.hit_test(x, y)
        if hit == 'menu_btn': self.hover['menu'] = True
        elif hit == 'height_input': self.hover['height'] = True
        elif hit == 'seek_bar': self.hover['seek_bar'] = True
        elif hit == 'btn_play': self.hover['btn_play'] = True
        elif hit == 'btn_cam': self.hover['btn_cam'] = True
        elif hit == 'btn_video': self.hover['btn_video'] = True
        elif hit and hit.startswith('item_'):
            idx = int(hit.split('_')[1])
            self.hover[f"i{idx}"] = True

    def draw_skeleton(self, img, pts, is_avatar=False):
        if not pts: return
        limbs = [('ls','le'),('le','lw'),('rs','re'),('re','rw'),('ls','lh'),('rs','rh'),('lh','rh'),('ls','rs'),('lh','lk'),('lk','la'),('rh','rk'),('rk','ra')]
        for u, v in limbs:
            if pts.get(u) and pts.get(v):
                cv2.line(img, pts[u], pts[v], ColorConfig.NEON_BLUE, 4 if is_avatar else 2)
        
        if pts.get('waist') and pts.get('thorax') and pts.get('neck') and pts.get('hip'):
            is_bad = pts.get('rounding_bad', False)
            if not is_bad:
                col = ColorConfig.NEON_PURPLE
                w = 3 if is_avatar else 2
                cv2.line(img, pts['neck'], pts['thorax'], col, w)
                cv2.line(img, pts['thorax'], pts['waist'], col, w)
                cv2.line(img, pts['waist'], pts['hip'], col, w)
                cv2.circle(img, pts['thorax'], 5, col, -1)
                cv2.circle(img, pts['waist'], 6, col, -1)

        for k, p in pts.items():
            if p and k not in ['nose', 'neck', 'thorax', 'lumbar', 'waist', 'hip', 'spine_state', 'rounding_bad']:
                cv2.circle(img, p, 5, ColorConfig.NEON_YELLOW, -1)
                cv2.circle(img, p, 2, (255,255,255), -1)

    def _draw_arrow(self, img, start, vec, col, gap, base):
        dx, dy = vec
        mag = math.hypot(dx, dy)
        if mag == 0: return
        ux, uy = dx/mag, dy/mag
        l = base + int(8 * math.sin(time.time() * 15))
        s = (int(start[0]+ux*gap), int(start[1]+uy*gap))
        e = (int(s[0]+ux*l), int(s[1]+uy*l))
        cv2.arrowedLine(img, s, e, col, 4, cv2.LINE_AA, tipLength=0.3)

    def _draw_dash(self, img, p1, p2, col, thickness=2):
        dist = GeomUtils.dist(p1, p2)
        if dist < 10: return
        pts = np.linspace(p1, p2, int(dist/15)).astype(int)
        for i in range(len(pts)-1):
            if i % 2 == 0: cv2.line(img, tuple(pts[i]), tuple(pts[i+1]), col, thickness)

    def _draw_check(self, img, center):
        cx, cy = center
        pts = np.array([[cx - 10, cy], [cx - 3, cy + 10], [cx + 20, cy - 15]], np.int32)
        cv2.polylines(img, [pts], False, ColorConfig.NEON_GREEN, 4, cv2.LINE_AA)
        
    def draw_visuals(self, img, visuals):
        for h in visuals:
            ok = h.get('ok', False)
            col = ColorConfig.NEON_GREEN if ok else ColorConfig.NEON_RED
            tag = h.get('type')

            if tag == 'press_guide':
                s, e = h['wrist'], h['elbow']
                target = (e[0], e[1] - int(GeomUtils.dist(s, e)))
                self._draw_dash(img, e, target, col)
                cv2.circle(img, target, 12, col, 2)
                cv2.circle(img, s, 8, col, -1)
                if not ok:
                    vec = (target[0]-s[0], 0)
                    self._draw_arrow(img, s, vec, col, gap=20, base=50)
                else: self._draw_check(img, (s[0], s[1]-30))

            elif tag == 'squat_valgus':
                pt, side = h['pt'], h['side']
                if h.get('foot_pt') is not None:
                    foot_pt = h['foot_pt']
                    target_y = pt[1] - 100
                    self._draw_dash(img, foot_pt, (foot_pt[0], target_y), ColorConfig.NEON_ORANGE if not ok else ColorConfig.NEON_GREEN)
                
                if ok: 
                    self._draw_check(img, (pt[0], pt[1]-30))
                else:
                    center_x = AppConfig.W // 4 
                    vec = (-1, 0) if pt[0] < center_x else (1, 0)
                    self._draw_arrow(img, pt, vec, col, gap=20, base=60)

            elif tag == 'depth' or tag == 'lunge_depth': 
                p1, p2 = h['p1'], h['p2']
                self._draw_dash(img, p1, p2, col)
                cv2.circle(img, p1, 8, col, -1)
                cv2.circle(img, p2, 8, col, 2)
            
            elif tag == 'bounce_arrow': 
                pt, side = h['start'], h['side']
                if ok: self._draw_check(img, (pt[0], pt[1]-30))
                else:
                    center_x = AppConfig.W // 4 
                    vec = (-1, 0) if pt[0] < center_x else (1, 0)
                    self._draw_arrow(img, pt, vec, col, gap=20, base=60)
            
            elif tag == 'rounding_guide':
                pts_curve = [h['neck'], h['thorax'], h['waist'], h['hip']]
                cv2.polylines(img, [np.array(pts_curve)], False, ColorConfig.NEON_RED, 4, cv2.LINE_AA)
                self._draw_dash(img, h['neck'], h['hip'], ColorConfig.NEON_GREEN, 1)
                target_pt = h['waist'] 
                push_dir = 1 if target_pt[0] < h['neck'][0] else -1
                start_arrow = (target_pt[0] - (push_dir * 80), target_pt[1])
                self._draw_arrow(img, start_arrow, (target_pt[0]-start_arrow[0], 0), ColorConfig.NEON_ORANGE, gap=0, base=60)
                cv2.circle(img, target_pt, 8, ColorConfig.NEON_RED, -1)

            elif tag == 'raise_guide':
                s, e = h['shoulder'], h['elbow']
                target = (e[0], s[1])
                self._draw_dash(img, s, target, col)
                cv2.circle(img, target, 10, col, 2)
                if not ok:
                    self._draw_arrow(img, e, (0, -1), col, gap=20, base=50)
                    cv2.circle(img, e, 8, col, -1)
                else:
                    self._draw_check(img, (e[0], e[1]-40))
            
            elif tag == 'lunge_knee_guide':
                k, d = h['knee'], h['direction']
                foot_pt = h.get('foot_pt')

                if ok: 
                    self._draw_check(img, (k[0], k[1]-40))
                else:
                    vec = (1, 0) if d == 'right' else (-1, 0)
                    self._draw_arrow(img, k, vec, col, gap=25, base=70)

                if foot_pt is not None:
                     target_y = k[1] - 100
                     self._draw_dash(img, foot_pt, (foot_pt[0], target_y), ColorConfig.NEON_ORANGE if not ok else ColorConfig.NEON_GREEN)

    def _box(self, draw, img, rect, col):
        x1, y1, x2, y2 = rect
        if x1 < 0: x1 = 0
        if y1 < 0: y1 = 0
        sub = img[y1:y2, x1:x2]
        if sub.size > 0:
            black = np.zeros_like(sub)
            img[y1:y2, x1:x2] = cv2.addWeighted(sub, 0.2, black, 0.8, 0)
        if draw: draw.rectangle(rect, outline=(col[2],col[1],col[0]), width=2)

    def draw_text_shadow(self, draw, x, y, text, font, col):
        draw.text((x+2, y+2), text, font=font, fill=(0,0,0))
        draw.text((x, y), text, font=font, fill=(col[2], col[1], col[0]))

    def draw_all_text_layers(self, img, mode, count, fps, menu, h_str, typing, msg, msg_color, error_stats, bad_reps, vid, paused):
        self.update_layout(menu, 4)
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil)

        target = 1.0 if menu else 0.0
        step = AppConfig.MENU_ANIM_STEP
        if self.menu_height_ratio < target: self.menu_height_ratio = min(self.menu_height_ratio + step, target)
        elif self.menu_height_ratio > target: self.menu_height_ratio = max(self.menu_height_ratio - step, target)

        c_menu = ColorConfig.UI_BORDER_ACTIVE if self.hover["menu"] else ColorConfig.UI_BORDER_NORMAL
        self._box(draw, img, self.hit_boxes['menu_btn'], c_menu)
        self.draw_text_shadow(draw, 40, 25, mode, self.font_md, ColorConfig.NEON_YELLOW)
        draw.text((190, 30), "▼", font=self.font_sm, fill=ColorConfig.TEXT_DIM)

        h_box_x = 260
        h_rect = (h_box_x, 20, h_box_x+220, 70)
        c_h = ColorConfig.UI_BORDER_ACTIVE if (typing or self.hover["height"]) else ColorConfig.UI_BORDER_NORMAL
        self._box(draw, img, h_rect, c_h)
        self.draw_text_shadow(draw, 270, 32, "身高", self.font_sm, ColorConfig.TEXT_DIM)
        disp_h = h_str + ("|" if (typing and time.time()%1>0.5) else "")
        self.draw_text_shadow(draw, 330, 27, disp_h, self.font_md, ColorConfig.TEXT_MAIN)
        self.draw_text_shadow(draw, 420, 32, "cm", self.font_sm, ColorConfig.TEXT_DIM)

        if self.menu_height_ratio > 0.01:
            opts = [TextConfig.ACT_PRESS, TextConfig.ACT_SQUAT, TextConfig.ACT_RAISE, TextConfig.ACT_LUNGE]
            y = 75
            for i, m in enumerate(opts):
                ci = ColorConfig.UI_BORDER_ACTIVE if self.hover[f"i{i}"] else ColorConfig.UI_BORDER_NORMAL
                self._box(draw, img, (20, y, 220, y+50), ci)
                self.draw_text_shadow(draw, 40, y+12, m, self.font_md, ColorConfig.TEXT_MAIN)
                y += 55

        count_str = str(count) if count is not None else "0"
        rx_count = AppConfig.W - 200 
        self.draw_text_shadow(draw, rx_count, 20, TextConfig.LABEL_COUNT, self.font_sm, ColorConfig.TEXT_DIM)
        self.draw_text_shadow(draw, rx_count + 80, 10, count_str, self.font_lg, ColorConfig.NEON_YELLOW)

        rx_acc = rx_count - 220
        acc_str = "-"
        acc_col = ColorConfig.NEON_YELLOW
        if count > 0:
            acc_val = int(((count - bad_reps) / count) * 100)
            acc_val = max(0, acc_val)
            acc_str = f"{acc_val}%"
            acc_col = ColorConfig.NEON_GREEN if acc_val >= 80 else (ColorConfig.NEON_ORANGE if acc_val >= 60 else ColorConfig.NEON_RED)
            
        self.draw_text_shadow(draw, rx_acc, 20, TextConfig.LABEL_ACC, self.font_sm, ColorConfig.TEXT_DIM)
        self.draw_text_shadow(draw, rx_acc + 80, 10, acc_str, self.font_lg, acc_col)
        
        rx_stat = rx_acc - 180
        for err_key, err_name in ERR_NAMES_MAP.items():
            err_val = error_stats.get(err_key, 0)
            if err_val > 0:
                self.draw_text_shadow(draw, rx_stat, 25, err_name, self.font_sm, ColorConfig.TEXT_DIM)
                self.draw_text_shadow(draw, rx_stat + 90, 25, str(err_val), self.font_md, ColorConfig.NEON_RED)
                rx_stat -= 160 

        self.draw_text_shadow(draw, 20, AppConfig.H - 30, f"{TextConfig.LABEL_FPS}: {fps}", self.font_xs, ColorConfig.FPS)

        if msg:
            H, W = img.shape[:2]
            bbox = draw.textbbox((0,0), msg, font=self.font_lg)
            tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
            pad = 40
            cx, cy = W//2, H-100
            x1, y1, x2, y2 = cx - tw//2 - pad, cy - th//2 - pad, cx + tw//2 + pad, cy + th//2 + pad
            self._box(draw, img, (x1, y1, x2, y2), msg_color)
            draw.text((x1+pad, y1+pad-5), msg, font=self.font_lg, fill=(msg_color[2], msg_color[1], msg_color[0]))

        img[:] = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

# ==========================================
# 6. 逻辑核心
# ==========================================
class LogicEngine:
    def __init__(self, sound_mgr):
        self.sound = sound_mgr
        self.mode = TextConfig.ACT_PRESS
        self.counter = 0
        self.bad_reps = 0 
        self.current_rep_has_error = False 
        self.stage = "start"
        self.history = {}
        self.active_errs = set()
        self.error_counts = {} 
        self.msg = ""
        self.msg_color = ColorConfig.TEXT_DIM
        self.msg_timer = 0
        self.last_act = time.time()
        self.cycle_flags = {}
        self.max_torso_len = 0.0
        self.base_shrug_dist = 0
        self.neck_curr_smooth = 0.0
        
        # 弓步蹲状态
        self.prev_hip_y = 0
        self.stand_y = 0.0 
        self.prev_hy = 0
        self.front_idx = None
        self.lunge_front_idx = None 
        
        self.last_count_time = 0.0 
        self.facing_score_smooth = 0.0 
        self.smoother = PointSmoother(alpha=AlgoConfig.SHRUG_SMOOTH_FACTOR)

    def set_mode(self, m):
        if self.mode == m: return
        self.mode = m
        self.counter = 0
        self.bad_reps = 0
        self.error_counts = {}
        self.history = {}
        self.active_errs = set()
        self.msg = ""
        self.stage = "start"
        self.max_torso_len = 0.0
        
        self.prev_hip_y = 0
        self.stand_y = 0.0
        self.prev_hy = 0
        self.front_idx = None
        self.lunge_front_idx = None

    def update(self, pts, world_pts, vis_scores, user_height_cm):
        if not pts: return []
        vis = []
        pts = self.smoother.filter(pts)
        scale = user_height_cm / AlgoConfig.STD_HEIGHT
        
        self._update_elastic_spine(pts)
        
        if self.stage == "up": self.stage = "start"
        
        if not self._gatekeeper(pts):
            return vis, pts
            
        if self.mode == TextConfig.ACT_PRESS: self._press(pts, vis, scale)
        elif self.mode == TextConfig.ACT_SQUAT: self._squat(pts, vis, scale)
        elif self.mode == TextConfig.ACT_RAISE: self._front_raise(pts, world_pts, vis, scale)
        elif self.mode == TextConfig.ACT_LUNGE: self._lunge(pts, vis, scale)
        
        if pts.get('rounding_bad') and 'rounding' in self.active_errs:
            vis.append({'type': 'rounding_guide', 'neck': pts['neck'], 'thorax': pts['thorax'], 'waist': pts['waist'], 'hip': pts['hip']})
            
        return vis, pts

    def _update_elastic_spine(self, pts):
        if not (pts.get('ls') and pts.get('rs') and pts.get('lh') and pts.get('rh') and pts.get('neck') and pts.get('hip')): return

        ls, rs = np.array(pts['ls']), np.array(pts['rs'])
        lh, rh = np.array(pts['lh']), np.array(pts['rh'])
        neck = (ls + rs) / 2
        hip = (lh + rh) / 2
        vec_torso = hip - neck
        len_torso = np.linalg.norm(vec_torso)
        if len_torso < 10: return

        len_left = np.linalg.norm(ls - lh)
        len_right = np.linalg.norm(rs - rh)
        lateral_diff = (len_right - len_left) * AlgoConfig.LATERAL_GAIN
        
        is_standing = GeomUtils.calc_inclination(pts['neck'], pts['hip']) < 20
        if is_standing:
            if len_torso > self.max_torso_len: 
                self.max_torso_len = len_torso
            elif self.max_torso_len > 0:
                self.max_torso_len = self.max_torso_len * (1-AlgoConfig.CALIBRATION_RATE) + len_torso * AlgoConfig.CALIBRATION_RATE
        
        compression_ratio = 0.0
        if self.max_torso_len > 0:
            compression_ratio = max(0.0, 1.0 - (len_torso / self.max_torso_len))

        u_torso = vec_torso / len_torso
        n_torso = np.array([-u_torso[1], u_torso[0]]) 
        face_sign = 1.0 if ls[0] < rs[0] else -1.0
        back_vec = n_torso * face_sign * AlgoConfig.GLOBAL_DIR_FLIP
        
        angle_rad = math.atan2(vec_torso[0], vec_torso[1]) 
        inclination = abs(math.degrees(angle_rad))
        
        inclination_factor = min(inclination / 90.0, 1.0)
        hinge_allowance = inclination_factor * AlgoConfig.HINGE_TOLERANCE_GAIN
        
        pitch_allowance = AlgoConfig.CAMERA_PITCH_TOLERANCE if is_standing else 0.0
        total_tolerance = hinge_allowance + pitch_allowance
        effective_compression = max(0.0, compression_ratio - total_tolerance)
        
        rounding_force = effective_compression * AlgoConfig.ROUNDING_AMP
        if inclination < AlgoConfig.HINGE_ANGLE_MIN: 
             rounding_force = -compression_ratio * 0.5

        lateral_vec = n_torso * lateral_diff
        sagittal_offset = back_vec * (rounding_force * len_torso)
        t_offset = lateral_vec + sagittal_offset
        l_offset = lateral_vec + (sagittal_offset * 1.5)
        t_base = neck + vec_torso * AlgoConfig.LOC_THORAX
        pt_thorax = t_base + t_offset
        l_base = neck + vec_torso * AlgoConfig.LOC_LUMBAR
        pt_lumbar = l_base + l_offset
        pts['neck'] = (int(neck[0]), int(neck[1]))
        pts['hip'] = (int(hip[0]), int(hip[1]))
        pts['thorax'] = (int(pt_thorax[0]), int(pt_thorax[1]))
        pts['waist'] = (int(pt_lumbar[0]), int(pt_lumbar[1]))
        pts['lumbar'] = pts['waist']
        pts['spine_state'] = 'neutral'
        pts['rounding_bad'] = False
        if inclination > AlgoConfig.HINGE_ANGLE_MIN and effective_compression > AlgoConfig.ROUNDING_COMPRESS_TH:
            pts['spine_state'] = 'rounding'
            pts['rounding_bad'] = True

    def _gatekeeper(self, pts):
        is_similar = False
        tip = ""
        if self.mode == TextConfig.ACT_PRESS:
            tip = TextConfig.TIP_PRESS_DO
            if pts.get('lw') and pts.get('rw') and pts.get('ls') and pts.get('rs'):
                wrist_y = (pts['lw'][1]+pts['rw'][1])/2
                shou_y = (pts['ls'][1]+pts['rs'][1])/2
                if wrist_y < shou_y + 200: is_similar = True
                
        elif self.mode == TextConfig.ACT_SQUAT:
            tip = TextConfig.TIP_SQUAT_DO
            if pts.get('lh') and pts.get('rh'):
                if abs(pts['lh'][0]-pts['rh'][0]) > 20: is_similar = True
                
        elif self.mode == TextConfig.ACT_RAISE:
            tip = TextConfig.TIP_RAISE_DO
            if pts.get('ls') and pts.get('rs') and pts.get('lw') and pts.get('rw'):
                sw = GeomUtils.dist(pts['ls'], pts['rs'])
                ww = GeomUtils.dist(pts['lw'], pts['rw'])
                if ww <= sw * 2.5: is_similar = True
        
        elif self.mode == TextConfig.ACT_LUNGE:
            tip = TextConfig.TIP_LUNGE_DO
            if pts.get('lt') and pts.get('rt') and pts.get('ls') and pts.get('rs'):
                fd = abs(pts['lt'][0]-pts['rt'][0])
                sw = abs(pts['ls'][0]-pts['rs'][0])
                if fd > sw * 0.5: is_similar = True

        if is_similar:
            self.last_act = time.time()
            if self.msg == tip: self.msg = ""
            return True
        else:
            if time.time() - self.last_act > AlgoConfig.GATEKEEPER_TIMEOUT:
                if not self.active_errs: self._set_msg(tip, ColorConfig.NEON_RED, perm=True)
            return False

    def _check_shrug_adaptive(self, p, scale, stage_check="down"):
        if not (p.get('ls') and p.get('rs') and p.get('le_ear') and p.get('re_ear')): return
        shou_y = (p['ls'][1] + p['rs'][1]) / 2
        ear_y = (p['le_ear'][1] + p['re_ear'][1]) / 2
        curr_dist = max(0, shou_y - ear_y)
        if self.stage == "start":
            if curr_dist > 0: self.base_shrug_dist = max(self.base_shrug_dist, curr_dist)
            self.active_errs.discard('shrug')
            self.cycle_flags['shrug'] = True
        if self.stage == stage_check and self.base_shrug_dist > 0:
            if curr_dist / (self.base_shrug_dist + 1e-6) < AlgoConfig.SHRUG_RATIO_TH: self.cycle_flags['shrug'] = False

    def _front_raise(self, p, wp, vis, scale):
        if not (p.get('lw') and p.get('rw') and p.get('le') and p.get('re') and p.get('ls') and p.get('rs')): return
        wy = (p['lw'][1]+p['rw'][1])/2
        sy = (p['ls'][1]+p['rs'][1])/2
        ty = (p['le'][1]+p['re'][1])/2
        
        if self.stage == "start" and wy < ty:
            self.stage = "down"; self._reset_flags(["range","shrug"]); self.current_rep_has_error = False
        elif self.stage == "down" and wy > sy + 100:
            self.stage = "start"
            self.counter += 1; self._end_cycle(["range","shrug"])

        if self.stage == "down":
            lt = GeomUtils.dist_3d(wp[23], wp[11])
            la = GeomUtils.dist_3d(wp[11], wp[13])
            ld = wp[13].y - wp[11].y
            lal = la - (lt * AlgoConfig.RAISE_HEIGHT_RATIO)
            rt = GeomUtils.dist_3d(wp[24], wp[12])
            ra = GeomUtils.dist_3d(wp[12], wp[14])
            rd = wp[14].y - wp[12].y
            ral = ra - (rt * AlgoConfig.RAISE_HEIGHT_RATIO)
            if ld < lal and rd < ral: self.cycle_flags['range'] = True
        
        self._check_shrug_adaptive(p, scale, "down")
        if 'range' in self.active_errs:
            self._set_msg(TextConfig.ERR_RAISE_RANGE, ColorConfig.NEON_RED, perm=True)
            vis.append({'type':'raise_guide', 'shoulder':p['ls'], 'elbow':p['le'], 'ok':self.cycle_flags.get('range', True)})
            vis.append({'type':'raise_guide', 'shoulder':p['rs'], 'elbow':p['re'], 'ok':self.cycle_flags.get('range', True)})
        elif 'shrug' in self.active_errs:
            self._set_msg(TextConfig.ERR_PRESS_SHRUG, ColorConfig.NEON_RED, perm=True)

    def _press(self, p, vis, scale):
        if not (p.get('lw') and p.get('rw') and p.get('le') and p.get('re') and p.get('ls') and p.get('rs')): return
        wrist_y = (p['lw'][1]+p['rw'][1])/2
        shou_y = (p['ls'][1]+p['rs'][1])/2
        nose_y = p['nose'][1] if p.get('nose') else 0
        
        if self.stage == "start" and wrist_y < nose_y - 50:
            self.stage = "down"; self._reset_flags(["arm","shrug"]); self.current_rep_has_error = False
        elif self.stage == "down" and wrist_y > nose_y:
            self.stage = "start"
            self.counter += 1; self._end_cycle(["arm","shrug"])
        
        if self.stage == "down":
            lok = GeomUtils.is_vertical(p['lw'], p['le'], AlgoConfig.PRESS_VERT_TOLERANCE)
            rok = GeomUtils.is_vertical(p['rw'], p['re'], AlgoConfig.PRESS_VERT_TOLERANCE)
            if not (lok and rok): self.cycle_flags['arm'] = False
        
        self._check_shrug_adaptive(p, scale, "down")
        if 'arm' in self.active_errs:
            self._set_msg(TextConfig.ERR_PRESS_ARM, ColorConfig.NEON_RED, perm=True)
            vis.append({'type':'press_guide', 'elbow':p['le'], 'wrist':p['lw'], 'ok':self.cycle_flags.get('arm', True)})
            vis.append({'type':'press_guide', 'elbow':p['re'], 'wrist':p['rw'], 'ok':self.cycle_flags.get('arm', True)})
        elif 'shrug' in self.active_errs:
            self._set_msg(TextConfig.ERR_PRESS_SHRUG, ColorConfig.NEON_RED, perm=True)

    def _squat(self, p, vis, scale):
        if not (p.get('lh') and p.get('rh') and p.get('lk') and p.get('rk') and 
                p.get('lt') and p.get('rt') and p.get('la') and p.get('ra')): return
        hy, ky = (p['lh'][1]+p['rh'][1])/2, (p['lk'][1]+p['rk'][1])/2
        
        in_valgus_check_zone = False # Init
        
        if self.prev_hip_y == 0: self.prev_hip_y = hy
        desc = hy > (self.prev_hip_y + 2) 
        self.prev_hip_y = hy 
        
        # [深蹲计次 - 像素阈值]
        if self.stage == "start" and hy > ky - AlgoConfig.SQUAT_DOWN_TH_PIXEL:
            self.stage = "down"
            self._reset_flags(["rounding", "valgus", "depth"])
            self.current_rep_has_error = False
            
        elif self.stage == "down" and hy < ky - AlgoConfig.SQUAT_UP_TH_PIXEL:
            self.stage = "start"
            self.counter += 1
            self._end_cycle(["rounding", "valgus", "depth"])
            
        deep = hy >= ky - 30
        
        hip_w = abs(p['lh'][0] - p['rh'][0])
        knee_w = abs(p['lk'][0] - p['rk'][0])
        is_valgus = knee_w < (hip_w * AlgoConfig.VALGUS_RATIO)
        
        in_valgus_check_zone = hy > ky - 200
        
        if self.stage == "down" and desc and in_valgus_check_zone:
            if is_valgus: self.cycle_flags['valgus'] = False
            if p.get('rounding_bad'): self.cycle_flags['rounding'] = False
        
        if self.stage == "down" and deep: self.cycle_flags['depth'] = True
            
        if 'valgus' in self.active_errs:
            self._set_msg(TextConfig.ERR_SQUAT_VALGUS, ColorConfig.NEON_RED, perm=True)
            
            foot_exists = p.get('lt') is not None and p.get('rt') is not None and p.get('la') is not None and p.get('ra') is not None
            l_foot_center = ((p['la'][0] + p['lt'][0])//2, p['lt'][1]) if foot_exists else None
            r_foot_center = ((p['ra'][0] + p['rt'][0])//2, p['rt'][1]) if foot_exists else None

            vis.append({'type':'squat_valgus', 'pt':p['lk'], 'side':'left', 'foot_pt': l_foot_center, 'ok':not is_valgus})
            vis.append({'type':'squat_valgus', 'pt':p['rk'], 'side':'right', 'foot_pt': r_foot_center, 'ok':not is_valgus})

        elif 'depth' in self.active_errs:
            self._set_msg(TextConfig.ERR_SQUAT_DEPTH, ColorConfig.NEON_RED, perm=True)
            p1 = ((p['lh'][0]+p['rh'][0])//2, int(hy))
            p2 = ((p['lk'][0]+p['rk'][0])//2, int(ky))
            vis.append({'type':'depth', 'p1':p1, 'p2':p2, 'ok':deep})
            
        elif 'rounding' in self.active_errs:
            self._set_msg(TextConfig.ERR_SQUAT_ROUNDING, ColorConfig.NEON_RED, perm=True)
            vis.append({'type': 'rounding_guide', 'neck': p['neck'], 'thorax': p['thorax'], 'waist': p['waist'], 'hip': p['hip']})

    # [弓步蹲 - 相对位移法逻辑恢复]
    def _lunge(self, pts, vis, scale):
        # 1. 变量强制初始化
        is_descending = False
        valgus = False
        
        if not (pts.get('lt') and pts.get('rt') and pts.get('ls') and pts.get('rs') and pts.get('la') and pts.get('ra')):
             return

        if not pts.get('lk'): return 
        
        # 前腿识别
        curr_front = 25 if pts['la'][1] > pts['ra'][1] else 26
        idx = self.front_idx if self.front_idx else curr_front
        
        fk = pts['lk'] if idx == 25 else pts['rk']
        fh = pts['lh'] if idx == 25 else pts['rh']
        fa = pts['la'] if idx == 25 else pts['ra']
        ft = pts['lt'] if idx == 25 else pts['rt']
        
        hy, ky = fh[1], fk[1]
        
        if self.stand_y == 0 or hy < self.stand_y: self.stand_y = hy
        
        if self.prev_hy == 0: self.prev_hy = hy
        desc = hy > self.prev_hy + 5 
        self.prev_hy = hy
        
        drop = hy - self.stand_y
        max_drop = self.max_torso_len if self.max_torso_len > 0 else 200 
        
        # 状态机：DOWN (drop > 15%)
        if self.stage == "start" and drop > max_drop * AlgoConfig.LUNGE_DROP_DOWN_RATIO:
            self.stage = "down"
            self.current_rep_has_error = False
            self.active_errs.clear()
            self.front_idx = curr_front 
            
        # 状态机：UP (drop < 10%)
        elif self.stage == "down" and drop < max_drop * AlgoConfig.LUNGE_DROP_UP_RATIO:
            self.stage = "start"
            if time.time() - self.last_count_time > AlgoConfig.COUNT_COOLDOWN:
                self.counter += 1
                self.sound.play('count')
                self.last_count_time = time.time()
                if self.current_rep_has_error: self.bad_reps += 1
                else: self.sound.play('success')
            self.front_idx = None # Unlock
            self.stand_y = 0

        # Correction
        is_deep = hy >= ky - 30
        if self.stage == "down" and is_deep: self.cycle_flags['lunge_depth'] = True
        
        direction = 'left'
        
        if self.front_idx:
            # 重新获取锁定后的前腿关键点
            idx = self.front_idx
            fk = pts['lk'] if idx == 25 else pts['rk']
            fa = pts['la'] if idx == 25 else pts['ra']
            ft = pts['lt'] if idx == 25 else pts['rt']
            fheel = pts['lhe'] if idx == 25 else pts['rhe']
            
            # 足中点计算
            mid_foot_x = (ft[0]+fheel[0])/2 if (ft and fheel) else fa[0]
            
            # 内扣判定
            if idx == 25: # 左腿在前
                if fk[0] < mid_foot_x - 35: valgus = True; direction = 'right'
            else: # 右腿在前
                if fk[0] > mid_foot_x + 35: valgus = True; direction = 'left'
            
            # 触发条件
            if self.stage == "down" and desc and drop > max_drop * 0.2 and valgus:
                # 直接添加错误 (复刻历史逻辑行为)
                if 'lunge_valgus' not in self.active_errs:
                     self.active_errs.add('lunge_valgus')
                     self.error_counts['lunge_valgus'] = self.error_counts.get('lunge_valgus', 0) + 1
                     self.current_rep_has_error = True
                     self.sound.play('error')
            
            # Visualization
            if 'lunge_valgus' in self.active_errs:
                if self.stage == "down":
                    foot_center = ((fa[0] + ft[0])//2, (fa[1] + ft[1])//2) if ft else None
                    vis.append({
                        'type': 'lunge_knee_guide', 
                        'knee': fk, 
                        'foot_pt': foot_center,
                        'direction': direction, 
                        'ok': not valgus
                    })
                self._set_msg(TextConfig.ERR_LUNGE_KNEE, ColorConfig.NEON_RED, perm=True)
                
            elif 'lunge_depth' in self.active_errs: 
                 pass

    def _reset_flags(self, keys):
        for k in keys:
            if k in ["depth", "range", "lunge_valgus", "lunge_depth"]: self.cycle_flags[k] = False
            else: self.cycle_flags[k] = True

    def _end_cycle(self, keys):
        fixed, triggered = False, False
        if time.time() - self.last_count_time < AlgoConfig.COUNT_COOLDOWN: return 

        for i, k in enumerate(keys):
            res = self.cycle_flags.get(k, True)
            if not res:
                self.error_counts[k] = self.error_counts.get(k, 0) + 1
                self.current_rep_has_error = True
            st = self._update_hist(k, res)
            is_active = (st == 'TRIGGER') or (k in self.active_errs)
            if is_active and not res:
                triggered = True
                for lower_k in keys[i+1:]:
                    if lower_k in self.active_errs: self.active_errs.remove(lower_k)
                break
            if st == 'FIXED': fixed = True
        
        if self.current_rep_has_error: self.bad_reps += 1

        if triggered: self.sound.play('error')
        elif fixed:
            self.sound.play('success')
            if not self.active_errs: self._set_msg(TextConfig.MSG_GOOD, ColorConfig.NEON_GREEN, 3.0)
        elif not any(k in self.active_errs for k in keys):
            self.sound.play('count')
        self.last_count_time = time.time()

    def _update_hist(self, k, res, block=False):
        if k not in self.history: self.history[k] = []
        self.history[k].append(res)
        if len(self.history[k]) > 5: self.history[k].pop(0)
        if k in self.active_errs:
            if res:
                self.active_errs.remove(k)
                return 'FIXED'
        else:
            if not block and len(self.history[k])>=2 and not any(self.history[k][-2:]):
                self.active_errs.add(k)
                return 'TRIGGER'
        return 'NONE'

    def _set_msg(self, t, c, dur=0, perm=False):
        if time.time() < self.msg_timer: return
        self.msg, self.msg_color = t, c
        self.msg_timer = (time.time() + dur) if dur > 0 else 0

    def get_msg(self):
        if time.time() < self.msg_timer or self.msg_timer == 0: return self.msg, self.msg_color
        return "", ColorConfig.TEXT_DIM

# ==========================================
# 7. 主程序
# ==========================================
def main():
    cam_loader = CameraLoader(0, AppConfig.W, AppConfig.H)
    time.sleep(1.0)
    
    # 简单的无信号检查
    if not cam_loader.ret and not cam_loader.is_video:
        print("Camera not ready, waiting...")
        time.sleep(2.0)
    
    pose = mp.solutions.pose.Pose(min_detection_confidence=0.6, model_complexity=1)
    engine = LogicEngine(SoundManager())
    renderer = UIRenderer()
    
    cv2.namedWindow(TextConfig.WINDOW_NAME, cv2.WINDOW_NORMAL)
    menu_open = False
    prev_time = time.time()
    fps = 0
    user_height_str = "180"
    is_typing = False
    
    def mouse_cb(e, x, y, f, p):
        nonlocal menu_open, is_typing
        renderer.update_hover(x, y, menu_open)
        if e == cv2.EVENT_LBUTTONDOWN:
            if 260 < x < 480 and 20 < y < 70:
                is_typing = True
                menu_open = False
            else:
                is_typing = False
                if x < 240 and y < 70: menu_open = not menu_open
                elif menu_open and x < 240:
                    if 75 < y < 130: engine.set_mode(TextConfig.ACT_PRESS); menu_open=False
                    elif 130 < y < 185: engine.set_mode(TextConfig.ACT_SQUAT); menu_open=False
                    elif 185 < y < 240: engine.set_mode(TextConfig.ACT_RAISE); menu_open=False
                    elif 240 < y < 295: engine.set_mode(TextConfig.ACT_LUNGE); menu_open=False
    cv2.setMouseCallback(TextConfig.WINDOW_NAME, mouse_cb)

    while cam_loader.running:
        ret, frame = cam_loader.read()
        
        # [Fix] Handle camera failure gracefully
        if not ret: 
            # Show a blank screen with text if no camera
            blank = np.zeros((AppConfig.H, AppConfig.W, 3), dtype=np.uint8)
            cv2.putText(blank, "No Signal - Check Camera", (50, AppConfig.H//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
            cv2.imshow(TextConfig.WINDOW_NAME, blank)
            if cv2.waitKey(1) & 0xFF == 27: break
            time.sleep(0.1)
            continue
            
        frame = cv2.flip(frame, 1)
        
        curr_time = time.time()
        if curr_time - prev_time > 0: fps = int(1 / (curr_time - prev_time))
        prev_time = curr_time
        
        cw = AppConfig.HALF_W
        sx = (frame.shape[1] - cw) // 2
        f_l = frame[:, sx:sx+cw].copy()
        
        res = pose.process(cv2.cvtColor(f_l, cv2.COLOR_BGR2RGB))
        pts, hints = {}, []
        world_pts = None
        vis_scores = []
        
        if res.pose_landmarks:
            vis_scores = [lm.visibility for lm in res.pose_landmarks.landmark]
            imap = {11:'ls',12:'rs',13:'le',14:'re',15:'lw',16:'rw',23:'lh',24:'rh',25:'lk',26:'rk',
                    27:'la',28:'ra',29:'lhe',30:'rhe',31:'lt',32:'rt',0:'nose', 7:'le_ear', 8:'re_ear'}
            for i, n in imap.items():
                lm = res.pose_landmarks.landmark[i]
                if lm.visibility > 0.5:
                    pts[n] = (int(lm.x*cw), int(lm.y*AppConfig.H))
                else:
                    pts[n] = None
            world_pts = res.pose_world_landmarks.landmark
            try: h_val = float(user_height_str)
            except: h_val = 180.0
            hints, pts = engine.update(pts, world_pts, vis_scores, h_val)

        f_r = np.zeros((AppConfig.H, AppConfig.HALF_W, 3), dtype=np.uint8)
        f_r[:] = ColorConfig.BG
        cv2.line(f_r, (0,0), (0,AppConfig.H), ColorConfig.GRID, 1) 
        
        renderer.draw_skeleton(f_l, pts)
        renderer.draw_skeleton(f_r, pts, is_avatar=True)
        for t in [f_l, f_r]: renderer.draw_visuals(t, hints)

        final = np.hstack((f_l, f_r))
        
        msg, msg_col = engine.get_msg()
        renderer.draw_all_text_layers(final, engine.mode, engine.counter, fps, menu_open, user_height_str, is_typing, msg, msg_col, engine.error_counts, engine.bad_reps, cam_loader.is_video, cam_loader.paused)

        cv2.imshow(TextConfig.WINDOW_NAME, final)
        key = cv2.waitKey(1)
        if key & 0xFF == 27: break
        if is_typing:
            if 48 <= key <= 57:
                if len(user_height_str) < 3: user_height_str += chr(key)
            elif key == 8:
                user_height_str = user_height_str[:-1]
        
    cam_loader.release()
    cv2.destroyAllWindows()
    if HAS_AUDIO: pygame.quit()

if __name__ == "__main__":
    main()