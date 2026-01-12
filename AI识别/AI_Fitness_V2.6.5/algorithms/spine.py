import numpy as np
import math
from config import AlgoConfig

class SpineAlgo:
    def __init__(self):
        self.spine_alpha_smooth = 0.0
        self.facing_score_smooth = 0.0
        
    def determine_facing(self, pts):
        score = 0.0
        if pts.get('nose') and pts.get('neck'):
            diff = pts['nose'][0] - pts['neck'][0]
            if abs(diff) > 10: score += AlgoConfig.W_NOSE * np.sign(diff)
        if pts.get('lt') and pts.get('lhe'): 
            score += AlgoConfig.W_TOE * np.sign(pts['lt'][0] - pts['lhe'][0])
        if pts.get('rt') and pts.get('rhe'): 
            score += AlgoConfig.W_TOE * np.sign(pts['rt'][0] - pts['rhe'][0])
        
        alpha = AlgoConfig.FACING_SMOOTH_ALPHA
        self.facing_score_smooth = (1 - alpha) * self.facing_score_smooth + alpha * score
        if self.facing_score_smooth > 0.1: return 1.0
        if self.facing_score_smooth < -0.1: return -1.0
        return 1.0

    def update(self, engine, pts):
        if not (pts.get('ls') and pts.get('rs') and pts.get('lh') and pts.get('rh')): return
        ls, rs = np.array(pts['ls']), np.array(pts['rs'])
        lh, rh = np.array(pts['lh']), np.array(pts['rh'])
        neck = (ls + rs) / 2
        hip = (lh + rh) / 2
        vec_torso = hip - neck
        len_torso = np.linalg.norm(vec_torso)
        if len_torso < 10: return

        len_left = np.linalg.norm(ls - lh)
        len_right = np.linalg.norm(rs - rh)
        lateral_diff = (len_right - len_left) * AlgoConfig.LATERAL_GAIN
        
        if engine.stage in ["start", "up"]:
            if len_torso > engine.max_torso_len: 
                engine.max_torso_len = len_torso
            elif engine.max_torso_len > 0:
                engine.max_torso_len = engine.max_torso_len * (1-AlgoConfig.CALIBRATION_RATE) + len_torso * AlgoConfig.CALIBRATION_RATE
        
        compression_ratio = 0.0
        if engine.max_torso_len > 0:
            compression_ratio = max(0.0, 1.0 - (len_torso / engine.max_torso_len))

        u_torso = vec_torso / len_torso
        n_torso = np.array([-u_torso[1], u_torso[0]]) 
        
        face_sign = 1.0 if ls[0] < rs[0] else -1.0
        back_vec = n_torso * face_sign * AlgoConfig.GLOBAL_DIR_FLIP
        
        angle_rad = math.atan2(vec_torso[0], vec_torso[1]) 
        inclination = abs(math.degrees(angle_rad))
        
        inclination_factor = min(inclination / 90.0, 1.0)
        hinge_allowance = inclination_factor * AlgoConfig.HINGE_TOLERANCE_GAIN
        is_standing = inclination < 20
        pitch_allowance = AlgoConfig.CAMERA_PITCH_TOLERANCE if is_standing else 0.0
        total_tolerance = hinge_allowance + pitch_allowance
        effective_compression = max(0.0, compression_ratio - total_tolerance)
        
        rounding_force = effective_compression * AlgoConfig.ROUNDING_AMP
        if inclination < AlgoConfig.HINGE_ANGLE_MIN: 
             rounding_force = -compression_ratio * 0.5

        lateral_vec = n_torso * lateral_diff
        sagittal_offset = back_vec * (rounding_force * len_torso)
        t_offset = lateral_vec + sagittal_offset
        l_offset = lateral_vec + (sagittal_offset * 1.5)
        t_base = neck + vec_torso * AlgoConfig.LOC_THORAX
        pt_thorax = t_base + t_offset
        l_base = neck + vec_torso * AlgoConfig.LOC_LUMBAR
        pt_lumbar = l_base + l_offset

        pts['neck'] = (int(neck[0]), int(neck[1]))
        pts['hip'] = (int(hip[0]), int(hip[1]))
        pts['thorax'] = (int(pt_thorax[0]), int(pt_thorax[1]))
        pts['waist'] = (int(pt_lumbar[0]), int(pt_lumbar[1]))
        pts['lumbar'] = pts['waist']
        
        pts['spine_state'] = 'neutral'
        pts['rounding_bad'] = False
        if inclination > AlgoConfig.HINGE_ANGLE_MIN and effective_compression > AlgoConfig.ROUNDING_COMPRESS_TH:
            pts['spine_state'] = 'rounding'
            pts['rounding_bad'] = True