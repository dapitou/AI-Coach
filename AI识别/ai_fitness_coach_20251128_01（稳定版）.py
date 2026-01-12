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
    print("Warning: Pygame not found. Audio disabled.")

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
        self.t = threading.Thread(target=self._update, daemon=True)
        self.t.start()
    
    def _update(self):
        while self.running:
            ret, frame = self.cap.read()
            with self.lock:
                self.ret, self.frame = ret, frame
            time.sleep(0.005)

    def read(self):
        with self.lock:
            return self.ret, self.frame.copy() if self.frame is not None else None

    def release(self):
        self.running = False
        self.cap.release()

# ==========================================
# 2. 全局配置 (已开放极高自由度参数)
# ==========================================
@dataclass(frozen=True)
class AlgoConfig:
    STD_HEIGHT: float = 180.0
    
    # --- [参数调优区：请在此调整] ---
    
    # 1. [全局方向修正]
    # 如果弓背方向反了（变成了挺胸），请将此值改为 -1.0 或 1.0 进行翻转
    GLOBAL_DIR_FLIP: float = -1.0 
    
    # 2. [胸椎灵敏度] (Thoracic)
    # 控制上半身弓背的幅度。值越大，一低头胸椎向后顶得越厉害
    THORACIC_SENSITIVITY: float = 1.5 
    
    # 3. [腰椎灵敏度] (Lumbar)
    # 控制下半身弓背的幅度。值越大，腰椎“反弓变圆背”的效果越明显
    LUMBAR_SENSITIVITY: float = 2.5 

    # 4. [侧屈灵敏度]
    # 控制左右弯曲幅度
    LATERAL_GAIN: float = 0.5

    # 5. [基础生理曲度] (中立位站姿)
    # 正值=向后凸(Kyphosis), 负值=向前凸(Lordosis)
    BASE_KYPHOSIS: float = 0.05   
    BASE_LORDOSIS: float = -0.07 

    # ------------------------------

    # 椎体位置
    LOC_THORAX: float = 0.35
    LOC_LUMBAR: float = 0.65
    
    # 视角判断
    VIEW_SIDE_RATIO: float = 0.28  
    VIEW_FRONT_RATIO: float = 0.45 
    
    # 躯干校准
    CALIBRATION_RATE: float = 0.05

    # 动作逻辑
    PRESS_VERT_TOLERANCE: int = 25
    SHRUG_RATIO_TH: float = 0.35
    SHRUG_SMOOTH_FACTOR: float = 0.6
    SQUAT_CHECK_START_BASE: int = 300
    VALGUS_RATIO: float = 1.0
    ROUNDING_COMPRESS_TH: float = 0.02
    HINGE_ANGLE_MIN: float = 10.0
    HINGE_ALIGN_TOLERANCE: float = 20.0
    RAISE_HEIGHT_RATIO: float = 0.5

@dataclass(frozen=True)
class TextConfig:
    WINDOW_NAME: str = "AEKE Fitness Mirror (Pro Tuning)"
    ACT_PRESS: str = "推举"
    ACT_SQUAT: str = "深蹲"
    ACT_RAISE: str = "前平举"
    LABEL_COUNT: str = "COUNT"
    LABEL_FPS: str = "FPS"
    LABEL_HEIGHT: str = "身高"
    UNIT_CM: str = "cm"
    MSG_GOOD: str = "真棒！动作正确了！"
    TIP_PRESS_DO: str = "请做“推举”动作"
    ERR_PRESS_ARM: str = "小臂全程垂直于地面效果更好！"
    ERR_PRESS_SHRUG: str = "动作中耸肩影响训练效果！"
    TIP_SQUAT_DO: str = "请做“深蹲”动作"
    ERR_SQUAT_DEPTH: str = "蹲至大腿平行地面地面效果更好！"
    ERR_SQUAT_VALGUS: str = "注意膝关节不要内扣！"
    ERR_SQUAT_ROUNDING: str = "背部挺直，不要弓腰！" 
    TIP_RAISE_DO: str = "请做“前平举”动作"
    ERR_RAISE_RANGE: str = "肘部抬至与肩等高效果更好"

@dataclass(frozen=True)
class ColorConfig:
    BG: tuple = (15, 15, 20)
    GRID: tuple = (40, 40, 50)
    NEON_BLUE: tuple = (255, 200, 0)
    NEON_GREEN: tuple = (50, 255, 50)
    NEON_RED: tuple = (50, 50, 255)
    NEON_YELLOW: tuple = (0, 215, 255)
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
# 3. 数学工具箱
# ==========================================
class GeomUtils:
    @staticmethod
    def dist(p1, p2):
        return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

    @staticmethod
    def dist_3d(p1, p2):
        return math.sqrt((p1.x-p2.x)**2 + (p1.y-p2.y)**2 + (p1.z-p2.z)**2)

    @staticmethod
    def is_vertical(p1, p2, tolerance):
        dx = abs(p1[0] - p2[0])
        dy = abs(p1[1] - p2[1])
        if dy == 0: return False
        angle = math.degrees(math.atan(dx / dy))
        return angle < tolerance

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

# ==========================================
# 4. 音效与渲染
# ==========================================
class SoundManager:
    def __init__(self):
        self.sounds = {}
        if HAS_AUDIO:
            try: self._gen_sounds()
            except: pass

    def _gen_wave(self, freq, dur, type='sine'):
        sr = 44100
        t = np.linspace(0, dur, int(sr*dur), False)
        w = np.sin(2*np.pi*freq*t) if type == 'sine' else np.sign(np.sin(2*np.pi*freq*t))
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
            try: self.sounds[name].play()
            except: pass

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
        self.hover = {"menu": False, "height": False, "i0": False, "i1": False, "i2": False}

    def update_hover(self, x, y, menu_open):
        self.hover["menu"] = (20 <= x <= 240 and 20 <= y <= 70)
        self.hover["height"] = (260 <= x <= 480 and 20 <= y <= 70)
        if menu_open:
            for i in range(3):
                self.hover[f"i{i}"] = (20 <= x <= 240 and 75 + i*55 <= y <= 75 + i*55 + 50)
        else:
            for i in range(3): self.hover[f"i{i}"] = False

    def draw_skeleton(self, img, pts, is_avatar=False):
        if not pts: return
        limbs = [('ls','le'),('le','lw'),('rs','re'),('re','rw'),('ls','lh'),('rs','rh'),('lh','rh'),('ls','rs'),('lh','lk'),('lk','la'),('rh','rk'),('rk','ra')]
        for u, v in limbs:
            if pts.get(u) and pts.get(v):
                cv2.line(img, pts[u], pts[v], ColorConfig.NEON_BLUE, 4 if is_avatar else 2)
        
        # 脊柱绘制
        if pts.get('waist') and pts.get('thorax') and pts.get('neck') and pts.get('hip'):
            is_bad = pts.get('rounding_bad', False)
            col = ColorConfig.NEON_RED if is_bad else ColorConfig.NEON_PURPLE
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

    def draw_hints(self, img, hints):
        for h in hints:
            ok = h.get('ok', False)
            color = ColorConfig.NEON_GREEN if ok else ColorConfig.NEON_RED
            
            if h['type'] == 'press_guide':
                s, e = h['wrist'], h['elbow']
                target = (e[0], e[1] - int(GeomUtils.dist(s, e)))
                self._draw_dash(img, e, target, color)
                cv2.circle(img, target, 12, color, 2)
                cv2.circle(img, s, 8, color, -1)
                if ok: self._draw_check(img, (s[0], s[1]-30), ColorConfig.NEON_GREEN, 1.2)

            elif h['type'] == 'depth': 
                self._draw_dash(img, h['p1'], h['p2'], color)
                cv2.circle(img, h['p1'], 8, color, -1)
                cv2.circle(img, h['p2'], 8, color, 2)
            
            elif h['type'] == 'bounce_arrow':
                pt, side = h['start'], h['side']
                gap = 35
                start_x = pt[0] - gap if side == 'left' else pt[0] + gap
                start_pt = (start_x, pt[1])
                if ok: self._draw_check(img, start_pt, ColorConfig.NEON_GREEN)
                else:
                    bounce = int(12 * math.sin(time.time() * 15))
                    length = 60 + abs(bounce)
                    end_pt = (start_x + length, pt[1]) if side == 'left' else (start_x - length, pt[1])
                    cv2.arrowedLine(img, start_pt, end_pt, ColorConfig.NEON_RED, 4, 8, 0, 0.4)
            
            elif h['type'] == 'spine_alert':
                w = h['waist']
                if not ok:
                    cv2.circle(img, w, 18, ColorConfig.NEON_RED, 2)
                    cv2.putText(img, "!", (w[0]-5, w[1]+10), cv2.FONT_HERSHEY_SIMPLEX, 1, ColorConfig.NEON_RED, 3)

            elif h['type'] == 'raise_guide':
                s, e = h['shoulder'], h['elbow']
                side = h['side'] 
                arm_len = GeomUtils.dist(s, e)
                angle_rad = math.radians(30)
                dx = int(arm_len * math.sin(angle_rad) * 1.2) 
                dy = int(arm_len * math.cos(angle_rad))
                if side == 'left': target_pt = (s[0] + dx, s[1] - dy) 
                else: target_pt = (s[0] - dx, s[1] - dy) 
                self._draw_dash(img, s, target_pt, color, 2)
                cv2.circle(img, target_pt, 12, color, 2)
                if ok: self._draw_check(img, (e[0], e[1]-40), ColorConfig.NEON_GREEN)

    def _draw_dash(self, img, p1, p2, color, thickness=2):
        dist = GeomUtils.dist(p1, p2)
        if dist < 10: return
        pts = np.linspace(p1, p2, int(dist/15)).astype(int)
        for i in range(len(pts)-1):
            if i % 2 == 0: cv2.line(img, tuple(pts[i]), tuple(pts[i+1]), color, thickness)

    def _draw_check(self, img, center, color, scale=1.0):
        x, y = center
        pts = np.array([[x - int(10*scale), y], [x - int(3*scale), y + int(10*scale)], [x + int(20*scale), y - int(15*scale)]], np.int32)
        cv2.polylines(img, [pts], False, color, int(4*scale), cv2.LINE_AA)

    def _box(self, draw, img, rect, col):
        x1, y1, x2, y2 = rect
        if x1 < 0: x1 = 0
        if y1 < 0: y1 = 0
        if x2 > img.shape[1]: x2 = img.shape[1]
        if y2 > img.shape[0]: y2 = img.shape[0]
        if x2 <= x1 or y2 <= y1: return
        sub = img[y1:y2, x1:x2]
        if sub.size > 0:
            black = np.zeros_like(sub)
            img[y1:y2, x1:x2] = cv2.addWeighted(sub, 0.2, black, 0.8, 0)
        if draw: draw.rectangle(rect, outline=(col[2],col[1],col[0]), width=2)

    def draw_all_text_layers(self, img, mode, count, fps, menu_open, height_str, is_typing, msg, msg_color):
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil)

        target = 1.0 if menu_open else 0.0
        step = AppConfig.MENU_ANIM_STEP
        if self.menu_height_ratio < target: self.menu_height_ratio = min(self.menu_height_ratio + step, target)
        elif self.menu_height_ratio > target: self.menu_height_ratio = max(self.menu_height_ratio - step, target)

        c_menu = ColorConfig.UI_BORDER_ACTIVE if self.hover["menu"] else ColorConfig.UI_BORDER_NORMAL
        self._box(draw, img, (20,20,220,70), c_menu)
        draw.text((40, 25), mode, font=self.font_md, fill=ColorConfig.NEON_YELLOW)
        draw.text((190, 30), "▼", font=self.font_sm, fill=ColorConfig.TEXT_DIM)

        h_box_x = 260
        h_rect = (h_box_x, 20, h_box_x+220, 70)
        c_h = ColorConfig.UI_BORDER_ACTIVE if (is_typing or self.hover["height"]) else ColorConfig.UI_BORDER_NORMAL
        self._box(draw, img, h_rect, c_h)
        draw.text((h_box_x+10, 32), TextConfig.LABEL_HEIGHT, font=self.font_sm, fill=ColorConfig.TEXT_DIM)
        disp_h = height_str + ("|" if (is_typing and time.time()%1>0.5) else "")
        draw.text((h_box_x+70, 27), disp_h, font=self.font_md, fill=ColorConfig.TEXT_MAIN)
        draw.text((h_box_x+170, 32), TextConfig.UNIT_CM, font=self.font_sm, fill=ColorConfig.TEXT_DIM)

        if self.menu_height_ratio > 0.01:
            opts = [TextConfig.ACT_PRESS, TextConfig.ACT_SQUAT, TextConfig.ACT_RAISE]
            h_total = len(opts) * 55
            curr_h = int(h_total * self.menu_height_ratio)
            y = 75
            for i, m in enumerate(opts):
                if y - 75 + 55 > curr_h: break
                ci = ColorConfig.UI_BORDER_ACTIVE if self.hover[f"i{i}"] else ColorConfig.UI_BORDER_NORMAL
                self._box(draw, img, (20, y, 220, y+50), ci)
                draw.text((40, y+12), m, font=self.font_md, fill=ColorConfig.TEXT_MAIN)
                y += 55

        rx = AppConfig.W - 200
        draw.text((rx, 20), TextConfig.LABEL_COUNT, font=self.font_sm, fill=ColorConfig.TEXT_DIM)
        draw.text((rx + 80, 10), str(count), font=self.font_lg, fill=ColorConfig.NEON_YELLOW)
        draw.text((20, AppConfig.H - 30), f"{TextConfig.LABEL_FPS}: {fps}", font=self.font_xs, fill=ColorConfig.FPS)

        if msg:
            H, W = img.shape[:2]
            bbox = draw.textbbox((0,0), msg, font=self.font_lg)
            tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
            font = self.font_lg
            if tw > W - 100: 
                font = self.font_md
                bbox = draw.textbbox((0,0), msg, font=font)
                tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
            pad = 40
            cx, cy = W//2, H-100
            x1, y1, x2, y2 = cx - tw//2 - pad, cy - th//2 - pad, cx + tw//2 + pad, cy + th//2 + pad
            self._box(draw, img, (x1, y1, x2, y2), msg_color)
            draw.text((x1+pad, y1+pad-5), msg, font=font, fill=(msg_color[2], msg_color[1], msg_color[0]))

        img[:] = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

# ==========================================
# 5. 逻辑核心 (生理学参数化脊柱模型)
# ==========================================
class LogicEngine:
    def __init__(self, sound_mgr):
        self.sound = sound_mgr
        self.mode = TextConfig.ACT_PRESS
        self.counter = 0
        self.stage = "start"
        self.history = {}
        self.active_errs = set()
        self.msg = ""
        self.msg_color = ColorConfig.TEXT_DIM
        self.msg_timer = 0
        self.last_act = time.time()
        self.cycle_flags = {}
        
        self.spine_alpha_smooth = 0.0 
        self.max_torso_len = 0.0
        self.base_shrug_dist = 0
        self.neck_curr_smooth = 0.0
        self.prev_hip_y = 0
        self.smoother = PointSmoother(alpha=AlgoConfig.SHRUG_SMOOTH_FACTOR)

    def set_mode(self, m):
        if self.mode == m: return
        self.mode = m
        self.counter = 0
        self.history = {}
        self.active_errs = set()
        self.msg = ""
        self.stage = "start"
        self.max_torso_len = 0.0
        self.spine_alpha_smooth = 0.0

    def update(self, pts, world_pts, vis_scores, user_height_cm):
        if not pts: return []
        vis = []
        pts = self.smoother.filter(pts)
        scale = user_height_cm / AlgoConfig.STD_HEIGHT
        
        self._update_elastic_spine(pts)
        
        if not self._gatekeeper(pts):
            return vis, pts
            
        if self.mode == TextConfig.ACT_PRESS: self._press(pts, vis, scale)
        elif self.mode == TextConfig.ACT_SQUAT: self._squat(pts, vis, scale)
        elif self.mode == TextConfig.ACT_RAISE: self._front_raise(pts, world_pts, vis, scale)
        return vis, pts

    # --- 核心算法：可调参生物力学模型 ---
    def _update_elastic_spine(self, pts):
        if not (pts.get('ls') and pts.get('rs') and pts.get('lh') and pts.get('rh')): return

        ls, rs = np.array(pts['ls']), np.array(pts['rs'])
        lh, rh = np.array(pts['lh']), np.array(pts['rh'])

        # 1. 基础解剖基点
        neck = (ls + rs) / 2
        hip = (lh + rh) / 2
        vec_torso = hip - neck
        len_torso = np.linalg.norm(vec_torso)
        if len_torso < 10: return

        # 2. 侧屈检测 (Lateral Flexion)
        len_left = np.linalg.norm(ls - lh)
        len_right = np.linalg.norm(rs - rh)
        lateral_diff = (len_right - len_left) * AlgoConfig.LATERAL_GAIN
        
        # 3. 躯干校准
        if self.stage in ["start", "up"]:
            if len_torso > self.max_torso_len: 
                self.max_torso_len = len_torso
            elif self.max_torso_len > 0:
                self.max_torso_len = self.max_torso_len * (1-AlgoConfig.CALIBRATION_RATE) + len_torso * AlgoConfig.CALIBRATION_RATE
        
        # 4. 视角与法向量
        w_shou = np.linalg.norm(ls - rs)
        w_hip = np.linalg.norm(lh - rh)
        ratio = ((w_shou + w_hip) / 2.0) / len_torso
        raw_alpha = 1.0 - (ratio - AlgoConfig.VIEW_SIDE_RATIO) / (AlgoConfig.VIEW_FRONT_RATIO - AlgoConfig.VIEW_SIDE_RATIO)
        raw_alpha = np.clip(raw_alpha, 0.0, 1.0)
        self.spine_alpha_smooth = 0.8 * self.spine_alpha_smooth + 0.2 * raw_alpha
        view_factor = self.spine_alpha_smooth

        u_torso = vec_torso / len_torso
        n_torso = np.array([-u_torso[1], u_torso[0]]) 
        
        # 5. [核心] 弓背与反弓的动态判定
        # 计算躯干倾角 (判断是俯身还是后仰)
        # 垂直=0, 俯身>0 (y轴向下，x轴向右)
        # 简单判定：如果 hip.y > neck.y，且 |dx| 较大
        # 使用 vec_torso 计算倾角
        angle_rad = math.atan2(vec_torso[0], vec_torso[1]) # x, y 
        inclination = math.degrees(angle_rad) # 0度表示垂直向下
        
        # 判定是否俯身 (Hinge)
        is_hinging = abs(inclination) > AlgoConfig.HINGE_ANGLE_MIN
        
        # 压缩率
        compression = 0.0
        if self.max_torso_len > 0:
            compression = max(0.0, 1.0 - (len_torso / self.max_torso_len))
        
        # [方向符号计算]
        # 1. 检测面部朝向 (左右)
        face_lr = 1.0 if ls[0] < rs[0] else -1.0
        
        # 2. 结合 n_torso 和 GLOBAL_DIR_FLIP
        # 此向量永远指向"背部"
        back_vec = n_torso * face_lr * AlgoConfig.GLOBAL_DIR_FLIP
        
        # [动态增益计算]
        # 逻辑：
        # 如果俯身 (Hinge) + 压缩 -> 弓背 (Rounding) -> 脊柱向背部顶出 (+BackVec)
        # 如果直立/后仰 + 压缩 -> 反弓 (Extension) -> 脊柱向胸部顶出 (-BackVec)
        # 但为了平滑，我们使用 inclination 的符号来辅助
        
        rounding_force = 0.0
        if is_hinging:
            # 俯身状态：压缩 = 弓背 (向后顶)
            rounding_force = compression
        else:
            # 直立/后仰状态：压缩 = 反弓/挺胸 (向前顶)
            # 我们给予一个反向的系数
            rounding_force = -compression * 0.8
            
        # 6. 计算最终偏移
        lateral_vec = n_torso * lateral_diff
        
        # 基础S曲线
        s_k = back_vec * (AlgoConfig.BASE_KYPHOSIS * len_torso * view_factor)
        s_l = back_vec * (AlgoConfig.BASE_LORDOSIS * len_torso * view_factor)
        
        # 动态变形 (Thoracic & Lumbar 分别计算)
        # 胸椎变形：基础后凸 + 动态力 * 灵敏度
        dyn_k = back_vec * (rounding_force * len_torso * AlgoConfig.THORACIC_SENSITIVITY)
        
        # 腰椎变形：基础前凸 + 动态力 * 灵敏度 (腰椎灵敏度通常更高，容易反转)
        dyn_l = back_vec * (rounding_force * len_torso * AlgoConfig.LUMBAR_SENSITIVITY)
        
        # 7. 坐标合成
        t_base = neck + vec_torso * AlgoConfig.LOC_THORAX
        pt_thorax = t_base + lateral_vec + s_k + dyn_k
        
        l_base = neck + vec_torso * AlgoConfig.LOC_LUMBAR
        pt_lumbar = l_base + lateral_vec + s_l + dyn_l

        # 8. 写入
        pts['neck'] = (int(neck[0]), int(neck[1]))
        pts['hip'] = (int(hip[0]), int(hip[1]))
        pts['thorax'] = (int(pt_thorax[0]), int(pt_thorax[1]))
        pts['waist'] = (int(pt_lumbar[0]), int(pt_lumbar[1]))
        pts['lumbar'] = pts['waist']
        
        # 9. 判定
        pts['spine_state'] = 'neutral'
        pts['rounding_bad'] = False
        if is_hinging and compression > AlgoConfig.ROUNDING_COMPRESS_TH:
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
            if pts.get('lw') and pts.get('rw') and pts.get('ls') and pts.get('rs'):
                sw = abs(pts['ls'][0]-pts['rs'][0])
                ww = abs(pts['lw'][0]-pts['rw'][0])
                if ww <= sw * 2.5: is_similar = True

        if is_similar:
            self.last_act = time.time()
            if self.msg == tip: self.msg = ""
            return True
        else:
            if time.time() - self.last_act > 3.0:
                if not self.active_errs: self._set_msg(tip, ColorConfig.NEON_RED, perm=True)
            return False

    def _check_shrug_adaptive(self, p, scale, stage_check="up"):
        if not (p.get('ls') and p.get('rs') and p.get('le_ear') and p.get('re_ear')): return
        shou_y = (p['ls'][1] + p['rs'][1]) / 2
        ear_y = (p['le_ear'][1] + p['re_ear'][1]) / 2
        curr_dist = max(0, shou_y - ear_y)
        self.neck_curr_smooth = curr_dist
        is_relax = (self.stage != stage_check)
        if is_relax:
            if curr_dist > 0:
                if self.base_shrug_dist == 0: self.base_shrug_dist = self.neck_curr_smooth
                else: self.base_shrug_dist = max(self.base_shrug_dist, self.neck_curr_smooth)
            if 'shrug' in self.active_errs:
                self.active_errs.remove('shrug')
                self.cycle_flags['shrug'] = True
        if self.stage == stage_check and self.base_shrug_dist > 0:
            ratio = self.neck_curr_smooth / (self.base_shrug_dist + 1e-6)
            if ratio < AlgoConfig.SHRUG_RATIO_TH: self.cycle_flags['shrug'] = False

    def _front_raise(self, p, wp, vis, scale):
        if not (p.get('lw') and p.get('rw') and p.get('le') and p.get('re') and p.get('ls') and p.get('rs')): return

        wrist_y = (p['lw'][1] + p['rw'][1]) / 2
        shou_y = (p['ls'][1] + p['rs'][1]) / 2
        trigger_y = (p['le'][1] + p['re'][1]) / 2
        
        if self.stage != "up" and wrist_y < trigger_y:
            self.stage = "up"
            self._reset_flags(["range", "shrug"])
        elif self.stage == "up" and wrist_y > shou_y + 100:
            self.stage = "down"
            self.counter += 1
            self._end_cycle(["range", "shrug"])

        if self.stage == "up":
            l_torso = GeomUtils.dist_3d(wp[23], wp[11])
            l_arm = GeomUtils.dist_3d(wp[11], wp[13])
            l_drop = wp[13].y - wp[11].y
            l_allow = l_arm - (l_torso * AlgoConfig.RAISE_HEIGHT_RATIO)
            r_torso = GeomUtils.dist_3d(wp[24], wp[12])
            r_arm = GeomUtils.dist_3d(wp[12], wp[14])
            r_drop = wp[14].y - wp[12].y
            r_allow = r_arm - (r_torso * AlgoConfig.RAISE_HEIGHT_RATIO)
            if l_drop < l_allow and r_drop < r_allow:
                self.cycle_flags['range'] = True

        self._check_shrug_adaptive(p, scale, "up")
        show_shrug = "shrug" in self.active_errs and "range" not in self.active_errs
        if "range" in self.active_errs:
            self._set_msg(TextConfig.ERR_RAISE_RANGE, ColorConfig.NEON_RED, perm=True)
            is_ok = self.cycle_flags['range']
            if p['le']: vis.append({'type':'raise_guide', 'shoulder':p['ls'], 'elbow':p['le'], 'side':'left', 'ok':is_ok})
            if p['re']: vis.append({'type':'raise_guide', 'shoulder':p['rs'], 'elbow':p['re'], 'side':'right', 'ok':is_ok})
        elif show_shrug:
            self._set_msg(TextConfig.ERR_PRESS_SHRUG, ColorConfig.NEON_RED, perm=True)

    def _press(self, p, vis, scale):
        if not (p.get('lw') and p.get('rw') and p.get('le') and p.get('re') and p.get('ls') and p.get('rs')): return
        wrist_y = (p['lw'][1]+p['rw'][1])/2
        shou_y = (p['ls'][1]+p['rs'][1])/2
        nose_y = p['nose'][1] if p.get('nose') else 0
        
        if self.stage != "up" and wrist_y < nose_y - 50:
            self.stage = "up"
            self._reset_flags(["arm", "shrug"])
        elif self.stage == "up" and wrist_y > nose_y:
            self.stage = "down"
            self.counter += 1
            self._end_cycle(["arm", "shrug"])
        
        lok = GeomUtils.is_vertical(p['lw'], p['le'], AlgoConfig.PRESS_VERT_TOLERANCE)
        rok = GeomUtils.is_vertical(p['rw'], p['re'], AlgoConfig.PRESS_VERT_TOLERANCE)
        if not (lok and rok): self.cycle_flags['arm'] = False
        
        self._check_shrug_adaptive(p, scale, "up")
        show_shrug = "shrug" in self.active_errs and "arm" not in self.active_errs
        if "arm" in self.active_errs:
            self._set_msg(TextConfig.ERR_PRESS_ARM, ColorConfig.NEON_RED, perm=True)
            if p['le']: vis.append({'type':'press_guide', 'elbow':p['le'], 'wrist':p['lw'], 'ok':lok})
            if p['re']: vis.append({'type':'press_guide', 'elbow':p['re'], 'wrist':p['rw'], 'ok':rok})
        elif show_shrug:
            self._set_msg(TextConfig.ERR_PRESS_SHRUG, ColorConfig.NEON_RED, perm=True)

    def _squat(self, p, vis, scale):
        if not (p.get('lh') and p.get('rh') and p.get('lk') and p.get('rk') and 
                p.get('lt') and p.get('rt') and p.get('la') and p.get('ra')): return
        hy, ky = (p['lh'][1]+p['rh'][1])/2, (p['lk'][1]+p['rk'][1])/2
        
        if self.prev_hip_y == 0: self.prev_hip_y = hy
        is_descending = hy > (self.prev_hip_y + 2) 
        self.prev_hip_y = hy 
        
        vert_dist = ky - hy 
        check_th = AlgoConfig.SQUAT_CHECK_START_BASE * scale
        in_check_zone = vert_dist < check_th
        
        if self.stage != "down" and hy > ky - 80:
            self.stage = "down"
            self._reset_flags(["rounding", "valgus", "depth"])
        elif self.stage == "down" and hy < ky - 120:
            self.stage = "up"
            self.counter += 1
            self._end_cycle(["rounding", "valgus", "depth"])
            
        is_deep = hy >= ky - 30
        
        l_foot_x = (p['lt'][0] + p['la'][0]) / 2
        r_foot_x = (p['rt'][0] + p['ra'][0]) / 2
        knee_dist = abs(p['lk'][0] - p['rk'][0])
        foot_dist = abs(l_foot_x - r_foot_x)
        is_valgus = knee_dist < (foot_dist * AlgoConfig.VALGUS_RATIO)
        l_in = p['lk'][0] > l_foot_x 
        r_in = p['rk'][0] < r_foot_x
        l_fail = is_valgus and l_in
        r_fail = is_valgus and r_in
        if is_valgus and not l_fail and not r_fail: l_fail = r_fail = True
        
        if is_descending and in_check_zone:
            if l_fail or r_fail: self.cycle_flags['valgus'] = False
            if p.get('rounding_bad'): self.cycle_flags['rounding'] = False
        
        if self.stage == "down" and is_deep: self.cycle_flags['depth'] = True
            
        show_rounding = "rounding" in self.active_errs
        show_valgus = "valgus" in self.active_errs and not show_rounding
        show_depth = "depth" in self.active_errs and not show_valgus and not show_rounding
        
        if show_rounding:
            self._set_msg(TextConfig.ERR_SQUAT_ROUNDING, ColorConfig.NEON_RED, perm=True)
            if p.get('waist'): vis.append({'type':'spine_alert', 'waist':p['waist'], 'ok':False})
        elif show_valgus:
            self._set_msg(TextConfig.ERR_SQUAT_VALGUS, ColorConfig.NEON_RED, perm=True)
            if p['lk']: vis.append({'type':'bounce_arrow', 'start':p['lk'], 'side':'left', 'ok':not l_fail})
            if p['rk']: vis.append({'type':'bounce_arrow', 'start':p['rk'], 'side':'right', 'ok':not r_fail})
        elif show_depth:
            self._set_msg(TextConfig.ERR_SQUAT_DEPTH, ColorConfig.NEON_RED, perm=True)
            p1 = ((p['lh'][0]+p['rh'][0])//2, int(hy))
            p2 = ((p['lk'][0]+p['rk'][0])//2, int(ky))
            vis.append({'type':'depth', 'p1':p1, 'p2':p2, 'ok':is_deep})

    def _reset_flags(self, keys):
        for k in keys:
            if k in ["depth", "range"]: self.cycle_flags[k] = False
            else: self.cycle_flags[k] = True

    def _end_cycle(self, keys):
        fixed, triggered = False, False
        for i, k in enumerate(keys):
            res = self.cycle_flags.get(k, True)
            st = self._update_hist(k, res)
            is_bad = (st == 'TRIGGER') or (k in self.active_errs)
            if is_bad:
                triggered = True
                for lower_k in keys[i+1:]:
                    if lower_k in self.active_errs: self.active_errs.remove(lower_k)
                break
            if st == 'FIXED': fixed = True
        
        if triggered: self.sound.play('error')
        elif fixed:
            self.sound.play('success')
            if not self.active_errs: self._set_msg(TextConfig.MSG_GOOD, ColorConfig.NEON_GREEN, 3.0)
        elif not any(k in self.active_errs for k in keys):
            self.sound.play('count')

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
# 6. 主程序
# ==========================================
def main():
    cam_loader = CameraLoader(0, AppConfig.W, AppConfig.H)
    time.sleep(1.0) # 等待摄像头预热
    
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
    cv2.setMouseCallback(TextConfig.WINDOW_NAME, mouse_cb)

    while cam_loader.running:
        ret, frame = cam_loader.read()
        if not ret: 
            time.sleep(0.01)
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
            imap = {11:'ls',12:'rs',13:'le',14:'re',15:'lw',16:'rw',23:'lh',24:'rh',25:'lk',26:'rk',27:'la',28:'ra',31:'lt',32:'rt',0:'nose', 7:'le_ear', 8:'re_ear'}
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
        cv2.line(f_r, (0,0), (0,AppConfig.H), ColorConfig.GRID, 1) # 边界
        
        renderer.draw_skeleton(f_l, pts)
        renderer.draw_skeleton(f_r, pts, is_avatar=True)
        for t in [f_l, f_r]: renderer.draw_hints(t, hints)

        final = np.hstack((f_l, f_r))
        
        msg, msg_col = engine.get_msg()
        renderer.draw_all_text_layers(final, engine.mode, engine.counter, fps, menu_open, user_height_str, is_typing, msg, msg_col)

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