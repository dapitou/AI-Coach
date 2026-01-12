import math

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