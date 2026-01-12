from exercises.base import BaseExercise
from core.config import TextConfig, ColorConfig, AlgoConfig

class LungeExercise(BaseExercise):
    def __init__(self, s):
        super().__init__(s)
        self.prev_hip_y = 0
        self.stand_y = 0.0 
        self.prev_hy = 0
        self.front_idx = None
        
    def process(self, pts, shared):
        vis = []
        if not (pts.get('lh') and pts.get('rh')): return vis
        
        lk_y = pts['lk'][1] if pts.get('lk') else 0
        rk_y = pts['rk'][1] if pts.get('rk') else 0
        
        if pts.get('lk') and pts.get('rk'):
             curr_front = 25 if lk_y > rk_y else 26 
        elif pts.get('lk'): curr_front = 25
        else: curr_front = 26
        
        idx = self.front_idx if self.front_idx else curr_front
        
        if idx == 25:
             fk = pts.get('lk'); fa = pts.get('la'); ft = pts.get('lt'); fheel = pts.get('lhe')
        else:
             fk = pts.get('rk'); fa = pts.get('ra'); ft = pts.get('rt'); fheel = pts.get('rhe')
             
        if not fk: return vis
        
        hy = (pts['lh'][1]+pts['rh'][1])/2
        ky = fk[1]
        
        if self.stand_y == 0 or hy < self.stand_y: self.stand_y = hy
        drop = hy - self.stand_y
        max_drop = shared.get('max_torso_len', 200)
        
        if self.prev_hy == 0: self.prev_hy = hy
        desc = hy > self.prev_hy + 5 
        self.prev_hy = hy
        
        if self.stage == "start" and drop > max_drop * AlgoConfig.LUNGE_DROP_DOWN_RATIO:
            self.stage = "down"
            self.cycle_flags['lunge_valgus'] = True
            self.cycle_flags['lunge_depth'] = False
            self.front_idx = curr_front
            
        elif self.stage == "down" and drop < max_drop * AlgoConfig.LUNGE_DROP_UP_RATIO:
            self.stage = "start"
            self.counter += 1
            self._end_cycle(['lunge_valgus', 'lunge_depth'])
            self.front_idx = None
            self.stand_y = 0

        is_deep = hy >= ky - 100 
        if self.stage == "down" and is_deep: self.cycle_flags['lunge_depth'] = True
        
        valgus = False
        direction = 'left'
        foot_center = None
        
        if fa:
             if ft and fheel:
                foot_center = ((ft[0]+fheel[0])//2, (ft[1]+fheel[1])//2)
                mid_x = foot_center[0]
             else:
                foot_center = fa
                mid_x = fa[0]
                
             if idx == 25: 
                  if fk[0] < mid_x - 35: valgus = True; direction = 'right'
             else:
                  if fk[0] > mid_x + 35: valgus = True; direction = 'left'

        if self.stage == "down" and desc and drop > max_drop * 0.2 and valgus:
             if 'lunge_valgus' not in self.active_feedback:
                  self.feedback.process_error('lunge_valgus', False, set_msg_callback=self._set_msg)

        if self.stage == "down" and not valgus and 'lunge_valgus' in self.active_feedback:
             self.feedback.process_error('lunge_valgus', True, set_msg_callback=self._set_msg)

        if 'lunge_valgus' in self.active_feedback:
             col = ColorConfig.NEON_GREEN if not valgus else ColorConfig.NEON_RED
             vec = (1, 0) if direction == 'right' else (-1, 0)
             
             vis.append({'cmd':'arrow', 'start':fk, 'target':vec, 'color':col, 'gap':25, 'len':70, 'mode':'vec'})
             
             if foot_center:
                  l_col = ColorConfig.NEON_ORANGE if valgus else ColorConfig.NEON_GREEN
                  vis.append({'cmd':'line', 'style':'dash', 'start':foot_center, 'end':(foot_center[0], fk[1]), 'color':l_col})
             
             if not valgus:
                  vis.append({'cmd':'check', 'center':(fk[0], fk[1]-40), 'color':ColorConfig.NEON_GREEN})
                  
             self._set_msg(TextConfig.ERR_LUNGE_KNEE, ColorConfig.NEON_RED, perm=True, priority=1)
             
        elif 'lunge_depth' in self.active_feedback:
             col = ColorConfig.NEON_GREEN if is_deep else ColorConfig.NEON_RED
             m, t = ((pts['lh'][0]+pts['rh'][0])//2, int(hy)), (int((pts['lh'][0]+pts['rh'][0])//2), int(ky))
             
             vis.append({'cmd':'line', 'style':'dash', 'start':m, 'end':t, 'color':col})
             vis.append({'cmd':'circle', 'center':m, 'radius':8, 'color':col, 'thick':-1})
             vis.append({'cmd':'circle', 'center':t, 'radius':8, 'color':col, 'thick':2})
             
             self._set_msg(TextConfig.ERR_LUNGE_DEPTH, ColorConfig.NEON_RED, perm=True, priority=1)
             
        return vis