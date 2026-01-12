import cv2
import numpy as np
import math
import time
from PIL import Image, ImageDraw, ImageFont
from .config import AppConfig, ColorConfig, TextConfig, ERR_NAMES_MAP

class UIRenderer:
    def __init__(self):
        try:
            self.font_lg = ImageFont.truetype(AppConfig.FONT, 42)
            self.font_md = ImageFont.truetype(AppConfig.FONT, 26)
            self.font_sm = ImageFont.truetype(AppConfig.FONT, 18)
            self.font_xs = ImageFont.truetype(AppConfig.FONT, 14)
        except:
            self.font_lg = self.font_md = self.font_sm = self.font_xs = ImageFont.load_default()
        
        self.menu_ratio = 0.0
        self.hover = {k:False for k in ["menu","height","seek_bar","btn_play","btn_cam","btn_video","i0","i1","i2","i3"]}

    def update_hover(self, x, y, menu_open, num_actions=4):
        h = self.hover
        h["menu"] = (20<=x<=240 and 20<=y<=70)
        h["height"] = (260<=x<=480 and 20<=y<=70)
        h["seek_bar"] = (60<=x<=AppConfig.W-20 and y>=AppConfig.H-25)
        h["btn_play"] = (10<=x<=50 and y>=AppConfig.H-30)
        by = AppConfig.H-65
        h["btn_cam"] = (100<=x<=170 and by<=y<=by+30)
        h["btn_video"] = (190<=x<=280 and by<=y<=by+30)
        if menu_open:
            for i in range(num_actions): h[f"i{i}"] = (20<=x<=240 and 75+i*55<=y<=75+i*55+50)
        else:
            for i in range(num_actions): h[f"i{i}"] = False

    def draw_skeleton(self, img, pts, is_avatar=False):
        if not pts: return
        limbs = [('ls','le'),('le','lw'),('rs','re'),('re','rw'),('ls','lh'),('rs','rh'),('lh','rh'),('ls','rs'),('lh','lk'),('lk','la'),('rh','rk'),('rk','ra')]
        for u, v in limbs:
            if pts.get(u) and pts.get(v):
                cv2.line(img, pts[u], pts[v], ColorConfig.NEON_BLUE, 4 if is_avatar else 2)
        if not pts.get('rounding_bad', False) and pts.get('waist'):
             for u, v in [('neck','thorax'), ('thorax','waist'), ('waist','hip')]:
                 cv2.line(img, pts[u], pts[v], ColorConfig.NEON_PURPLE, 3 if is_avatar else 2)
             for k in ['thorax', 'waist']: cv2.circle(img, pts[k], 5, ColorConfig.NEON_PURPLE, -1)
        for k in pts:
            if k not in ['nose','neck','thorax','lumbar','waist','hip','spine_state','rounding_bad'] and pts[k]:
                cv2.circle(img, pts[k], 5, ColorConfig.NEON_YELLOW, -1)

    # [核心] 抽象化渲染接口：只接收图元数据
    # 动作逻辑负责计算坐标和颜色
    def draw_visuals(self, img, visuals):
        for v in visuals:
            v_type = v.get('type')
            color = v.get('color', ColorConfig.NEON_RED)
            
            if v_type == 'arrow':
                # start: (x,y), vec: (dx,dy) or (tx,ty), mode: 'vector'/'point'
                start, vec = v['start'], v['vec']
                mode = v.get('mode', 'vector')
                self._draw_arrow_primitive(img, start, vec, color, v.get('gap', 25), v.get('len', 50), mode)
                
            elif v_type == 'line':
                style = v.get('style', 'solid')
                if style == 'dash': self._draw_dash(img, v['p1'], v['p2'], color)
                else: cv2.line(img, v['p1'], v['p2'], color, v.get('width', 2))
                
            elif v_type == 'circle':
                style = v.get('style', 'fill')
                th = -1 if style == 'fill' else 2
                cv2.circle(img, v['center'], v.get('radius', 5), color, th)
            
            elif v_type == 'polyline':
                cv2.polylines(img, [np.array(v['pts'])], False, color, v.get('width', 2), cv2.LINE_AA)
            
            elif v_type == 'check':
                cx, cy = v['center']
                pts = np.array([[cx-10, cy], [cx-3, cy+10], [cx+20, cy-15]], np.int32)
                cv2.polylines(img, [pts], False, ColorConfig.NEON_GREEN, 4, cv2.LINE_AA)

    def _draw_arrow_primitive(self, img, start, vec, col, gap, base, mode):
        dx, dy = 0, 0
        if mode == 'point': dx, dy = vec[0] - start[0], vec[1] - start[1]
        else: dx, dy = vec[0], vec[1]
        mag = math.hypot(dx, dy)
        if mag == 0: return
        ux, uy = dx/mag, dy/mag
        l = base + int(8*math.sin(time.time()*12)) # 弹性
        s = (int(start[0]+ux*gap), int(start[1]+uy*gap))
        e = (int(s[0]+ux*l), int(s[1]+uy*l))
        cv2.arrowedLine(img, s, e, col, 4, cv2.LINE_AA, tipLength=0.2)

    def _draw_dash(self, img, p1, p2, col):
        dist = math.hypot(p1[0]-p2[0], p1[1]-p2[1])
        if dist < 10: return
        pts = np.linspace(p1, p2, int(dist/15)).astype(int)
        for i in range(len(pts)-1):
            if i%2==0: cv2.line(img, tuple(pts[i]), tuple(pts[i+1]), col, 2)

    def draw_ui_overlay(self, img, mode, action_list, count, fps, menu, h_str, typing, msg, m_col, errs, bad, vid, paused):
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil)
        
        # Menu
        tgt = 1.0 if menu else 0.0
        if self.menu_ratio < tgt: self.menu_ratio = min(self.menu_ratio+0.15, tgt)
        elif self.menu_ratio > tgt: self.menu_ratio = max(self.menu_ratio-0.15, tgt)
        
        self._box(draw, img, (20,20,220,70), ColorConfig.UI_BORDER_ACTIVE if self.hover['menu'] else ColorConfig.UI_BORDER_NORMAL)
        draw.text((40,25), mode, font=self.font_md, fill=ColorConfig.NEON_YELLOW)
        
        self._box(draw, img, (260,20,480,70), ColorConfig.UI_BORDER_ACTIVE if typing else ColorConfig.UI_BORDER_NORMAL)
        draw.text((270,32), "身高", font=self.font_sm, fill=ColorConfig.TEXT_DIM)
        draw.text((330,27), h_str+("|" if typing and time.time()%1>.5 else ""), font=self.font_md, fill=ColorConfig.TEXT_MAIN)
        draw.text((420,32), "cm", font=self.font_sm, fill=ColorConfig.TEXT_DIM)
        
        if self.menu_ratio > 0.01:
            for i, o in enumerate(action_list):
                y = 75 + i*55
                if y > 75 + len(action_list)*55 * self.menu_ratio: break
                self._box(draw, img, (20,y,220,y+50), ColorConfig.UI_BORDER_ACTIVE if self.hover[f"i{i}"] else ColorConfig.UI_BORDER_NORMAL)
                draw.text((40,y+12), o, font=self.font_md, fill=ColorConfig.TEXT_MAIN)
        
        # Stats
        rx = AppConfig.W - 200
        self._txt(draw, rx, 20, "COUNT", str(count))
        
        acc = "-"
        if count > 0:
            val = int(((count-bad)/count)*100)
            acc = f"{max(0, val)}%"
        self._txt(draw, rx-220, 20, "正确率", acc, is_acc=True)
        
        ex = rx - 400
        for k, v in errs.items():
            if v > 0:
                self._txt(draw, ex, 25, ERR_NAMES_MAP.get(k,k), str(v), small=True)
                ex -= 160
                
        # Bottom
        by = AppConfig.H - 80
        self._txt(draw, 20, by, "FPS", str(fps), small=True)
        c_cam = ColorConfig.NEON_ORANGE if self.hover['btn_cam'] else (ColorConfig.NEON_YELLOW if not vid else ColorConfig.TEXT_DIM)
        c_vid = ColorConfig.NEON_ORANGE if self.hover['btn_video'] else (ColorConfig.NEON_YELLOW if vid else ColorConfig.TEXT_DIM)
        
        self._txt(draw, 100, AppConfig.H-65, "摄像头", "", small=True, color_override=c_cam)
        self._txt(draw, 190, AppConfig.H-65, "导入视频", "", small=True, color_override=c_vid)

        if msg:
            w, h = draw.textbbox((0,0), msg, font=self.font_lg)[2:]
            cx = AppConfig.W//2
            self._box(draw, img, (cx-w//2-20, AppConfig.H-140, cx+w//2+20, AppConfig.H-60), m_col)
            draw.text((cx-w//2, AppConfig.H-115), msg, font=self.font_lg, fill=m_col)

        img[:] = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

    def draw_video_bar(self, img, prog, paused):
        h, w = img.shape[:2]
        by = h - 12
        btn_c = ColorConfig.NEON_YELLOW if self.hover['btn_play'] else ColorConfig.TEXT_MAIN
        if paused:
            pts = np.array([[20, by-4], [20, by+12], [36, by+4]], np.int32)
            cv2.fillPoly(img, [pts], btn_c)
        else:
            cv2.rectangle(img, (20, by-4), (24, by+12), btn_c, -1)
            cv2.rectangle(img, (28, by-4), (32, by+12), btn_c, -1)
        
        bar_start, bar_end = 60, w-20
        cv2.rectangle(img, (bar_start, by), (bar_end, by+8), (60,60,60), -1)
        fw = int((bar_end-bar_start)*prog)
        col = ColorConfig.NEON_BLUE if not self.hover['seek_bar'] else ColorConfig.NEON_YELLOW
        cv2.rectangle(img, (bar_start, by), (bar_start+fw, by+8), col, -1)
        cv2.circle(img, (bar_start+fw, by+4), 7, (255,255,255), -1)

    def _box(self, draw, img, rect, col):
        sub = img[rect[1]:rect[3], rect[0]:rect[2]]
        if sub.size>0: img[rect[1]:rect[3], rect[0]:rect[2]] = cv2.addWeighted(sub, 0.2, np.zeros_like(sub), 0.8, 0)
        draw.rectangle(rect, outline=col, width=2)
    
    def _txt(self, draw, x, y, label, val, small=False, active=False, is_acc=False, color_override=None):
        f = self.font_sm if small else self.font_sm
        vf = self.font_md if small else self.font_lg
        c = color_override if color_override else (ColorConfig.NEON_ORANGE if active else ColorConfig.TEXT_DIM)
        draw.text((x, y), label, font=f, fill=c)
        if val: 
            vc = ColorConfig.NEON_YELLOW
            if is_acc:
                if "100" in val or (len(val)==3 and val[0]>='8'): vc = ColorConfig.NEON_GREEN
            elif small and not active:
                vc = ColorConfig.NEON_RED
            draw.text((x+80, y-10), val, font=vf, fill=vc)