from .config import AlgoConfig
import numpy as np
import math

class SpineAlgo:
    def __init__(self):
        self.facing_smooth = 0.0
        
    def update(self, engine, pts):
        if not (pts.get('ls') and pts.get('rs') and pts.get('lh') and pts.get('rh')): return
        
        ls, rs = np.array(pts['ls']), np.array(pts['rs'])
        lh, rh = np.array(pts['lh']), np.array(pts['rh'])
        neck = (ls + rs) / 2
        hip = (lh + rh) / 2
        vec = hip - neck
        curr_len = np.linalg.norm(vec)
        
        if engine.stage in ["start", "up"]:
            if curr_len > engine.max_torso_len: engine.max_torso_len = curr_len
            elif engine.max_torso_len > 0: engine.max_torso_len = engine.max_torso_len * 0.95 + curr_len * 0.05
            
        comp = max(0, 1.0 - curr_len/engine.max_torso_len) if engine.max_torso_len > 0 else 0
        
        score = 0
        if pts.get('nose'): score += np.sign(pts['nose'][0]-neck[0]) * 2.5
        self.facing_smooth = self.facing_smooth * 0.95 + score * 0.05
        face_dir = 1.0 if self.facing_smooth > 0 else -1.0
        
        u = vec / curr_len
        n = np.array([-u[1], u[0]])
        back = n * face_dir * AlgoConfig.GLOBAL_DIR_FLIP
        
        inc = abs(math.degrees(math.atan2(vec[0], vec[1])))
        hinge_tol = min(inc/90.0, 1.0) * AlgoConfig.HINGE_TOLERANCE_GAIN
        real_comp = max(0, comp - hinge_tol)
        
        rounding = real_comp * AlgoConfig.ROUNDING_AMP if inc > 15 else -comp * 0.5
        lateral = (np.linalg.norm(rs-rh) - np.linalg.norm(ls-lh)) * AlgoConfig.LATERAL_GAIN
        
        sagittal = back * (rounding * curr_len)
        lat_vec = n * lateral
        
        pts['neck'], pts['hip'] = (int(neck[0]), int(neck[1])), (int(hip[0]), int(hip[1]))
        t_pt = neck + vec * AlgoConfig.LOC_THORAX + lat_vec + sagittal
        l_pt = neck + vec * AlgoConfig.LOC_LUMBAR + lat_vec + sagittal * 1.5
        pts['thorax'] = (int(t_pt[0]), int(t_pt[1]))
        pts['waist'] = (int(l_pt[0]), int(l_pt[1]))
        pts['rounding_bad'] = (inc > 15 and real_comp > AlgoConfig.ROUNDING_COMPRESS_TH)