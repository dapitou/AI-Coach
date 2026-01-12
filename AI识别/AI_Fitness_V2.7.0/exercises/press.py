from core.base import BaseExercise
from core.config import ColorConfig, AlgoConfig, TextConfig
from core.utils import GeomUtils
import time

class PressExercise(BaseExercise):
    def __init__(self, s): 
        super().__init__(s)
        self.name = TextConfig.ACT_PRESS
        self.last_t = 0
        
    def process(self, pts, shared):
        vis = []
        if not (pts.get('lw') and pts.get('rw') and pts.get('ls')):
            return vis, (TextConfig.TIP_PRESS_DO, ColorConfig.NEON_RED), False
        
        wy = (pts['lw'][1]+pts['rw'][1])/2
        sy = (pts['ls'][1]+pts['rs'][1])/2
        if wy >= sy + 200: return vis, (TextConfig.TIP_PRESS_DO, ColorConfig.NEON_RED), False
        
        ny = pts['nose'][1] if pts.get('nose') else 0
        if self.stage != "up" and wy < ny-50:
            self.stage = "up"; self.curr_rep_error = False; self.active_errs.clear()
        elif self.stage == "up" and wy > ny:
            self.stage = "down"
            if time.time()-self.last_t > 0.2:
                self.counter += 1; self.sound.play('count'); self.last_t = time.time()
                if self.curr_rep_error: self.bad_reps += 1
                else: self.sound.play('success')

        if self.stage == "up":
            lok = GeomUtils.is_vertical(pts['lw'], pts['le'], 25)
            rok = GeomUtils.is_vertical(pts['rw'], pts['re'], 25)
            if not (lok and rok): self._trigger_error('arm')
                
        if 'arm' in self.active_errs:
            # 构造 press_guide
            vis.append({'type': 'press_guide', 'wrist': pts['lw'], 'elbow': pts['le'], 'ok': False})
            vis.append({'type': 'press_guide', 'wrist': pts['rw'], 'elbow': pts['re'], 'ok': False})
            return vis, (TextConfig.ERR_PRESS_ARM, ColorConfig.NEON_RED), True
            
        return vis, ("", ColorConfig.TEXT_DIM), True