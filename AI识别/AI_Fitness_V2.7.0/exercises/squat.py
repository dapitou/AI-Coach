from core.base import BaseExercise
from core.config import ColorConfig, AlgoConfig, TextConfig
from core.utils import GeomUtils
import time

class SquatExercise(BaseExercise):
    def __init__(self, s):
        super().__init__(s)
        self.name = TextConfig.ACT_SQUAT
        self.prev_hy = 0
        self.last_t = 0
        
    def process(self, pts, shared):
        vis = []
        if not (pts.get('ls') and pts.get('rs') and pts.get('la') and pts.get('ra')):
            return vis, (TextConfig.TIP_SQUAT_DO, ColorConfig.NEON_RED), False
        
        sw = GeomUtils.dist(pts['ls'], pts['rs'])
        aw = GeomUtils.dist(pts['la'], pts['ra'])
        if sw == 0 or aw < sw * 0.5:
             return vis, (TextConfig.TIP_SQUAT_DO, ColorConfig.NEON_RED), False

        hy = (pts['lh'][1]+pts['rh'][1])/2
        ky = (pts['lk'][1]+pts['rk'][1])/2
        
        if self.prev_hy == 0: self.prev_hy = hy
        desc = hy > self.prev_hy + 2
        self.prev_hy = hy
        
        if self.stage != "down" and hy > ky - AlgoConfig.SQUAT_DOWN_TH:
            self.stage = "down"; self.curr_rep_error = False; self.active_errs.clear()
        elif self.stage == "down" and hy < ky - AlgoConfig.SQUAT_UP_TH:
            self.stage = "up"
            if time.time()-self.last_t > 0.2:
                self.counter += 1; self.sound.play('count'); self.last_t = time.time()
                if self.curr_rep_error: self.bad_reps += 1
                else: self.sound.play('success')
                
        is_deep = hy >= ky - 30
        if self.stage == "down" and is_deep: self.active_errs.discard('depth')
        
        if self.stage == "down" and desc and hy > ky - 200:
            lx = (pts['lt'][0]+pts['la'][0])/2
            rx = (pts['rt'][0]+pts['ra'][0])/2
            if pts['lk'][0] > lx or pts['rk'][0] < rx: self._trigger_error('valgus')
            if not is_deep and hy > ky - 50: self._trigger_error('depth')
            if shared.get('rounding_bad'): self._trigger_error('rounding')
            
        if 'valgus' in self.active_errs:
            # 构造 bounce_arrow
            vis.append({'type': 'bounce_arrow', 'start': pts['lk'], 'side': 'left', 'ok': False})
            vis.append({'type': 'bounce_arrow', 'start': pts['rk'], 'side': 'right', 'ok': False})
            return vis, (TextConfig.ERR_SQUAT_VALGUS, ColorConfig.NEON_RED), True
            
        if 'depth' in self.active_errs:
            center_h = (int((pts['lh'][0]+pts['rh'][0])/2), int(hy))
            center_k = (int((pts['lk'][0]+pts['rk'][0])/2), int(ky))
            vis.append({'type': 'depth', 'p1': center_h, 'p2': center_k, 'ok': is_deep})
            return vis, (TextConfig.ERR_SQUAT_DEPTH, ColorConfig.NEON_RED), True
            
        if 'rounding' in self.active_errs:
            vis.append({'type': 'rounding_guide', 'neck': pts['neck'], 'thorax': pts['thorax'], 'waist': pts['waist'], 'hip': pts['hip']})
            return vis, (TextConfig.ERR_SQUAT_ROUNDING, ColorConfig.NEON_RED), True

        return vis, ("", ColorConfig.TEXT_DIM), True