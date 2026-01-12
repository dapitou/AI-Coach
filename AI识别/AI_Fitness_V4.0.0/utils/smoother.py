import math

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