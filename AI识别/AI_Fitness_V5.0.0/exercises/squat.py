from exercises.base import BaseExercise
from core.config import TextConfig, ColorConfig, AlgoConfig

class SquatExercise(BaseExercise):
    def __init__(self, s):
        super().__init__(s)
        self.prev_hip_y = 0

    def process(self, pts, shared):
        vis = []
        if not (pts.get('lh') and pts.get('rh') and pts.get('lk') and pts.get('rk')): return vis
        
        hy = (pts['lh'][1]+pts['rh'][1])/2
        ky = (pts['lk'][1]+pts['rk'][1])/2
        
        if self.prev_hip_y == 0: self.prev_hip_y = hy
        desc = hy > self.prev_hip_y + 2
        self.prev_hip_y = hy
        
        if self.stage == "start" and hy > ky - AlgoConfig.SQUAT_DOWN_TH_PIXEL:
            self.stage = "down"
            self.cycle_flags = {'valgus':True, 'depth':False, 'rounding':True}
        elif self.stage == "down" and hy < ky - AlgoConfig.SQUAT_UP_TH_PIXEL:
            self.stage = "start"
            self.counter += 1
            self._end_cycle(['valgus', 'depth', 'rounding'])
            
        deep = hy >= ky - 30
        if self.stage == "down" and deep: self.cycle_flags['depth'] = True
        
        hip_w = abs(pts['lh'][0] - pts['rh'][0])
        knee_w = abs(pts['lk'][0] - pts['rk'][0])
        is_valgus_now = knee_w < (hip_w * AlgoConfig.VALGUS_RATIO)
        
        if self.stage == "down" and desc and hy > ky - 200:
            if is_valgus_now: self.cycle_flags['valgus'] = False
            if shared.get('rounding_bad'): self.cycle_flags['rounding'] = False
            
        if 'valgus' in self.active_feedback:
             col = ColorConfig.NEON_GREEN if not is_valgus_now else ColorConfig.NEON_RED
             
             # 箭头水平向外 (Hardcoded center 320 logic moved here)
             cx = 320 
             vl = (-1, 0) if pts['lk'][0] < cx else (1, 0)
             
             vis.append({'cmd':'arrow', 'start':pts['lk'], 'target':vl, 'color':col, 'gap':20, 'len':60, 'mode':'vec'})
             vis.append({'cmd':'arrow', 'start':pts['rk'], 'target':(1,0), 'color':col, 'gap':20, 'len':60, 'mode':'vec'})
             
             if not is_valgus_now:
                 vis.append({'cmd':'check', 'center':(pts['lk'][0], pts['lk'][1]-30), 'color':ColorConfig.NEON_GREEN})
                 
             if pts.get('lt') and pts.get('rt'):
                 # 虚线颜色跟随状态
                 l_col = ColorConfig.NEON_ORANGE if is_valgus_now else ColorConfig.NEON_GREEN
                 vis.append({'cmd':'line', 'style':'dash', 'start':pts['lt'], 'end':(pts['lt'][0], pts['lk'][1]), 'color':l_col})
                 vis.append({'cmd':'line', 'style':'dash', 'start':pts['rt'], 'end':(pts['rt'][0], pts['rk'][1]), 'color':l_col})
                 
             self._set_msg(TextConfig.ERR_SQUAT_VALGUS, ColorConfig.NEON_RED, perm=True, priority=1)
             
        elif 'depth' in self.active_feedback:
             col = ColorConfig.NEON_GREEN if deep else ColorConfig.NEON_RED
             p1 = ((pts['lh'][0]+pts['rh'][0])//2, int(hy))
             p2 = ((pts['lk'][0]+pts['rk'][0])//2, int(ky))
             
             vis.append({'cmd':'line', 'style':'dash', 'start':p1, 'end':p2, 'color':col})
             vis.append({'cmd':'circle', 'center':p1, 'radius':8, 'color':col, 'thick':-1})
             vis.append({'cmd':'circle', 'center':p2, 'radius':8, 'color':col, 'thick':2})
             
             self._set_msg(TextConfig.ERR_SQUAT_DEPTH, ColorConfig.NEON_RED, perm=True, priority=1)
             
        return vis