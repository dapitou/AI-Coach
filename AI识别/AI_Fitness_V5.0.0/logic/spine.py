import numpy as np
import math
from core.config import AlgoConfig
from utils.geometry import GeomUtils

class SpineAnalyzer:
    def __init__(self):
        self.max_torso_len = 0.0
        
    def analyze(self, pts):
        # 基础点位检查
        if not (pts.get('ls') and pts.get('rs') and pts.get('lh') and pts.get('rh') and pts.get('neck') and pts.get('hip')): return

        # 坐标提取
        ls, rs = np.array(pts['ls']), np.array(pts['rs'])
        lh, rh = np.array(pts['lh']), np.array(pts['rh'])
        neck = (ls + rs) / 2
        hip = (lh + rh) / 2
        
        # 躯干向量
        vec_torso = hip - neck
        len_torso = np.linalg.norm(vec_torso)
        if len_torso < 10: return

        # 站立校准：动态获取最大躯干长度
        is_standing = GeomUtils.calc_inclination(pts['neck'], pts['hip']) < 20
        if is_standing:
            if len_torso > self.max_torso_len: 
                self.max_torso_len = len_torso
            elif self.max_torso_len > 0:
                self.max_torso_len = self.max_torso_len * (1-AlgoConfig.CALIBRATION_RATE) + len_torso * AlgoConfig.CALIBRATION_RATE
        
        # 压缩率计算
        compression_ratio = 0.0
        if self.max_torso_len > 0:
            compression_ratio = max(0.0, 1.0 - (len_torso / self.max_torso_len))
        
        # 几何补偿与弓背判定
        angle_rad = math.atan2(vec_torso[0], vec_torso[1]) 
        inclination = abs(math.degrees(angle_rad))
        
        pitch_allowance = AlgoConfig.CAMERA_PITCH_TOLERANCE if is_standing else 0.0
        effective_compression = max(0.0, compression_ratio - (0.5 * min(inclination/90, 1.0) + pitch_allowance))
        
        # 计算渲染用的偏移点
        lateral_vec = np.array([-vec_torso[1], vec_torso[0]]) / len_torso * (np.linalg.norm(rs-rh) - np.linalg.norm(ls-lh)) * 0.5
        
        t_base = neck + vec_torso * AlgoConfig.LOC_THORAX
        l_base = neck + vec_torso * AlgoConfig.LOC_LUMBAR
        
        pts['thorax'] = (int(t_base[0] + lateral_vec[0]), int(t_base[1] + lateral_vec[1]))
        pts['waist'] = (int(l_base[0] + lateral_vec[0]), int(l_base[1] + lateral_vec[1]))
        
        # 写入结果
        pts['rounding_bad'] = False
        if inclination > AlgoConfig.HINGE_ANGLE_MIN and effective_compression > AlgoConfig.ROUNDING_COMPRESS_TH:
            pts['rounding_bad'] = True
            
    def get_max_len(self):
        return self.max_torso_len if self.max_torso_len > 0 else 200