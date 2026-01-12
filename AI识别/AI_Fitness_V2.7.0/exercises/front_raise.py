from core.base import BaseExercise
from core.config import ColorConfig, TextConfig
from core.utils import GeomUtils
import time

class FrontRaiseExercise(BaseExercise):
    def __init__(self, s):
        super().__init__(s)
        self.name = TextConfig.ACT_RAISE
        self.last_t = 0
        
    def process(self, pts, shared):
        vis = []
        if not (pts.get('ls') and pts.get('lw') and pts.get('rw')):
             return vis, (TextConfig.TIP_RAISE_DO, ColorConfig.NEON_RED), False
             
        sw = GeomUtils.dist(pts['ls'], pts['rs'])
        ww = GeomUtils.dist(pts['lw'], pts['rw'])
        if ww > sw * 2.0: return vis, (TextConfig.TIP_RAISE_DO, ColorConfig.NEON_RED), False
        
        wy = (pts['lw'][1]+pts['rw'][1])/2
        hy = (pts['lh'][1]+pts['rh'][1])/2
        
        if self.stage != "up" and wy < hy - 100:
            self.stage = "up"; self.curr_rep_error = False; self.active_errs.clear()
        elif self.stage == "up" and wy > hy - 50:
            self.stage = "down"
            if time.time()-self.last_t > 0.2:
                self.counter += 1; self.sound.play('count'); self.last_t = time.time()
                if self.curr_rep_error: self.bad_reps += 1
                else: self.sound.play('success')
        
        if self.stage == "up":
            if pts['le'][1] > pts['ls'][1]: self._trigger_error('range')
            
        if 'range' in self.active_errs:
            vis.append({'type': 'raise_guide', 'shoulder': pts['ls'], 'elbow': pts['le'], 'ok': False})
            vis.append({'type': 'raise_guide', 'shoulder': pts['rs'], 'elbow': pts['re'], 'ok': False})
            return vis, (TextConfig.ERR_RAISE_RANGE, ColorConfig.NEON_RED), True
            
        return vis, ("", ColorConfig.TEXT_DIM), True