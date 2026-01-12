from exercises.base import BaseExercise
from core.config import TextConfig, ColorConfig, AlgoConfig

class FrontRaiseExercise(BaseExercise):
    def process(self, pts, shared):
        vis = []
        # [Fix] Check ALL required points to prevent KeyError
        # Needed: lw, rw, ls, rs, le, re
        if not (pts.get('lw') and pts.get('rw') and 
                pts.get('ls') and pts.get('rs') and 
                pts.get('le') and pts.get('re')): 
            return vis
            
        wy = (pts['lw'][1]+pts['rw'][1])/2
        sy = (pts['ls'][1]+pts['rs'][1])/2
        ty = (pts['le'][1]+pts['re'][1])/2
        
        if self.stage == "start" and wy < ty:
            self.stage = "down"
            self.cycle_flags['range'] = False
        elif self.stage == "down" and wy > sy + 100:
            self.stage = "start"
            self.counter += 1
            self._end_cycle(['range', 'shrug'])

        if self.stage == "down":
            if pts['le'][1] <= pts['ls'][1] or pts['re'][1] <= pts['rs'][1]:
                self.cycle_flags['range'] = True
        
        if 'range' in self.active_feedback:
            ok = self.cycle_flags['range']
            col = ColorConfig.NEON_GREEN if ok else ColorConfig.NEON_RED
            
            # Draw shoulder level line
            vis.append({'cmd':'line', 'style':'dash', 'start':pts['ls'], 'end':(pts['ls'][0]+200, pts['ls'][1]), 'color':ColorConfig.NEON_BLUE})
            vis.append({'cmd':'circle', 'center':(pts['ls'][0]+200, pts['ls'][1]), 'radius':10, 'color':ColorConfig.NEON_BLUE, 'thick':2})
            
            if not ok:
                 # Up arrow
                 vis.append({'cmd':'arrow', 'start':pts['le'], 'target':(0, -1), 'color':col, 'gap':20, 'mode':'vec'})
                 vis.append({'cmd':'circle', 'center':pts['le'], 'radius':8, 'color':col, 'thick':-1})
                 
                 vis.append({'cmd':'arrow', 'start':pts['re'], 'target':(0, -1), 'color':col, 'gap':20, 'mode':'vec'})
            else:
                 vis.append({'cmd':'check', 'center':(pts['le'][0], pts['le'][1]-40), 'color':ColorConfig.NEON_GREEN})
            
            self._set_msg(TextConfig.ERR_RAISE_RANGE, ColorConfig.NEON_RED, perm=True, priority=1)

        return vis