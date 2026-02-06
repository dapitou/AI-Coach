"""
动作纠错特效渲染模块
V7.6.1: 增强文本与图形绘制的健壮性 (坐标取整)
"""
import cv2
import numpy as np
import math
import time
from core.config import ColorConfig
from utils.geometry import GeomUtils

class VisualFeedbackRenderer:
    def draw_commands(self, img, commands):
        for c in commands:
            cmd = c.get('cmd')
            color = c.get('color', ColorConfig.NEON_GREEN)
            
            if cmd == 'arrow':
                self._draw_dynamic_arrow(
                    img, c['start'], c['target'], color, 
                    gap=c.get('gap', 25), 
                    base_len=c.get('len', 50), 
                    mode=c.get('mode', 'vec')
                )
            elif cmd == 'line': 
                style = c.get('style', 'solid')
                thick = c.get('thick', 2)
                if style == 'dash':
                    self._draw_dash(img, c['start'], c['end'], color, thick)
                else:
                    self._draw_line_alpha(img, c['start'], c['end'], color, thick, c.get('alpha', 1.0))
            elif cmd == 'check':
                self._draw_check(img, c['center'], color, scale=c.get('scale', 1.0))
            elif cmd == 'circle':
                thick = c.get('thick', 2)
                cv2.circle(img, self._pt(c['center']), c.get('radius', 10), color, thick, cv2.LINE_AA)
            elif cmd == 'polyline':
                pts = np.array(c['pts'], np.int32)
                cv2.polylines(img, [pts], False, color, c.get('thick', 4), cv2.LINE_AA)
            elif cmd == 'text': 
                self._draw_text(img, c['pos'], c['text'], color, c.get('scale', 0.8))

    def _pt(self, p):
        """Helper to ensure integer coordinates"""
        return (int(p[0]), int(p[1]))

    def _draw_line_alpha(self, img, p1, p2, color, thick, alpha):
        """绘制带透明度的直线 (Alpha Blending)"""
        p1_int, p2_int = self._pt(p1), self._pt(p2)
        if alpha >= 0.99:
            cv2.line(img, p1_int, p2_int, color, thick, cv2.LINE_AA)
            return

        h, w = img.shape[:2]
        pad = thick + 2
        x1, y1 = p1_int
        x2, y2 = p2_int
        min_x, max_x = max(0, min(x1, x2) - pad), min(w, max(x1, x2) + pad)
        min_y, max_y = max(0, min(y1, y2) - pad), min(h, max(y1, y2) + pad)

        if max_x <= min_x or max_y <= min_y: return

        sub = img[min_y:max_y, min_x:max_x]
        overlay = sub.copy()
        cv2.line(overlay, (x1 - min_x, y1 - min_y), (x2 - min_x, y2 - min_y), color, thick, cv2.LINE_AA)
        cv2.addWeighted(overlay, alpha, sub, 1.0 - alpha, 0, sub)

    def _draw_text(self, img, pos, text, color, scale=0.8):
        font = cv2.FONT_HERSHEY_SIMPLEX
        ix, iy = int(pos[0]), int(pos[1])
        # Shadow
        cv2.putText(img, text, (ix+2, iy+2), font, scale, (0,0,0), 2, cv2.LINE_AA)
        # Main
        cv2.putText(img, text, (ix, iy), font, scale, color, 2, cv2.LINE_AA)

    def _draw_dynamic_arrow(self, img, start, target, color, gap, base_len, mode):
        dx, dy = 0, 0
        if mode == 'point':
            dx, dy = target[0] - start[0], target[1] - start[1]
        else:
            dx, dy = target[0], target[1]
            
        mag = math.hypot(dx, dy)
        if mag == 0: return
        ux, uy = dx / mag, dy / mag
        
        # 增强动态感：加大振幅 (8->12) 和 频率 (15->20)
        bounce = int(12 * math.sin(time.time() * 20))
        current_len = base_len + bounce
        
        s_x = int(start[0] + ux * gap)
        s_y = int(start[1] + uy * gap)
        
        if mode == 'point' and mag < current_len: 
            e_x, e_y = int(target[0]), int(target[1])
        else:
            e_x = int(s_x + ux * current_len)
            e_y = int(s_y + uy * current_len)
        
        # 增强视觉存在感：加大粗细 (4->6) 和 箭头三角比例 (0.3->0.4)
        cv2.arrowedLine(img, (s_x, s_y), (e_x, e_y), color, 6, cv2.LINE_AA, tipLength=0.4)

    def _draw_dash(self, img, p1, p2, color, thickness=2):
        dist = GeomUtils.dist(p1, p2)
        if dist < 10: return
        pts = np.linspace(p1, p2, int(dist/15)).astype(int)
        for i in range(len(pts)-1):
            if i % 2 == 0: cv2.line(img, tuple(pts[i]), tuple(pts[i+1]), color, thickness)

    def _draw_check(self, img, center, color, scale=1.0):
        x, y = center
        pts = np.array([
            [x - int(10*scale), y], 
            [x - int(3*scale), y + int(10*scale)], 
            [x + int(20*scale), y - int(15*scale)]
        ], np.int32)
        cv2.polylines(img, [pts], False, color, int(4*scale), cv2.LINE_AA)