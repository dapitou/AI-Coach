import cv2
import numpy as np
import math
import time
from PIL import Image, ImageDraw, ImageFont
from config import AppConfig, ColorConfig, TextConfig, ERR_NAMES_MAP
from utils import GeomUtils

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
        
        # [核心修复] 补全所有悬停状态键值，防止 KeyError
        self.hover = {
            "menu": False, 
            "height": False, 
            "seek_bar": False, 
            "btn_play": False,
            "btn_cam": False, 
            "btn_video": False,
            "i0": False, "i1": False, "i2": False, "i3": False
        }

    def update_hover(self, x, y, menu_open):
        self.hover["menu"] = (20 <= x <= 240 and 20 <= y <= 70)
        self.hover["height"] = (260 <= x <= 480 and 20 <= y <= 70)
        
        # 底部交互区
        self.hover["seek_bar"] = (60 <= x <= AppConfig.W - 20 and y >= AppConfig.H - 25)
        self.hover["btn_play"] = (10 <= x <= 50 and y >= AppConfig.H - 30)

        # 按钮区域 (左下角)
        btn_y_top = AppConfig.H - 85
        btn_y_bot = AppConfig.H - 50
        self.hover["btn_cam"] = (100 <= x <= 170 and btn_y_top <= y <= btn_y_bot)
        self.hover["btn_video"] = (190 <= x <= 280 and btn_y_top <= y <= btn_y_bot)

        if menu_open:
            for i in range(4):
                self.hover[f"i{i}"] = (20 <= x <= 240 and 75 + i*55 <= y <= 75 + i*55 + 50)
        else:
            for i in range(4): self.hover[f"i{i}"] = False

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

    def _draw_dynamic_arrow(self, img, start, direction_vec, color, gap=25, base_len=50, mode='point'):
        dx, dy = 0, 0
        if mode == 'point':
            dx = direction_vec[0] - start[0]
            dy = direction_vec[1] - start[1]
        else:
            dx, dy = direction_vec[0], direction_vec[1]
        mag = math.hypot(dx, dy)
        if mag == 0: return
        ux, uy = dx / mag, dy / mag
        bounce = int(10 * math.sin(time.time() * 15))
        current_len = base_len + bounce
        s_x = int(start[0] + ux * gap)
        s_y = int(start[1] + uy * gap)
        e_x = int(s_x + ux * current_len)
        e_y = int(s_y + uy * current_len)
        cv2.arrowedLine(img, (s_x, s_y), (e_x, e_y), color, 4, cv2.LINE_AA, tipLength=0.3)

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
                if not ok:
                    self._draw_dynamic_arrow(img, s, (target[0], s[1]), ColorConfig.NEON_RED, gap=20, mode='point')
                else:
                    self._draw_check(img, (s[0], s[1]-30), ColorConfig.NEON_GREEN, 1.2)

            elif h['type'] == 'depth': 
                self._draw_dash(img, h['p1'], h['p2'], color)
                cv2.circle(img, h['p1'], 8, color, -1)
                cv2.circle(img, h['p2'], 8, color, 2)
            
            elif h['type'] == 'bounce_arrow':
                pt, side = h['start'], h['side']
                if ok: 
                    self._draw_check(img, (pt[0], pt[1]-30), ColorConfig.NEON_GREEN)
                else:
                    vec = (1, 0) if side == 'left' else (-1, 0)
                    self._draw_dynamic_arrow(img, pt, vec, ColorConfig.NEON_RED, gap=20, base_len=60, mode='vector')
            
            elif h['type'] == 'rounding_guide':
                pts_curve = [h['neck'], h['thorax'], h['waist'], h['hip']]
                cv2.polylines(img, [np.array(pts_curve)], False, ColorConfig.NEON_RED, 4, cv2.LINE_AA)
                self._draw_dash(img, h['neck'], h['hip'], ColorConfig.NEON_GREEN, 1)
                target_pt = h['waist'] 
                push_dir = 1 if target_pt[0] < h['neck'][0] else -1
                start_arrow = (target_pt[0] - (push_dir * 80), target_pt[1])
                self._draw_dynamic_arrow(img, start_arrow, target_pt, ColorConfig.NEON_ORANGE, gap=0, base_len=60, mode='point')
                cv2.circle(img, target_pt, 8, ColorConfig.NEON_RED, -1)

            elif h['type'] == 'raise_guide':
                s, e = h['shoulder'], h['elbow']
                self._draw_dash(img, s, (s[0], s[1]-int(GeomUtils.dist(s,e))), color, 2)
                target_pt = (e[0], s[1])
                self._draw_dash(img, s, target_pt, color, 2)
                cv2.circle(img, target_pt, 10, color, 2)
                
                if not ok:
                    self._draw_dynamic_arrow(img, e, (0, -1), ColorConfig.NEON_RED, gap=20, mode='vector')
                    cv2.circle(img, e, 8, ColorConfig.NEON_RED, -1)
                else:
                    self._draw_check(img, (e[0], e[1]-40), ColorConfig.NEON_GREEN)
            
            # 弓步蹲 - 膝内扣
            elif h['type'] == 'lunge_knee_guide':
                k, a = h['knee'], h['ankle']
                direction = h['direction'] 
                
                # 目标线：脚踝垂直向上
                target_y = k[1] - 100
                self._draw_dash(img, a, (a[0], target_y), color)
                cv2.circle(img, k, 8, color, -1)
                
                if not ok:
                    vec = (-1, 0) if direction == 'left' else (1, 0)
                    self._draw_dynamic_arrow(img, k, vec, ColorConfig.NEON_RED, gap=25, base_len=70, mode='vector')
                else:
                    self._draw_check(img, (k[0], k[1]-40), ColorConfig.NEON_GREEN)

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

    def draw_text_shadow(self, draw, x, y, text, font, col):
        draw.text((x+2, y+2), text, font=font, fill=(0,0,0))
        draw.text((x, y), text, font=font, fill=(col[2], col[1], col[0]))

    def draw_video_bar(self, img, progress, is_paused):
        h, w = img.shape[:2]
        bar_y = h - 12
        bar_h = 8
        
        btn_x = 25
        btn_y = h - 15
        btn_col = ColorConfig.NEON_YELLOW if self.hover["btn_play"] else ColorConfig.TEXT_MAIN
        
        if is_paused: 
            pts = np.array([[btn_x-6, btn_y-8], [btn_x-6, btn_y+8], [btn_x+10, btn_y]], np.int32)
            cv2.fillPoly(img, [pts], btn_col)
        else: 
            cv2.rectangle(img, (btn_x-6, btn_y-8), (btn_x-2, btn_y+8), btn_col, -1)
            cv2.rectangle(img, (btn_x+2, btn_y-8), (btn_x+6, btn_y+8), btn_col, -1)
        
        bar_start = 60
        bar_end = w - 20
        bar_width = bar_end - bar_start
        cv2.rectangle(img, (bar_start, bar_y), (bar_end, bar_y + bar_h), (60, 60, 60), -1)
        
        fill_w = int(bar_width * progress)
        fill_col = ColorConfig.NEON_BLUE if not self.hover["seek_bar"] else ColorConfig.NEON_YELLOW
        cv2.rectangle(img, (bar_start, bar_y), (bar_start + fill_w, bar_y + bar_h), fill_col, -1)
        cv2.circle(img, (bar_start + fill_w, bar_y + 4), 7, (255, 255, 255), -1)

    def draw_all_text_layers(self, img, mode, count, fps, menu_open, height_str, is_typing, msg, msg_color, error_stats, bad_reps, is_video):
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil)

        # 菜单
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
            opts = [TextConfig.ACT_PRESS, TextConfig.ACT_SQUAT, TextConfig.ACT_RAISE, TextConfig.ACT_LUNGE]
            y = 75
            for i, m in enumerate(opts):
                ci = ColorConfig.UI_BORDER_ACTIVE if self.hover[f"i{i}"] else ColorConfig.UI_BORDER_NORMAL
                self._box(draw, img, (20, y, 220, y+50), ci)
                draw.text((40, y+12), m, font=self.font_md, fill=ColorConfig.TEXT_MAIN)
                y += 55

        # 底部按钮
        c_cam = ColorConfig.NEON_YELLOW if not is_video else ColorConfig.TEXT_DIM
        c_vid = ColorConfig.NEON_YELLOW if is_video else ColorConfig.TEXT_DIM
        if self.hover["btn_cam"]: c_cam = ColorConfig.NEON_ORANGE
        if self.hover["btn_video"]: c_vid = ColorConfig.NEON_ORANGE
        
        base_y = AppConfig.H - 65
        self.draw_text_shadow(draw, 100, base_y, TextConfig.BTN_CAM, self.font_sm, c_cam)
        self.draw_text_shadow(draw, 190, base_y, TextConfig.BTN_VIDEO, self.font_sm, c_vid)

        # 顶部数据
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
                rx_stat -= 180 

        self.draw_text_shadow(draw, 20, AppConfig.H - 80, f"{TextConfig.LABEL_FPS}: {fps}", self.font_xs, ColorConfig.FPS)

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