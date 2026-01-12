from core.config import AlgoConfig

class CommonChecks:
    def __init__(self):
        self.base_shrug_dist = 0
        
    def calibrate_shrug(self, pts, stage):
        if stage != "start": return
        if not (pts.get('ls') and pts.get('rs') and pts.get('le_ear') and pts.get('re_ear')): return
        shou_y = (pts['ls'][1] + pts['rs'][1]) / 2
        ear_y = (pts['le_ear'][1] + pts['re_ear'][1]) / 2
        curr_dist = max(0, shou_y - ear_y)
        if curr_dist > 0: 
            self.base_shrug_dist = max(self.base_shrug_dist, curr_dist)
            
    def check_shrug(self, pts):
        if self.base_shrug_dist <= 0: return True
        if not (pts.get('ls') and pts.get('rs') and pts.get('le_ear') and pts.get('re_ear')): return True
        shou_y = (pts['ls'][1] + pts['rs'][1]) / 2
        ear_y = (pts['le_ear'][1] + pts['re_ear'][1]) / 2
        curr_dist = max(0, shou_y - ear_y)
        if curr_dist / (self.base_shrug_dist + 1e-6) < AlgoConfig.SHRUG_RATIO_TH:
            return False
        return True