import cv2
import mediapipe as mp
import numpy as np
import math
import time
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass

# ==========================================
# 0. 驱动层初始化
# ==========================================
try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False
    print("Warning: Pygame not found. Audio disabled.")

# ==========================================
# 1. 全局配置中心
# ==========================================
@dataclass(frozen=True)
class TextConfig:
    WINDOW_NAME: str = "AEKE Fitness Mirror V48 (Final Fix)"
    
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
    TEXT_MAIN: tuple = (250, 250, 250)
    TEXT_DIM: tuple = (160, 160, 160)
    FPS: tuple = (0, 255, 128)
    INPUT_ACTIVE: tuple = (0, 255, 255)

@dataclass(frozen=True)
class AlgoConfig:
    # [修改] 基础标准 (基于180cm)
    STD_HEIGHT: float = 180.0
    
    # 推举
    PRESS_VERT_TOLERANCE: int = 25
    # 耸肩
    SHRUG_ABS_LIMIT: float = 0.35
    SHRUG_REL_LIMIT: float = 0.92
    SHRUG_ARM_COMP: float = 0.90
    SHRUG_SMOOTH_FACTOR: float = 0.5
    
    # 深蹲
    SQUAT_CHECK_START_BASE: int = 300
    VALGUS_RATIO: float = 1.0
    
    # 前平举
    RAISE_ANGLE_TH: int = 80

@dataclass
class AppConfig:
    W: int = 1280
    H: int = 720
    HALF_W: int = 640
    FONT: str = "msyh.ttc"
    VOL: float = 0.5
    ANIM_SPEED: float = 0.2

# ==========================================
# 2. 核心工具库
# ==========================================
class GeomUtils:
    @staticmethod
    def dist(p1, p2):
        return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

    @staticmethod
    def is_vertical(p1, p2, tolerance):
        dx = abs(p1[0] - p2[0])
        dy = abs(p1[1] - p2[1])
        if dy == 0: return False
        angle = math.degrees(math.atan(dx / dy))
        return angle < tolerance

    @staticmethod
    def calc_angle_3pt(a, b, c):
        v1 = np.array([a.x - b.x, a.y - b.y, a.z - b.z])
        v2 = np.array([c.x - b.x, c.y - b.y, c.z - b.z])
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 < 1e-6 or n2 < 1e-6: return 0.0
        cosine = np.dot(v1, v2) / (n1 * n2)
        return np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))

# ==========================================
# 3. 音效系统
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
# 4. 渲染引擎 (UI & FX)
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
        self.hover = {"menu": False, "height": False, "item_0": False, "item_1": False, "item_2": False}

    def update_hover(self, x, y, menu_open):
        self.hover["menu"] = (20 < x < 240 and 20 < y < 70)
        self.hover["height"] = (260 < x < 480 and 20 < y < 70)
        if menu_open:
            for i in range(3):
                self.hover[f"item_{i}"] = (20 < x < 240 and 75 + i*55 < y < 75 + i*55 + 50)
        else:
            for i in range(3): self.hover[f"item_{i}"] = False

    # [修复] 补全 is_avatar 参数，防止 TypeError
    def draw_skeleton(self, img, pts, is_avatar=False):
        if not pts: return
        limbs = [('ls','le'),('le','lw'),('rs','re'),('re','rw'),('ls','lh'),('rs','rh'),('lh','rh'),('ls','rs'),('lh','lk'),('lk','la'),('rh','rk'),('rk','ra')]
        for u, v in limbs:
            if pts.get(u) and pts.get(v):
                # Avatar 模式下线条稍微粗一点
                thickness = 4 if is_avatar else 2
                cv2.line(img, pts[u], pts[v], ColorConfig.NEON_BLUE, thickness)
        for k, p in pts.items():
            if p and k != 'nose':
                radius = 6 if is_avatar else 4
                cv2.circle(img, p, radius, ColorConfig.NEON_YELLOW, -1)

    def draw_hints(self, img, hints):
        for h in hints:
            ok = h.get('ok', False)
            color = ColorConfig.NEON_GREEN if ok else ColorConfig.NEON_RED
            
            # 推举
            if h['type'] == 'press_guide':
                elbow, wrist = h['elbow'], h['wrist']
                arm_len = GeomUtils.dist(elbow, wrist)
                target_top = (int(elbow[0]), int(elbow[1] - arm_len))
                self._draw_dash(img, elbow, target_top, color, 2)
                cv2.circle(img, target_top, 12, color, 2)
                cv2.circle(img, wrist, 8, color, -1)
                
                if ok:
                    self._draw_check(img, (wrist[0], wrist[1]-30), ColorConfig.NEON_GREEN, 1.2)
                else:
                    dx = elbow[0] - wrist[0]
                    if abs(dx) > 15:
                        gap, bounce = 30, int(8 * math.sin(time.time() * 15))
                        start_x = wrist[0] + (gap * np.sign(dx))
                        end_x = wrist[0] + dx - (gap * np.sign(dx)) + (bounce * np.sign(dx))
                        if abs(end_x - start_x) > 10:
                            cv2.arrowedLine(img, (int(start_x), wrist[1]), (int(end_x), wrist[1]), color, 4, 8, 0, 0.4)

            # 深度
            elif h['type'] == 'depth': 
                self._draw_dash(img, h['p1'], h['p2'], color)
                cv2.circle(img, h['p1'], 8, color, -1)
                cv2.circle(img, h['p2'], 8, color, 2)
            
            # 内扣
            elif h['type'] == 'bounce_arrow':
                pt, side = h['start'], h['side']
                gap = 35
                start_x = pt[0] - gap if side == 'left' else pt[0] + gap
                start_pt = (start_x, pt[1])
                if ok:
                    self._draw_check(img, start_pt, ColorConfig.NEON_GREEN)
                else:
                    bounce = int(12 * math.sin(time.time() * 15))
                    length = 60 + abs(bounce)
                    end_pt = (start_x + length, pt[1]) if side == 'left' else (start_x - length, pt[1])
                    cv2.arrowedLine(img, start_pt, end_pt, ColorConfig.NEON_RED, 4, 8, 0, 0.4)

            # 前平举
            elif h['type'] == 'raise_guide':
                shoulder, elbow = h['shoulder'], h['elbow']
                arm_est = 150 
                self._draw_dash(img, shoulder, (shoulder[0], int(shoulder[1] - arm_est)), color, 2)
                cv2.circle(img, (shoulder[0], int(shoulder[1] - arm_est)), 12, color, 2)
                cv2.circle(img, elbow, 8, color, -1)
                if ok:
                    self._draw_check(img, (elbow[0], elbow[1]-40), ColorConfig.NEON_GREEN)
                else:
                    bounce = int(8 * math.sin(time.time() * 12))
                    arr_start = (elbow[0], elbow[1] - 30)
                    arr_end = (elbow[0], elbow[1] - 80 - bounce)
                    cv2.arrowedLine(img, arr_start, arr_end, color, 4, 8, 0, 0.4)

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

    def draw_hud_msg(self, img, text, color):
        if not text: return
        H, W = img.shape[:2]
        dummy = ImageDraw.Draw(Image.new('RGB',(1,1)))
        bbox = dummy.textbbox((0,0), text, font=self.font_lg)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        font = self.font_lg
        if tw > W - 100: 
            font = self.font_md
            bbox = dummy.textbbox((0,0), text, font=font)
            tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        pad = 40
        cx, cy = W//2, H-100
        x1, y1, x2, y2 = cx - tw//2 - pad, cy - th//2 - pad, cx + tw//2 + pad, cy + th//2 + pad
        
        sub = img[y1:y2, x1:x2]
        if sub.size > 0:
            black = np.zeros_like(sub)
            img[y1:y2, x1:x2] = cv2.addWeighted(sub, 0.4, black, 0.6, 0)
        cv2.rectangle(img, (x1,y1), (x2,y2), color, 2)
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        ImageDraw.Draw(pil).text((x1+pad, y1+pad-5), text, font=font, fill=(color[2],color[1],color[0]))
        img[:] = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

    def draw_ui_overlay(self, img, mode, count, fps, menu_open, height_str, is_typing):
        # 1. 动作选择框
        col_menu = ColorConfig.NEON_YELLOW if self.hover["menu"] else ColorConfig.GRID
        self._box(draw=None, img=img, rect=(20,20,220,70), col=col_menu) # 混合绘制需特殊处理
        
        # 为了文字质量，统一用PIL绘制上层
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil)

        # 重绘框体线条(PIL)以获得更好效果
        draw.rectangle((20,20,220,70), outline=col_menu, width=2)
        draw.text((40, 25), mode, font=self.font_md, fill=ColorConfig.NEON_YELLOW)
        draw.text((190, 30), "▼", font=self.font_sm, fill=(200,200,200))

        # 2. 身高框
        h_box_x = 260
        h_rect = (h_box_x, 20, h_box_x+220, 70)
        col_h = ColorConfig.NEON_YELLOW if (is_typing or self.hover["height"]) else ColorConfig.GRID
        draw.rectangle(h_rect, outline=col_h, width=2)
        
        draw.text((h_box_x+10, 32), TextConfig.LABEL_HEIGHT, font=self.font_sm, fill=ColorConfig.TEXT_DIM)
        disp_h = height_str + ("|" if (is_typing and time.time()%1>0.5) else "")
        draw.text((h_box_x+70, 27), disp_h, font=self.font_md, fill=(255,255,255))
        draw.text((h_box_x+170, 32), TextConfig.UNIT_CM, font=self.font_sm, fill=ColorConfig.TEXT_DIM)

        # 3. 菜单
        if self.menu_height_ratio > 0.01:
            opts = [TextConfig.ACT_PRESS, TextConfig.ACT_SQUAT, TextConfig.ACT_RAISE]
            h = int(len(opts) * 55 * self.menu_height_ratio)
            y = 75
            for i, m in enumerate(opts):
                if y - 75 + 50 > h: break
                ci = ColorConfig.NEON_YELLOW if self.hover[f"item_{i}"] else ColorConfig.GRID
                # 背景
                draw.rectangle((20,y,220,y+50), fill=(20,20,25), outline=ci, width=2)
                draw.text((40, y+12), m, font=self.font_md, fill=(255,255,255))
                y += 55

        # 4. 计数 & FPS
        rx = AppConfig.W - 200
        draw.text((rx, 20), TextConfig.LABEL_COUNT, font=self.font_sm, fill=ColorConfig.TEXT_DIM)
        draw.text((rx+80, 10), str(count), font=self.font_lg, fill=ColorConfig.NEON_YELLOW)
        draw.text((20, AppConfig.H-30), f"{TextConfig.LABEL_FPS}: {fps}", font=self.font_xs, fill=ColorConfig.FPS)
        
        img[:] = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

    def _box(self, draw, img, rect, col):
        # CV2 画半透明底
        x1, y1, x2, y2 = rect
        sub = img[y1:y2, x1:x2]
        black = np.zeros_like(sub)
        img[y1:y2, x1:x2] = cv2.addWeighted(sub, 0.2, black, 0.8, 0)

# ==========================================
# 4. 逻辑核心 (Logic Engine)
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
        self.base_shrug_dist = 0
        self.neck_curr_smooth = 0.0
        self.prev_hip_y = 0
        self.landmarks_vis = []

    def set_mode(self, m):
        if self.mode == m: return
        self.mode = m
        self.counter = 0
        self.history = {}
        self.active_errs = set()
        self.msg = ""
        self.msg_color = ColorConfig.TEXT_DIM
        self.stage = "start"
        self.base_shrug_dist = 0
        self.neck_curr_smooth = 0.0
        self.prev_hip_y = 0
        self.last_act = time.time()

    def update(self, pts, world_pts, vis_scores, user_height_cm):
        if not pts: return []
        vis = []
        self.landmarks_vis = vis_scores
        scale = user_height_cm / AlgoConfig.STD_HEIGHT
        
        if not self._gatekeeper(pts): return vis
            
        if self.mode == TextConfig.ACT_PRESS: self._press(pts, vis, scale)
        elif self.mode == TextConfig.ACT_SQUAT: self._squat(pts, vis, scale)
        elif self.mode == TextConfig.ACT_RAISE: self._front_raise(pts, world_pts, vis, scale)
        return vis

    def _gatekeeper(self, pts):
        is_similar = False
        tip_text = ""
        
        if self.mode == TextConfig.ACT_PRESS:
            tip_text = TextConfig.TIP_PRESS_DO
            if pts.get('lw') and pts.get('rw') and pts.get('ls') and pts.get('rs'):
                wrist_y = (pts['lw'][1]+pts['rw'][1])/2
                shou_y = (pts['ls'][1]+pts['rs'][1])/2
                if wrist_y < shou_y + 200: is_similar = True
        elif self.mode == TextConfig.ACT_SQUAT:
            tip_text = TextConfig.TIP_SQUAT_DO
            if pts.get('lh') and pts.get('rh'):
                if abs(pts['lh'][0]-pts['rh'][0]) > 20: is_similar = True
        elif self.mode == TextConfig.ACT_RAISE:
            tip_text = TextConfig.TIP_RAISE_DO
            if pts.get('lw') and pts.get('rw') and pts.get('ls') and pts.get('rs'):
                sw = abs(pts['ls'][0]-pts['rs'][0])
                ww = abs(pts['lw'][0]-pts['rw'][0])
                if ww <= sw * 2.5: is_similar = True

        if is_similar:
            self.last_act = time.time()
            if self.msg == tip_text: self.msg = ""
            return True
        else:
            if time.time() - self.last_act > 3.0:
                if not self.active_errs:
                    self._set_msg(tip_text, ColorConfig.NEON_RED, perm=True)
            return False

    def _check_shrug_adaptive(self, p, scale, stage_check="up"):
        if not (p.get('ls') and p.get('rs') and p.get('le_ear') and p.get('re_ear')): return
        shou_y = (p['ls'][1] + p['rs'][1]) / 2
        ear_y = (p['le_ear'][1] + p['re_ear'][1]) / 2
        curr_dist = max(0, shou_y - ear_y)
        
        alpha = AlgoConfig.SHRUG_SMOOTH_FACTOR
        if self.neck_curr_smooth == 0: self.neck_curr_smooth = curr_dist
        else: self.neck_curr_smooth = alpha * curr_dist + (1-alpha) * self.neck_curr_smooth
        
        is_relax = (self.stage != stage_check)
        if is_relax:
            if curr_dist > 0:
                if self.base_shrug_dist == 0: self.base_shrug_dist = self.neck_curr_smooth
                else: self.base_shrug_dist = max(self.base_shrug_dist, self.neck_curr_smooth)
            if 'shrug' in self.active_errs:
                self.active_errs.remove('shrug')
                self.cycle_flags['shrug'] = True

        if self.stage == stage_check and self.base_shrug_dist > 0:
            delta = self.base_shrug_dist - self.neck_curr_smooth
            adaptive_th = AlgoConfig.SHRUG_DELTA_BASE * scale
            
            # [优化] 抬臂补偿
            if (p['lw'][1] < shou_y): adaptive_th *= AlgoConfig.SHRUG_ARM_COMP

            if delta > adaptive_th: self.cycle_flags['shrug'] = False

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
            l_drop = wp[13].y - wp[11].y
            r_drop = wp[14].y - wp[12].y
            th = AlgoConfig.RAISE_DIFF_BASE * scale
            if l_drop < th and r_drop < th:
                self.cycle_flags['range'] = True

        self._check_shrug_adaptive(p, scale, "up")
        
        show_shrug = "shrug" in self.active_errs and "range" not in self.active_errs
        if "range" in self.active_errs:
            self._set_msg(TextConfig.ERR_RAISE_RANGE, ColorConfig.NEON_RED, perm=True)
            is_ok = self.cycle_flags['range']
            if p['le']: vis.append({'type':'raise_guide', 'shoulder':p['ls'], 'elbow':p['le'], 'ok':is_ok})
            if p['re']: vis.append({'type':'raise_guide', 'shoulder':p['rs'], 'elbow':p['re'], 'ok':is_ok})
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
        is_descending = hy > (self.prev_hip_y + 2) 
        self.prev_hip_y = hy 
        vert_dist = ky - hy 
        check_th = AlgoConfig.SQUAT_CHECK_START_BASE * scale
        in_check_zone = vert_dist < check_th
        
        if self.stage != "down" and hy > ky - 80:
            self.stage = "down"
            self._reset_flags(["valgus", "depth"])
        elif self.stage == "down" and hy < ky - 120:
            self.stage = "up"
            self.counter += 1
            self._end_cycle(["valgus", "depth"])
            
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
        if self.stage == "down" and is_deep:
            self.cycle_flags['depth'] = True
            
        show_depth = "depth" in self.active_errs and "valgus" not in self.active_errs
        if "valgus" in self.active_errs:
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
        err_high, err_low = keys[0], keys[1]
        
        res_h = self.cycle_flags.get(err_high, True)
        state_h = self._update_hist(err_high, res_h)
        
        block_low = (state_h == 'TRIGGER') or (err_high in self.active_errs)
        if block_low and err_low in self.active_errs:
            self.active_errs.remove(err_low)
        res2 = self.cycle_flags.get(err_low, True)
        state2 = self._update_hist(err_low, res2, block_low)
        
        if state_h == 'FIXED' or state2 == 'FIXED': fixed = True
        if state_h == 'TRIGGER' or state2 == 'TRIGGER': triggered = True
        
        if fixed:
            self.sound.play('success')
            self._set_msg(TextConfig.MSG_GOOD, ColorConfig.NEON_GREEN, 3.0)
        elif triggered:
            self.sound.play('error')
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
# 5. 主程序
# ==========================================
def main():
    cap = cv2.VideoCapture(0)
    cap.set(3, AppConfig.W)
    cap.set(4, AppConfig.H)
    pose = mp.solutions.pose.Pose(min_detection_confidence=0.6, model_complexity=1)
    engine = LogicEngine(SoundManager())
    renderer = UIRenderer()
    
    cv2.namedWindow(TextConfig.WINDOW_NAME, cv2.WINDOW_NORMAL)
    menu_open = False
    prev_time = time.time()
    fps = 0
    user_height_str = "180" # 默认180cm
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
                    if 75 < y < 130: engine.set_mode(TextConfig.ACT_PRESS); menu_open = False
                    elif 130 < y < 185: engine.set_mode(TextConfig.ACT_SQUAT); menu_open = False
                    elif 185 < y < 240: engine.set_mode(TextConfig.ACT_RAISE); menu_open = False
    cv2.setMouseCallback(TextConfig.WINDOW_NAME, mouse_cb)

    while True:
        ret, frame = cap.read()
        if not ret: break
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
            hints = engine.update(pts, world_pts, vis_scores, h_val)

        f_r = np.zeros((AppConfig.H, AppConfig.HALF_W, 3), dtype=np.uint8)
        f_r[:] = ColorConfig.BG
        for x in range(0, cw, 100): cv2.line(f_r, (x,0), (x,AppConfig.H), ColorConfig.GRID, 1)
        for y in range(0, AppConfig.H, 100): cv2.line(f_r, (0,y), (cw,y), ColorConfig.GRID, 1)

        renderer.draw_skeleton(f_l, pts)
        renderer.draw_skeleton(f_r, pts, is_avatar=True)
        for t in [f_l, f_r]: renderer.draw_hints(t, hints)

        final = np.hstack((f_l, f_r))
        renderer.draw_ui_overlay(final, engine.mode, engine.counter, fps, menu_open, user_height_str, is_typing)
        msg, col = engine.get_msg()
        renderer.draw_hud_msg(final, msg, col)

        cv2.imshow(TextConfig.WINDOW_NAME, final)
        key = cv2.waitKey(1)
        if key & 0xFF == 27: break
        if is_typing:
            if 48 <= key <= 57:
                if len(user_height_str) < 3: user_height_str += chr(key)
            elif key == 8:
                user_height_str = user_height_str[:-1]
        
    cap.release()
    cv2.destroyAllWindows()
    if HAS_AUDIO: pygame.quit()

if __name__ == "__main__":
    main()