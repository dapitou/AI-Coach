from exercises.base import BaseExercise
from core.config import TextConfig, ColorConfig, AlgoConfig
from utils.geometry import GeomUtils
from logic.detectors.shrug import ShrugDetector
from logic.detectors.rounding import RoundingDetector

class PressExercise(BaseExercise):
    def __init__(self, sound_mgr):
        super().__init__(sound_mgr)
        
        self.shrug_detector = ShrugDetector(
            compression_threshold=AlgoConfig.SHRUG_COMPRESSION_TH,
            error_key='shrug',
            msg=TextConfig.ERR_PRESS_SHRUG
        )
        self.add_detector(self.shrug_detector)
        
        self.add_detector(RoundingDetector(
            error_key='rounding',
            msg=TextConfig.ERR_SQUAT_ROUNDING 
        ))

    def process(self, pts, shared):
        vis = []
        if not (pts.get('lw') and pts.get('rw') and pts.get('le') and pts.get('re') and pts.get('nose')): 
            return vis

        # --- 1. 状态机 & 耸肩基准 ---
        wrist_y = (pts['lw'][1] + pts['rw'][1]) / 2
        nose_y = pts['nose'][1] if pts.get('nose') else 0
        
        if self.stage == "start":
            self.shrug_detector.set_reference(pts)

        if self.stage == "start" and wrist_y < nose_y - 50:
            self.stage = "down"
            self.cycle_flags['arm'] = True 
            
        elif self.stage == "down" and wrist_y > nose_y:
            self.stage = "start"
            self.counter += 1
            
            check_keys = ['shrug', 'rounding']
            if AlgoConfig.ENABLE_PRESS_ARM: check_keys.append('arm')
            self._end_cycle(check_keys)

        # --- 2. 实时检测 ---
        wrists_high = (pts['lw'][1] < pts['le'][1]) and (pts['rw'][1] < pts['re'][1])
        if self.stage == "down" and wrists_high:
             vis.extend(self.run_detectors(pts, shared))

        # --- 3. 小臂判定 (仅在发力时判定) ---
        if AlgoConfig.ENABLE_PRESS_ARM and self.stage == "down":
            tol = AlgoConfig.PRESS_VERT_TOLERANCE
            lok = GeomUtils.is_vertical(pts['lw'], pts['le'], tol)
            rok = GeomUtils.is_vertical(pts['rw'], pts['re'], tol)
            
            if not (lok and rok): 
                 self.cycle_flags['arm'] = False
        
        # --- 4. 小臂视觉反馈 (持续化: 只要有错误状态就绘制) ---
        # [Fix] Visuals Block moved OUT of "stage == down"
        if 'arm' in self.active_feedback and AlgoConfig.ENABLE_PRESS_ARM:
             
             # Re-calculate checks for rendering colors
             tol = AlgoConfig.PRESS_VERT_TOLERANCE
             lok = GeomUtils.is_vertical(pts['lw'], pts['le'], tol)
             rok = GeomUtils.is_vertical(pts['rw'], pts['re'], tol)
             
             col_l = ColorConfig.NEON_GREEN if lok else ColorConfig.NEON_RED
             col_r = ColorConfig.NEON_GREEN if rok else ColorConfig.NEON_RED
             
             dist_l = int(GeomUtils.dist(pts['lw'], pts['le']))
             target_l = (pts['le'][0], pts['le'][1] - dist_l)
             dist_r = int(GeomUtils.dist(pts['rw'], pts['re']))
             target_r = (pts['re'][0], pts['re'][1] - dist_r)
             
             vis.append({'cmd':'line', 'style':'dash', 'start':pts['le'], 'end':target_l, 'color':col_l, 'thick':2})
             vis.append({'cmd':'line', 'style':'dash', 'start':pts['re'], 'end':target_r, 'color':col_r, 'thick':2})
             vis.append({'cmd':'circle', 'center':target_l, 'radius':12, 'color':col_l, 'thick':2})
             vis.append({'cmd':'circle', 'center':target_r, 'radius':12, 'color':col_r, 'thick':2})
             vis.append({'cmd':'circle', 'center':pts['lw'], 'radius':8, 'color':col_l, 'thick':-1})
             vis.append({'cmd':'circle', 'center':pts['rw'], 'radius':8, 'color':col_r, 'thick':-1})
             
             if not lok:
                 vis.append({'cmd':'arrow', 'start':pts['lw'], 'target':(target_l[0], pts['lw'][1]), 'color':ColorConfig.NEON_RED, 'mode':'point', 'gap':20})
             else:
                 vis.append({'cmd':'check', 'center':(pts['lw'][0], pts['lw'][1]-30), 'color':ColorConfig.NEON_GREEN, 'scale':1.2})
                 
             if not rok:
                 vis.append({'cmd':'arrow', 'start':pts['rw'], 'target':(target_r[0], pts['rw'][1]), 'color':ColorConfig.NEON_RED, 'mode':'point', 'gap':20})
             else:
                 vis.append({'cmd':'check', 'center':(pts['rw'][0], pts['rw'][1]-30), 'color':ColorConfig.NEON_GREEN, 'scale':1.2})
             
        return vis