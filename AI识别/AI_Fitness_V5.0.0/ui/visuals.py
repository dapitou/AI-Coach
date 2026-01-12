"""
动作纠错特效渲染模块
负责绘制：动态箭头、虚线、对勾、圆圈等图元指令
"""
import cv2
import numpy as np
import math
import time
from core.config import ColorConfig
from utils.geometry import GeomUtils

class VisualFeedbackRenderer:
    
    def draw_commands(self, img, commands):
        """
        执行图元绘图指令列表
        :param commands: list of dict, e.g. [{'cmd': 'arrow', ...}, ...]
        """
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
                    cv2.line(img, c['start'], c['end'], color, thick)
            elif cmd == 'check':
                self._draw_check(img, c['center'], color, scale=c.get('scale', 1.0))
            elif cmd == 'circle':
                thick = c.get('thick', 2)
                cv2.circle(img, c['center'], c.get('radius', 10), color, thick)
            elif cmd == 'polyline':
                pts = np.array(c['pts'], np.int32)
                cv2.polylines(img, [pts], False, color, c.get('thick', 4), cv2.LINE_AA)

    def _draw_dynamic_arrow(self, img, start, target, color, gap, base_len, mode):
        """绘制带有呼吸动效的箭头"""
        dx, dy = 0, 0
        if mode == 'point':
            dx, dy = target[0] - start[0], target[1] - start[1]
        else:
            dx, dy = target[0], target[1]
            
        mag = math.hypot(dx, dy)
        if mag == 0: return
        ux, uy = dx / mag, dy / mag
        
        # 呼吸动效
        bounce = int(8 * math.sin(time.time() * 15))
        current_len = base_len + bounce
        
        s_x = int(start[0] + ux * gap)
        s_y = int(start[1] + uy * gap)
        
        if mode == 'point' and mag < current_len: 
            e_x, e_y = int(target[0]), int(target[1])
        else:
            e_x = int(s_x + ux * current_len)
            e_y = int(s_y + uy * current_len)
        
        cv2.arrowedLine(img, (s_x, s_y), (e_x, e_y), color, 4, cv2.LINE_AA, tipLength=0.3)

    def _draw_dash(self, img, p1, p2, color, thickness=2):
        """绘制虚线"""
        dist = GeomUtils.dist(p1, p2)
        if dist < 10: return
        pts = np.linspace(p1, p2, int(dist/15)).astype(int)
        for i in range(len(pts)-1):
            if i % 2 == 0: cv2.line(img, tuple(pts[i]), tuple(pts[i+1]), color, thickness)

    def _draw_check(self, img, center, color, scale=1.0):
        """绘制对勾"""
        x, y = center
        pts = np.array([
            [x - int(10*scale), y], 
            [x - int(3*scale), y + int(10*scale)], 
            [x + int(20*scale), y - int(15*scale)]
        ], np.int32)
        cv2.polylines(img, [pts], False, color, int(4*scale), cv2.LINE_AA)