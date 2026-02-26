import math
import numpy as np

class GeomUtils:
    @staticmethod
    def dist(p1, p2):
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    @staticmethod
    def angle(a, b, c):
        # Calculate angle <abc
        ba = (a[0]-b[0], a[1]-b[1])
        bc = (c[0]-b[0], c[1]-b[1])
        
        dot = ba[0]*bc[0] + ba[1]*bc[1]
        mag_a = math.hypot(ba[0], ba[1])
        mag_c = math.hypot(bc[0], bc[1])
        
        if mag_a * mag_c == 0: return 0.0
        
        cos_ang = dot / (mag_a * mag_c)
        cos_ang = max(-1.0, min(1.0, cos_ang))
        return math.degrees(math.acos(cos_ang))

    @staticmethod
    def angle_vertical(p1, p2):
        """
        计算线段 p1-p2 相对于垂直线(Y轴)的夹角(0-90度)
        """
        dx = abs(p1[0] - p2[0])
        dy = abs(p1[1] - p2[1])
        if dy == 0: return 90.0
        return math.degrees(math.atan(dx/dy))

    @staticmethod
    def is_vertical(p1, p2, tolerance):
        """
        [New] 判断线段是否垂直，返回布尔值
        :param p1, p2: 坐标点
        :param tolerance: 容忍角度
        """
        ang = GeomUtils.angle_vertical(p1, p2)
        return ang <= tolerance