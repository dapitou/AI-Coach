from exercises.base import BaseExercise
from core.config import TextConfig, ColorConfig, AlgoConfig
from utils.geometry import GeomUtils

class PressExercise(BaseExercise):
    def process(self, pts, shared):
        vis = []
        if not (pts.get('lw') and pts.get('rw') and pts.get('le') and pts.get('re')): return vis
        
        wrist_y = (pts['lw'][1]+pts['rw'][1])/2
        nose_y = pts['nose'][1] if pts.get('nose') else 0
        
        if self.stage == "start" and wrist_y < nose_y - 50:
            self.stage = "down"
            self.cycle_flags['arm'] = True
        elif self.stage == "down" and wrist_y > nose_y:
            self.stage = "start"
            self.counter += 1
            self._end_cycle(['arm', 'shrug'])
            
        lok = GeomUtils.is_vertical(pts['lw'], pts['le'], AlgoConfig.PRESS_VERT_TOLERANCE)
        rok = GeomUtils.is_vertical(pts['rw'], pts['re'], AlgoConfig.PRESS_VERT_TOLERANCE)
        
        if self.stage == "down":
             if not (lok and rok): self.cycle_flags['arm'] = False
        
        if 'arm' in self.active_feedback:
             col_l = ColorConfig.NEON_GREEN if lok else ColorConfig.NEON_RED
             col_r = ColorConfig.NEON_GREEN if rok else ColorConfig.NEON_RED
             
             # 计算动态虚线目标点 (基于当前臂长)
             dist_l = int(GeomUtils.dist(pts['lw'], pts['le']))
             target_l = (pts['le'][0], pts['le'][1] - dist_l)
             dist_r = int(GeomUtils.dist(pts['rw'], pts['re']))
             target_r = (pts['re'][0], pts['re'][1] - dist_r)
             
             # 1. 垂直虚线
             vis.append({'cmd':'line', 'style':'dash', 'start':pts['le'], 'end':target_l, 'color':col_l})
             vis.append({'cmd':'line', 'style':'dash', 'start':pts['re'], 'end':target_r, 'color':col_r})
             
             # 2. 顶端空心圆
             vis.append({'cmd':'circle', 'center':target_l, 'radius':12, 'color':col_l, 'thick':2})
             vis.append({'cmd':'circle', 'center':target_r, 'radius':12, 'color':col_r, 'thick':2})
             
             # 3. 手腕实心圆
             vis.append({'cmd':'circle', 'center':pts['lw'], 'radius':8, 'color':col_l, 'thick':-1})
             vis.append({'cmd':'circle', 'center':pts['rw'], 'radius':8, 'color':col_r, 'thick':-1})
             
             # 4. 指示箭头或对勾
             if not lok:
                 # 箭头水平指向垂直线目标X
                 vis.append({'cmd':'arrow', 'start':pts['lw'], 'target':(target_l[0], pts['lw'][1]), 'color':ColorConfig.NEON_RED, 'mode':'point', 'gap':20})
             else:
                 vis.append({'cmd':'check', 'center':(pts['lw'][0], pts['lw'][1]-30), 'color':ColorConfig.NEON_GREEN, 'scale':1.2})
                 
             if not rok:
                 vis.append({'cmd':'arrow', 'start':pts['rw'], 'target':(target_r[0], pts['rw'][1]), 'color':ColorConfig.NEON_RED, 'mode':'point', 'gap':20})
             else:
                 vis.append({'cmd':'check', 'center':(pts['rw'][0], pts['rw'][1]-30), 'color':ColorConfig.NEON_GREEN, 'scale':1.2})
                 
             self._set_msg(TextConfig.ERR_PRESS_ARM, ColorConfig.NEON_RED, perm=True, priority=1)
             
        return vis